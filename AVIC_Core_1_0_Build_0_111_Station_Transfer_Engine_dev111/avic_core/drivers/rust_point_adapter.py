"""Read-only Rust-backed protocol adapter for AVIC Point Runtime.

The Rust worker returns transport results only. This adapter owns binding lookup,
type conversion, quality transitions and publication into the shared Point Runtime.
"""
from __future__ import annotations

from math import isfinite
import ipaddress
from typing import Any

from avic_core.drivers.rust_worker import RustDriverWorker
from avic_core.network.modbus_tcp import decode_registers


_BACNET_OBJECT_TYPE_NAMES = {
    0: "AnalogInput", 1: "AnalogOutput", 2: "AnalogValue",
    3: "BinaryInput", 4: "BinaryOutput", 5: "BinaryValue",
    6: "Calendar", 7: "Command", 8: "Device", 9: "EventEnrollment",
    10: "File", 11: "Group", 12: "Loop", 13: "MultiStateInput",
    14: "MultiStateOutput", 15: "NotificationClass", 16: "Program",
    17: "Schedule", 18: "Averaging", 19: "MultiStateValue",
    20: "TrendLog", 21: "LifeSafetyPoint", 22: "LifeSafetyZone",
    23: "Accumulator", 24: "PulseConverter", 25: "EventLog",
    26: "GlobalGroup", 27: "TrendLogMultiple", 28: "LoadControl",
    29: "StructuredView", 30: "AccessDoor",
}


class RustDriverConfigurationError(ValueError):
    """Binding/configuration error, not a field communication failure."""


class RustDriverPointAdapter:
    """Common Point Runtime adapter for Rust Modbus/BACnet/KNX worker reads."""

    def __init__(self, *, worker_command, core, driver_instance_id: str,
                 protocol: str, config: dict[str, Any], bindings: list[dict[str, Any]],
                 installation_id: str, project_id: str, station_id: str,
                 generation: int = 1, timeout_seconds: float = 5.0, worker_mode: str = "RUST_WORKER_READ_ONLY") -> None:
        from avic_core.domain.models import PointQuality

        if protocol not in {"modbus-tcp", "bacnet-ip", "knxnet-ip"}:
            raise ValueError("unsupported Rust driver protocol")
        if not bindings:
            raise ValueError("Rust driver requires at least one point binding")
        self.protocol = protocol
        self.worker_mode = worker_mode
        self.core = core
        self._config = dict(config)
        self.point_runtime = core.point_runtime
        self.driver_instance_id = driver_instance_id
        self.bindings = tuple(dict(item) for item in bindings)
        self._last_errors: dict[str, str] = {}
        self._success_count = 0
        self._failure_count = 0
        self._closed = False
        self._PointQuality = PointQuality
        self._worker = RustDriverWorker(
            worker_command,
            installation_id=installation_id,
            project_id=project_id,
            station_id=station_id,
            driver_instance_id=driver_instance_id,
            generation=generation,
            timeout_seconds=max(8.0, float(timeout_seconds), float(config.get("timeout") or 2.0) * 2.0 + 2.0),
        )
        worker_config = {k: v for k, v in config.items()
                         if k not in {"bindings", "poll_interval_seconds", "project_id", "station_id", "engine"}}
        worker_config["protocol"] = protocol
        self._worker.start(worker_config)

    def _mark_failure(self, point_id: str, error: str, quality=None) -> dict:
        quality = quality or self._PointQuality.BAD_COMMUNICATION
        self._last_errors[point_id] = error
        self._failure_count += 1
        try:
            sample = self.point_runtime.mark_quality(
                point_id, quality, source_driver_id=self.driver_instance_id)
            return {"point_id": point_id, "ok": False, "value": sample.value,
                    "quality": sample.quality, "error": error}
        except Exception as exc:
            return {"point_id": point_id, "ok": False, "quality": "UNKNOWN",
                    "error": error, "quality_error": f"{type(exc).__name__}: {exc}"}

    @staticmethod
    def _scaled(value: Any, scale: float, offset: float) -> Any:
        if isinstance(value, bool):
            if scale != 1.0 or offset != 0.0:
                raise ValueError("scale/offset is not valid for boolean protocol values")
            return value
        if isinstance(value, (int, float)):
            if not isfinite(float(value)):
                raise ValueError("protocol value is not finite")
            result = float(value) * float(scale) + float(offset)
            if not isfinite(result):
                raise ValueError("scaled protocol value is not finite")
            return result
        if scale != 1.0 or offset != 0.0:
            raise ValueError("scale/offset requires numeric protocol values")
        return value

    def _read_modbus(self, binding: dict[str, Any]) -> Any:
        response = self._worker.read({
            "protocol": "modbus-tcp",
            "host": self._config["host"], "port": int(self._config.get("port", 502)),
            "unit_id": int(self._config.get("unit_id", 1)),
            "timeout_ms": int(float(self._config.get("timeout", 2.0)) * 1000),
            "function": int(binding["function"]), "address": int(binding["address"]),
            "count": int(binding.get("count", 1)),
        })
        result = response.get("result", {})
        values = result.get("values")
        if not isinstance(values, list):
            raise ValueError("Rust Modbus worker returned no values")
        function = int(binding["function"])
        if function in (1, 2):
            if len(values) != 1 or not isinstance(values[0], bool):
                raise ValueError("Rust Modbus bit read returned an invalid shape")
            return values[0]
        value = decode_registers(
            values, binding.get("data_type", "uint16"),
            byte_order=binding.get("byte_order", "big"),
            word_order=binding.get("word_order", "big"),
        )
        return self._scaled(value, float(binding.get("scale", 1.0)), float(binding.get("offset", 0.0)))

    def _read_bacnet_batch(self, address: tuple[str, int], device_instance: int) -> dict[tuple[str, int, int], Any]:
        result = self._worker.read({
            "protocol": "bacnet-ip", "address": f"{address[0]}:{int(address[1])}",
            "local_bind": f"{self._config['local_address']}:{int(self._config.get('udp_port', 47808))}",
            "timeout_ms": int(float(self._config.get("timeout", 3.0)) * 1000),
            "device_instance": int(device_instance),
        }).get("result", {})
        device = result.get("device", {})
        if int(device.get("device_instance", -1)) != int(device_instance):
            raise ValueError("BACnet worker returned a different Device Instance")
        objects = result.get("objects")
        if not isinstance(objects, list):
            raise ValueError("Rust BACnet worker returned no object list")
        values = {}
        for obj in objects:
            if not isinstance(obj, dict):
                continue
            key = (str(obj.get("object_type_name")), int(obj.get("object_instance", -1)),
                   int(device_instance))
            if obj.get("present_value") is not None:
                values[key] = {
                    "value": obj["present_value"],
                    "status_flags": obj.get("status_flags"),
                    "units": obj.get("units"),
                }
        return values

    def _read_knx(self, binding: dict[str, Any]) -> Any:
        raw = int(binding["group_address"])
        group_address = f"{(raw >> 11) & 0x1f}/{(raw >> 8) & 0x07}/{raw & 0xff}"
        gateway_ip = ipaddress.ip_address(self._config["gateway_host"])
        local_ip = ipaddress.ip_address(self._config["local_host"])
        gateway_port = int(self._config.get("gateway_port", 3671))
        local_port = int(self._config.get("local_port", 0))
        gateway = f"[{gateway_ip}]:{gateway_port}" if gateway_ip.version == 6 else f"{gateway_ip}:{gateway_port}"
        local_bind = f"[{local_ip}]:{local_port}" if local_ip.version == 6 else f"{local_ip}:{local_port}"
        result = self._worker.read({
            "protocol": "knxnet-ip", "gateway": gateway, "local_bind": local_bind,
            "group_address": group_address, "dpt": binding["datapoint_type"],
            "timeout_ms": int(float(self._config.get("timeout", 1.0)) * 1000),
        }).get("result", {})
        if "value" not in result:
            raise ValueError("Rust KNX worker returned no value")
        return result["value"]

    def poll_once(self) -> dict:
        # BACnet object lists are fetched once per unique device per poll.
        bacnet_values_by_device: dict[tuple[str, int, int], dict] = {}
        bacnet_errors: dict[tuple[str, int, int], str] = {}
        if self.protocol == "bacnet-ip":
            groups = {}
            for binding in self.bindings:
                address = tuple(binding["address"])
                device_instance = int(binding["device_instance"])
                key = (str(address[0]), int(address[1]), device_instance)
                groups.setdefault(key, (address, device_instance))
            for key, (address, device_instance) in groups.items():
                try:
                    bacnet_values_by_device[key] = self._read_bacnet_batch(address, device_instance)
                except Exception as exc:
                    bacnet_errors[key] = f"{type(exc).__name__}: {exc}"

        rows = []
        for binding in self.bindings:
            point_id = binding["point_id"]
            try:
                if self.protocol == "modbus-tcp":
                    value = self._read_modbus(binding)
                elif self.protocol == "bacnet-ip":
                    address = tuple(binding["address"])
                    device_instance = int(binding["device_instance"])
                    device_key = (str(address[0]), int(address[1]), device_instance)
                    if device_key in bacnet_errors:
                        raise RuntimeError(bacnet_errors[device_key])
                    if int(binding.get("property_id", 85)) != 85 or binding.get("array_index") is not None:
                        raise RustDriverConfigurationError("Rust BACnet adapter currently supports Present_Value (property 85) without array index")
                    name = _BACNET_OBJECT_TYPE_NAMES.get(int(binding["object_type"]))
                    if name is None:
                        raise RustDriverConfigurationError(f"Unsupported BACnet object type code: {binding['object_type']}")
                    key = (name, int(binding["object_instance"]), device_instance)
                    bacnet_values = bacnet_values_by_device.get(device_key, {})
                    if key not in bacnet_values:
                        raise RustDriverConfigurationError(f"BACnet object {name}:{binding['object_instance']} has no Present_Value")
                    object_data = bacnet_values[key]
                    value = self._scaled(
                        object_data["value"], float(binding.get("scale", 1.0)),
                        float(binding.get("offset", 0.0)))
                    flags = object_data.get("status_flags")
                    if not isinstance(flags, list) or len(flags) != 4 or any(not isinstance(flag, bool) for flag in flags):
                        sample_quality = self._PointQuality.UNCERTAIN
                    elif flags[3]:  # BACnet out_of_service
                        sample_quality = self._PointQuality.DISABLED
                    elif flags[1]:  # BACnet fault
                        sample_quality = self._PointQuality.BAD_COMMUNICATION
                    elif flags[2]:  # overridden
                        sample_quality = self._PointQuality.UNCERTAIN
                    else:
                        sample_quality = self._PointQuality.GOOD
                else:
                    value = self._read_knx(binding)
                    sample_quality = self._PointQuality.GOOD
                if self.protocol == "modbus-tcp":
                    sample_quality = self._PointQuality.GOOD
                sample = self.point_runtime.publish(
                    point_id, value, quality=sample_quality,
                    source_driver_id=self.driver_instance_id)
                self._last_errors.pop(point_id, None)
                self._success_count += 1
                rows.append({"point_id": point_id, "ok": True,
                             "value": sample.value, "quality": sample.quality})
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                quality = self._PointQuality.BAD_CONFIGURATION if isinstance(exc, RustDriverConfigurationError) else self._PointQuality.BAD_COMMUNICATION
                rows.append(self._mark_failure(point_id, message, quality=quality))
        return self._result(rows)

    def _result(self, rows: list[dict]) -> dict:
        return {"driver_instance_id": self.driver_instance_id, "polled": len(rows),
                "success_count": self._success_count, "failure_count": self._failure_count,
                "results": rows}

    def diagnostics(self) -> dict:
        return {"driver_id": self.protocol, "mode": self.worker_mode,
                "write_supported": False, "configured_points": len(self.bindings),
                "success_count": self._success_count, "failure_count": self._failure_count,
                "last_errors": dict(self._last_errors), "worker": self._worker.diagnostics()}

    def close(self) -> None:
        if self._closed:
            return
        close_error = None
        try:
            self._worker.close()
            self._closed = True
        except Exception as exc:
            self._closed = False
            close_error = exc
        for binding in self.bindings:
            try:
                self.point_runtime.mark_quality(
                    binding["point_id"], self._PointQuality.STALE,
                    source_driver_id=self.driver_instance_id,
                )
            except Exception as exc:
                close_error = close_error or exc
        if close_error is not None:
            raise close_error
