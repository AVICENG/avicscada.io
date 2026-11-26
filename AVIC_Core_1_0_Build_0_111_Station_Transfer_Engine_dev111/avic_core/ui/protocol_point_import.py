"""Protocol-neutral, transactional import of discovered field devices and points."""
from __future__ import annotations

from typing import Any
from datetime import datetime, timezone

from avic_core.domain.models import Device, Point, PointDirection, PointQuality
from avic_core.drivers.manager import DriverInstance


_PROTOCOL_DRIVERS = {
    "bacnet/ip": ("bacnet-ip", "BACnet/IP"),
    "modbus/tcp": ("modbus-tcp", "Modbus TCP"),
}
_DATA_TYPES = {
    "bool", "boolean", "binary", "digital", "digital input", "digital output", "binary-input", "binary-output",
    "float", "double", "real", "analog", "numeric", "number", "analog-input", "analog-output",
    "int", "integer", "uint", "counter", "long", "uint8", "uint16", "uint32", "uint64", "int8", "int16", "int32", "int64", "float32", "float64", "multi-state-input", "multi-state-output", "integer-value", "multi-state-value", "string", "text", "char",
}


class ProtocolDeviceImportService:
    """Imports normalized discovery results without protocol-specific repository logic.

    Expected input shape:
      protocol, network_id, device{native_identity,address,name,...},
      points[{native_identity,name,data_type,unit,direction,object_type,...}]
    Network discovery and field I/O are deliberately outside this service.
    """

    def __init__(self, core):
        self.core = core
        self.repository = core.repository

    def _validate(self, station_id: str, driver_instance_id: str,
                  inspection: dict[str, Any], selected_native_ids: list[str] | None,
                  import_all: bool) -> tuple[dict, dict, list[dict], set[str], dict]:
        station = self.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        if not isinstance(inspection, dict):
            raise ValueError("inspection должен быть объектом")
        protocol = str(inspection.get("protocol") or "").strip().casefold().replace(" ", "/")
        expected = _PROTOCOL_DRIVERS.get(protocol)
        if expected is None:
            raise ValueError(f"Протокол пока не поддерживает общий импорт: {protocol or 'не указан'}")
        driver = self.core.driver_manager.get_instance(driver_instance_id)
        if driver["station_id"] != station_id:
            raise ValueError("Экземпляр драйвера принадлежит другой станции")
        driver_protocol = str(driver["protocol"]).casefold().replace(" ", "/")
        if driver["driver_id"] != expected[0] or driver_protocol != protocol:
            raise ValueError("Протокол обнаружения не совпадает с выбранным экземпляром драйвера")

        device = inspection.get("device")
        if not isinstance(device, dict):
            raise ValueError("inspection.device должен быть объектом")
        native_device = str(device.get("native_identity") or "").strip()
        address = str(device.get("address") or "").strip()
        if not native_device or len(native_device) > 512 or not address or len(address) > 255:
            raise ValueError("Устройство должно иметь native_identity и address")
        device_name = str(device.get("name") or f"{expected[1]} {address}").strip()
        if not device_name or len(device_name) > 255:
            raise ValueError("Некорректное имя устройства")

        raw_points = inspection.get("points")
        if not isinstance(raw_points, list):
            raise ValueError("inspection.points должен быть списком")
        normalized: list[dict] = []
        seen: set[str] = set()
        for index, raw in enumerate(raw_points):
            if not isinstance(raw, dict):
                raise ValueError(f"Точка #{index + 1} должна быть объектом")
            native = str(raw.get("native_identity") or "").strip()
            name = str(raw.get("name") or "").strip()
            data_type = str(raw.get("data_type") or "").strip().casefold()
            direction_value = raw.get("direction")
            if direction_value is None:
                raise ValueError(f"Направление точки должно быть задано явно: {raw.get('native_identity', '')}")
            direction = str(direction_value).strip().casefold()
            unit = str(raw.get("unit") or "").strip()
            object_type = str(raw.get("object_type") or "").strip()
            if not native or len(native) > 512 or native in seen:
                raise ValueError(f"Отсутствует или повторяется native_identity точки: {native!r}")
            if not name or len(name) > 255:
                raise ValueError(f"Некорректное имя точки {native}")
            if data_type not in _DATA_TYPES:
                raise ValueError(f"Неподдерживаемый data_type точки {native}: {data_type}")
            if direction not in {"input", "output", "inout"}:
                raise ValueError(f"Некорректное направление точки {native}: {direction}")
            if len(unit) > 64 or len(object_type) > 128:
                raise ValueError(f"Слишком длинные метаданные точки {native}")
            seen.add(native)
            normalized.append({
                "native_identity": native, "name": name, "data_type": data_type,
                "direction": direction, "unit": unit, "object_type": object_type,
                "engineering_description": str(raw.get("engineering_description") or "")[:2000],
                "driver_binding": dict(raw.get("driver_binding") or {}),
            })

        available = {p["native_identity"] for p in normalized}
        if import_all:
            chosen = set(available)
        else:
            if selected_native_ids is None:
                chosen = set()
            elif not isinstance(selected_native_ids, list) or any(not isinstance(x, str) for x in selected_native_ids):
                raise ValueError("selected_native_ids должен быть списком строк")
            else:
                chosen = {x.strip() for x in selected_native_ids}
        unknown = sorted(chosen - available)
        if unknown:
            raise ValueError(f"Выбраны неизвестные точки: {unknown}")

        existing_device = next((r for r in self.repository.list_records(entity_type="Device", station_id=station_id)
                                if r["payload"].get("protocol", "").casefold() == protocol
                                and r["payload"].get("native_identity") == native_device), None)
        if existing_device and existing_device["payload"].get("driver_instance_id") != driver_instance_id:
            raise ValueError("Устройство уже связано с другим экземпляром драйвера")
        device_id = existing_device["entity_id"] if existing_device else None
        existing_points = set()
        if device_id:
            existing_points = {r["payload"].get("native_identity")
                for r in self.repository.list_records(entity_type="Point")
                if r["payload"].get("device_id") == device_id}
        duplicates = sorted(chosen & existing_points)
        new_points = sorted(chosen - existing_points)
        return station, driver, normalized, chosen, {
            "protocol": protocol, "device": device, "device_native_identity": native_device,
            "address": address, "device_name": device_name, "existing_device": existing_device,
            "new_points": new_points, "duplicate_points": duplicates,
            "unknown_selection": [], "selected_count": len(chosen),
        }

    @staticmethod
    def _bacnet_object_type(value: Any) -> int:
        names = {
            "analog-input": 0, "analog-output": 1, "analog-value": 2,
            "binary-input": 3, "binary-output": 4, "binary-value": 5,
            "multi-state-input": 13, "multi-state-output": 14, "multi-state-value": 19,
        }
        text = str(value or "").strip().casefold().replace("_", "-").replace(" ", "-")
        if text.isdigit():
            result = int(text)
        elif text in names:
            result = names[text]
        else:
            raise ValueError(f"BACnet object_type не распознан: {value!r}")
        if not 0 <= result <= 1023:
            raise ValueError("BACnet object_type вне допустимого диапазона")
        return result

    def _binding_template(self, protocol: str, device: dict, item: dict) -> dict:
        """Build a strict read-only driver binding; never guess Modbus addressing."""
        if protocol == "bacnet/ip":
            import ipaddress
            address_text = str(device.get("address") or "")
            host, sep, port_text = address_text.rpartition(":")
            if not sep:
                host, port_text = address_text, "47808"
            try:
                ipaddress.IPv4Address(host)
                port = int(port_text)
                device_instance = int(device.get("device_instance"))
                object_instance = int(str(item["native_identity"]).rsplit(":", 1)[1])
                object_type = self._bacnet_object_type(item.get("object_type"))
            except (ValueError, TypeError, KeyError) as exc:
                raise ValueError(
                    f"Недостаточно подтверждённых BACnet реквизитов для binding точки {item['native_identity']}: {exc}"
                ) from exc
            if not 1 <= port <= 65535 or not 0 <= device_instance <= 4_194_303 or not 0 <= object_instance <= 4_194_303:
                raise ValueError("BACnet address/device/object instance вне допустимого диапазона")
            return {"address": [host, port], "device_instance": device_instance,
                    "object_type": object_type, "object_instance": object_instance,
                    "property_id": 85}
        if protocol == "modbus/tcp":
            raw = item.get("driver_binding") or {}
            required = {"function", "address"}
            if not required.issubset(raw):
                raise ValueError(
                    f"Для Modbus точки {item['native_identity']} нужна явная карта регистра: function и address"
                )
            allowed = {"function", "address", "count", "data_type", "byte_order", "word_order", "scale", "offset"}
            if set(raw) - allowed:
                raise ValueError(f"Неизвестные параметры Modbus binding: {sorted(set(raw) - allowed)}")
            # Validate now, before creating any repository records.
            from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointBinding
            probe = ModbusTcpPointBinding(point_id="00000000-0000-0000-0000-000000000001",
                function=int(raw["function"]), address=int(raw["address"]),
                count=int(raw.get("count", 1)), data_type=str(raw.get("data_type", "uint16")),
                byte_order=str(raw.get("byte_order", "big")), word_order=str(raw.get("word_order", "big")),
                scale=float(raw.get("scale", 1.0)), offset=float(raw.get("offset", 0.0)))
            return {"function": probe.function, "address": probe.address, "count": probe.count,
                    "data_type": probe.data_type, "byte_order": probe.byte_order,
                    "word_order": probe.word_order, "scale": probe.scale, "offset": probe.offset}
        raise ValueError(f"Нет read-only binding builder для протокола {protocol}")

    def preview(self, station_id: str, driver_instance_id: str, inspection: dict[str, Any],
                selected_native_ids: list[str] | None = None, import_all: bool = False) -> dict:
        _, driver, points, chosen, info = self._validate(
            station_id, driver_instance_id, inspection, selected_native_ids, import_all)
        selected_items = [item for item in points if item["native_identity"] in chosen]
        binding_preview = {item["native_identity"]: self._binding_template(info["protocol"], info["device"], item)
                           for item in selected_items}
        return {
            "station_id": station_id, "driver_instance_id": driver_instance_id,
            "driver_id": driver["driver_id"], "protocol": info["protocol"],
            "device_native_identity": info["device_native_identity"],
            "device_exists": bool(info["existing_device"]),
            "device_id": info["existing_device"]["entity_id"] if info["existing_device"] else None,
            "discovered_points": len(points), "selected_points": len(chosen),
            "new_points": info["new_points"], "duplicate_points": info["duplicate_points"],
            "binding_count": len(binding_preview), "bindings_validated": True,
            "binding_preview": binding_preview, "device_only": not bool(chosen),
            "can_import": bool(chosen), "write_enabled": False, "field_device_writes": False,
        }

    def import_points(self, station_id: str, driver_instance_id: str, inspection: dict[str, Any],
                      selected_native_ids: list[str] | None = None, import_all: bool = False) -> dict:
        station, driver, points, chosen, info = self._validate(
            station_id, driver_instance_id, inspection, selected_native_ids, import_all)
        if not chosen:
            raise ValueError("Не выбраны точки для импорта")

        device_meta = info["device"]
        # Validate every selected native point before opening the write transaction.
        selected_items = [item for item in points if item["native_identity"] in chosen]
        templates = {item["native_identity"]: self._binding_template(info["protocol"], device_meta, item)
                     for item in selected_items}
        # Serialize import against driver start/stop/config changes.
        with self.core.driver_manager._lock:
            driver_item, driver_version = self.repository.get(driver_instance_id, DriverInstance)
            if driver_item.state != "STOPPED" or driver_item.enabled:
                raise RuntimeError("Импорт точек и изменение bindings разрешены только при остановленном драйвере")
            created_device = False
            added: list[str] = []
            skipped: list[str] = []
            with self.repository.transaction() as connection:
                existing_device = next((r for r in self.repository.list_records(
                    entity_type="Device", station_id=station_id, connection=connection)
                    if r["payload"].get("protocol", "").casefold() == info["protocol"]
                    and r["payload"].get("native_identity") == info["device_native_identity"]), None)
                if existing_device:
                    if existing_device["payload"].get("driver_instance_id") != driver_instance_id:
                        raise ValueError("Устройство уже связано с другим экземпляром драйвера")
                    device, version = self.repository.get(existing_device["entity_id"], Device)
                    if device.address != info["address"]:
                        raise ValueError("Адрес устройства изменился; требуется отдельная процедура переноса")
                else:
                    device = Device(
                        name=info["device_name"], station_id=station_id,
                        driver_instance_id=driver_instance_id, address=info["address"],
                        protocol=info["protocol"], network_id=str(inspection.get("network_id") or ""),
                        native_identity=info["device_native_identity"],
                        manufacturer=str(device_meta.get("manufacturer") or ""),
                        model=str(device_meta.get("model") or ""),
                        firmware_revision=str(device_meta.get("firmware_revision") or ""),
                        vendor_id=device_meta.get("vendor_id"),
                        identity_sources=dict(device_meta.get("identity_sources") or {}),
                        engineering_description=str(device_meta.get("engineering_description") or ""),
                    )
                    self.repository.save(device, connection=connection)
                    created_device = True
    
                existing_rows = self.repository.list_records(entity_type="Point", connection=connection)
                existing_native = {r["payload"].get("native_identity") for r in existing_rows
                                   if r["payload"].get("device_id") == device.id}
                pending_points = []
                for item in points:
                    native = item["native_identity"]
                    if native not in chosen:
                        continue
                    if native in existing_native:
                        skipped.append(native)
                        continue
                    point = Point(
                        name=item["name"], device_id=device.id, data_type=item["data_type"],
                        unit=item["unit"], direction=PointDirection(item["direction"]),
                        source_ref=native, native_identity=native, object_type=item["object_type"],
                        engineering_description=item["engineering_description"],
                        quality=PointQuality.UNCERTAIN, licensed_active=False,
                    )
                    pending_points.append((native, point))
                self.core.objects.assert_point_usage_transition(existing_rows, [point for _, point in pending_points])
                for native, point in pending_points:
                    self.repository.save(point, connection=connection)
                    added.append(point.id)
                    existing_native.add(native)
    
                # Driver configuration and engineering records commit together. Existing
                # bindings are preserved; a point can never be bound twice.
                if added:
                    config = dict(driver_item.config)
                    bindings = list(config.get("bindings") or [])
                    existing_binding_ids = {str(x.get("point_id")) for x in bindings if isinstance(x, dict)}
                    new_bindings = []
                    for point_id, item in zip(added, [x for x in selected_items
                                                      if x["native_identity"] not in skipped]):
                        if point_id in existing_binding_ids:
                            raise ValueError(f"Для точки {point_id} уже существует binding драйвера")
                        new_bindings.append({"point_id": point_id, **templates[item["native_identity"]]})
                    config["bindings"] = bindings + new_bindings
                    if info["protocol"] == "modbus/tcp":
                        host, sep, port_text = info["address"].rpartition(":")
                        if not sep:
                            host, port_text = info["address"], "502"
                        config.setdefault("host", host)
                        config.setdefault("port", int(port_text))
                        config.setdefault("unit_id", 1)
                    driver_item.config = config
                    driver_item.updated_at = datetime.now(timezone.utc)
                    self.repository.save(driver_item, expected_version=driver_version, connection=connection)

        return {
            "device_id": device.id, "device_created": created_device,
            "driver_instance_id": driver_instance_id, "protocol": info["protocol"],
            "points_added": added, "points_skipped_existing": skipped,
            "selected_count": len(chosen), "mode": "read_only",
            "write_enabled": False, "field_device_writes": False,
        }
