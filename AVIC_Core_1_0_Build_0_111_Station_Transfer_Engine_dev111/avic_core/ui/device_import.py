from __future__ import annotations
from typing import Any
from uuid import uuid4
from avic_core.domain.models import Device, Point, DriverInstance, DriverPackage, PointDirection, PointQuality
from avic_core.repository.sqlite_repository import EntityNotFound


class DeviceImportService:
    """Idempotent, read-only discovery import into a selected station."""
    def __init__(self, core):
        self.core = core

    def preview_bacnet(self, station_id: str, inspection: dict[str, Any], selected_native_ids: list[str] | None = None,
                       import_all: bool = False) -> dict[str, Any]:
        """Build a non-mutating import preview with duplicate and unknown-selection checks."""
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        ident = inspection.get("device_identity") or {}
        instance = int(ident.get("device_instance") or inspection.get("device_instance") or 0)
        address = str(inspection.get("address") or "").strip()
        if not address:
            raise ValueError("В inspection отсутствует адрес устройства")
        device_native = f"bacnet:device:{instance}@{address}"
        existing_device = next((r for r in self.core.repository.list_records(entity_type="Device", station_id=station_id)
                                if r["payload"].get("native_identity") == device_native), None)
        device_id = existing_device["entity_id"] if existing_device else None
        objects = list(inspection.get("objects") or [])
        available = {str(o.get("native_identity") or "") for o in objects if o.get("native_identity")}
        requested = available if import_all else set(selected_native_ids or [])
        unknown = sorted(requested - available)
        requested &= available
        existing_keys = set()
        if device_id:
            existing_keys = {r["payload"].get("native_identity") for r in self.core.repository.list_records(entity_type="Point")
                             if r["payload"].get("device_id") == device_id}
        duplicates = sorted(k for k in requested if k in existing_keys)
        new_points = sorted(requested - existing_keys)
        return {"station_id": station_id, "device_native_identity": device_native,
                "device_exists": bool(existing_device), "device_id": device_id,
                "discovered_points": len(objects), "selected_points": len(requested),
                "new_points": new_points, "duplicate_points": duplicates,
                "unknown_selection": unknown, "can_import": bool(requested) and not unknown,
                "write_enabled": False, "field_device_writes": False}

    def import_bacnet(self, station_id: str, inspection: dict[str, Any], selected_native_ids: list[str] | None = None,
                      import_all: bool = False, engineering_description: str = "",
                      interface_id: str = "", udp_port: int = 47808) -> dict[str, Any]:
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        ident = inspection.get("device_identity") or {}
        objects = list(inspection.get("objects") or [])
        address = str(inspection.get("address") or "")
        instance = int(ident.get("device_instance") or inspection.get("device_instance") or 0)
        protocol = "bacnet/ip"
        device_native = f"bacnet:device:{instance}@{address}"
        existing = None
        for row in self.core.repository.list_records(entity_type="Device", station_id=station_id):
            if row["payload"].get("native_identity") == device_native:
                existing = row
                break
        if existing:
            device, version = self.core.repository.get(existing["entity_id"], Device)
            device.manufacturer = ident.get("manufacturer") or device.manufacturer
            device.model = ident.get("model") or device.model
            device.firmware_revision = ident.get("firmware_revision") or device.firmware_revision
            device.vendor_id = ident.get("vendor_id") if ident.get("vendor_id") is not None else device.vendor_id
            device.identity_sources = {**device.identity_sources, **(ident.get("identity_sources") or {})}
            if engineering_description:
                device.engineering_description = engineering_description
            self.core.repository.save(device, expected_version=version)
            if device.driver_instance_id:
                try:
                    driver, driver_version = self.core.repository.get(device.driver_instance_id, DriverInstance)
                    driver.configuration = {**driver.configuration, "network_id": inspection.get("network_id", ""),
                        "interface_id": interface_id, "udp_port": udp_port, "mode": "read_only"}
                    self.core.repository.save(driver, expected_version=driver_version)
                except EntityNotFound:
                    pass
            created_device = False
        else:
            # A built-in driver is still represented by an installed package record:
            # DomainIntegrityService validates DriverInstance.package_id against it.
            package_id = "bacnet-ip"
            installed = next((row for row in self.core.repository.list_records(entity_type="DriverPackage")
                              if row.get("payload", {}).get("package_id") == package_id
                              and row.get("payload", {}).get("version") == "1.0"), None)
            if installed is None:
                self.core.repository.save(DriverPackage(
                    name="BACnet/IP", package_id=package_id, version="1.0",
                    vendor="AVIC", core_api_version="1.0", signature_status="BUILTIN",
                ))
            driver = DriverInstance(name="BACnet/IP", station_id=station_id, package_id=package_id,
                package_version="1.0", configuration={"network_id": inspection.get("network_id", ""), "interface_id": interface_id,
                               "udp_port": udp_port, "mode": "read_only"})
            self.core.repository.save(driver)
            device = Device(name=ident.get("model") or f"BACnet Device {instance}", station_id=station_id,
                driver_instance_id=driver.id, address=address, protocol=protocol,
                network_id=str(inspection.get("network_id") or ""), native_identity=device_native,
                manufacturer=str(ident.get("manufacturer") or ""), model=str(ident.get("model") or ""),
                firmware_revision=str(ident.get("firmware_revision") or ""), vendor_id=ident.get("vendor_id"),
                identity_sources=dict(ident.get("identity_sources") or {}), engineering_description=engineering_description)
            self.core.repository.save(device)
            created_device = True
        chosen = set(selected_native_ids or [])
        if import_all:
            chosen = {str(o.get("native_identity") or "") for o in objects}
        if not import_all and selected_native_ids is None:
            chosen = set()
        existing_points = {r["payload"].get("native_identity"): r for r in self.core.repository.list_records(entity_type="Point")
                           if r["payload"].get("device_id") == device.id}
        added, updated, skipped = [], [], []
        for obj in objects:
            native = str(obj.get("native_identity") or "")
            if not native or native not in chosen:
                continue
            if native in existing_points:
                skipped.append(native)
                continue
            object_type = str(obj.get("type_name") or "unknown")
            direction = PointDirection.OUTPUT if "output" in object_type else PointDirection.INPUT
            point = Point(name=str(obj.get("object_name") or f"{object_type} {obj.get('instance', '')}"),
                device_id=device.id, data_type=object_type, direction=direction, source_ref=native,
                native_identity=native, object_type=object_type, quality=PointQuality.UNCERTAIN,
                licensed_active=False)
            self.core.objects.save_graph([point])
            added.append(point.id)
        return {"device_id": device.id, "device_created": created_device, "points_added": added,
                "points_skipped_existing": skipped, "selected_count": len(chosen),
                "device_native_identity": device_native, "mode": "read_only", "write_enabled": False}

    def station_tree(self, station_id: str) -> dict[str, Any]:
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        devices = []
        for row in self.core.repository.list_records(entity_type="Device", station_id=station_id):
            d = row["payload"]
            points = []
            for pr in self.core.repository.list_records(entity_type="Point"):
                if pr["payload"].get("device_id") == row["entity_id"]:
                    points.append({"id": pr["entity_id"], "name": pr["name"], "native_identity": pr["payload"].get("native_identity"),
                                   "object_type": pr["payload"].get("object_type"), "data_type": pr["payload"].get("data_type"),
                                   "direction": getattr(pr["payload"].get("direction"), "value", pr["payload"].get("direction")),
                                   "description": pr["payload"].get("engineering_description", ""),
                                   "value": pr["payload"].get("value"), "unit": pr["payload"].get("unit", ""),
                                   "quality": getattr(pr["payload"].get("quality"), "value", pr["payload"].get("quality", "UNCERTAIN")),
                                   "timestamp": pr["payload"].get("timestamp")})
            devices.append({"id": row["entity_id"], "name": row["name"], "address": d.get("address"),
                "protocol": d.get("protocol"), "manufacturer": d.get("manufacturer"), "model": d.get("model"), "points": points})
        return {"station_id": station_id, "devices": devices}
