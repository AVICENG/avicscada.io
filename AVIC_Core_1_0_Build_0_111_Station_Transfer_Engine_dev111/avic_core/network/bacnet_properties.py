"""Read-only BACnet object property snapshots and Trend IQ3 catalog helpers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from .bacnet_ip import BacnetObjectIdentifier, BacnetProtocolError

# Standard BACnet property identifiers used by this increment.
PROPERTY_IDS = {
    "description": 28,
    "effective_period": 32,
    "exception_schedule": 38,
    "firmware_revision": 44,
    "model_name": 70,
    "object_identifier": 75,
    "object_list": 76,
    "object_name": 77,
    "out_of_service": 81,
    "present_value": 85,
    "reliability": 103,
    "status_flags": 111,
    "units": 117,
    "vendor_id": 118,
    "vendor_name": 119,
    "weekly_schedule": 123,
}


class ReadPropertyClient(Protocol):
    def read_property(self, address: tuple[str, int], device_instance: int,
                      object_type: int, object_instance: int, property_id: int,
                      timeout_seconds: float | None = None, array_index: int | None = None) -> Any: ...


@dataclass(frozen=True)
class BacnetPropertyResult:
    property_name: str
    property_id: int
    value: Any = None
    error: str | None = None
    @property
    def supported(self) -> bool:
        return self.error is None


@dataclass(frozen=True)
class BacnetObjectSnapshot:
    object_identifier: BacnetObjectIdentifier
    native_identity: str
    properties: dict[str, BacnetPropertyResult] = field(default_factory=dict)

    def value(self, name: str) -> Any:
        result = self.properties.get(name)
        return result.value if result and result.supported else None

    @property
    def quality(self) -> str:
        pv = self.properties.get("present_value")
        if pv is None or not pv.supported:
            return "unknown"
        reliability = self.properties.get("reliability")
        flags = self.properties.get("status_flags")
        if reliability and reliability.supported and reliability.value not in (0, "no-fault-detected"):
            return "unreliable"
        if flags and flags.supported and flags.value not in ("0000", "00000", 0, b"\x00"):
            return "flagged"
        return "good"


_POINT_PROPERTIES = ("object_name", "description", "present_value", "units",
                     "status_flags", "reliability", "out_of_service")
_SCHEDULE_PROPERTIES = ("object_name", "description", "present_value",
                        "weekly_schedule", "exception_schedule", "effective_period")


class BacnetObjectReader:
    """Reads object metadata/values; each property failure is isolated and retained."""
    def __init__(self, client: ReadPropertyClient, *, timeout_seconds: float | None = None):
        self.client = client
        self.timeout_seconds = timeout_seconds

    def read_snapshot(self, address: tuple[str, int], device_instance: int,
                      obj: BacnetObjectIdentifier) -> BacnetObjectSnapshot:
        names = _SCHEDULE_PROPERTIES if obj.object_type == 17 else _POINT_PROPERTIES
        results: dict[str, BacnetPropertyResult] = {}
        for name in names:
            property_id = PROPERTY_IDS[name]
            try:
                value = self.client.read_property(address, device_instance, obj.object_type,
                                                  obj.instance, property_id,
                                                  timeout_seconds=self.timeout_seconds)
                results[name] = BacnetPropertyResult(name, property_id, value=value)
            except (TimeoutError, BacnetProtocolError, OSError) as exc:
                results[name] = BacnetPropertyResult(name, property_id, error=str(exc))
        return BacnetObjectSnapshot(obj, obj.native_identity, results)

    def read_catalog(self, address: tuple[str, int], device_instance: int,
                     objects: list[BacnetObjectIdentifier]) -> list[BacnetObjectSnapshot]:
        """Read only point-like and schedule objects; retain every native object ID."""
        return [self.read_snapshot(address, device_instance, obj)
                for obj in objects if obj.object_type in (0, 1, 2, 3, 4, 5, 17)]


def trend_iq3_role(obj: BacnetObjectIdentifier) -> str:
    """Return a conservative category; physical/logical mapping needs engineering confirmation."""
    return {1: "analog-output", 3: "binary-input", 17: "schedule"}.get(
        obj.object_type, obj.type_name)


@dataclass(frozen=True)
class BacnetDeviceInspection:
    """Read-only device identity plus complete Object_List and readable point snapshots."""
    device_identity: dict[str, Any]
    objects: tuple[dict[str, Any], ...]
    point_snapshots: tuple[BacnetObjectSnapshot, ...]
    warnings: tuple[str, ...] = ()


class BacnetDeviceInspector:
    """Generic BACnet inspector; no Trend-specific assumptions and no write services."""
    def __init__(self, client: Any, reader: BacnetObjectReader | None = None):
        self.client = client
        self.reader = reader or BacnetObjectReader(client)

    def inspect(self, address: tuple[str, int], device_instance: int, *,
                max_objects: int = 4096) -> BacnetDeviceInspection:
        identity = self.client.read_device_identity(address, device_instance)
        native_objects = self.client.read_object_list(address, device_instance,
                                                       max_objects=max_objects)
        objects: list[dict[str, Any]] = []
        warnings: list[str] = []
        for obj in native_objects:
            try:
                name = self.client.read_object_name(address, device_instance, obj)
            except (TimeoutError, BacnetProtocolError, OSError) as exc:
                name = None
                warnings.append(f"{obj.native_identity}: Object_Name unavailable: {exc}")
            objects.append({"object_type": obj.object_type, "type_name": obj.type_name,
                            "instance": obj.instance, "native_identity": obj.native_identity,
                            "object_name": name})
        snapshots = self.reader.read_catalog(address, device_instance, native_objects)
        return BacnetDeviceInspection(identity, tuple(objects), tuple(snapshots), tuple(warnings))
