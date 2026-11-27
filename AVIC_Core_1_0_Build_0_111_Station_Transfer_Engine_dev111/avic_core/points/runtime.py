from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from threading import RLock
from typing import Any, Callable
from uuid import UUID

from avic_core.domain.models import BaseObject, Point, PointDirection, PointQuality


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class PointRuntimeValue:
    point_id: str
    value: Any
    quality: str
    timestamp: datetime | None
    unit: str
    data_type: str
    source: str
    revision: int


@dataclass(slots=True)
class FBDExposedPoint(BaseObject):
    """Virtual, read-only point published by an executable FBD output port."""
    station_id: str = ""
    fbd_document_id: str = ""
    studio_document_id: str = ""
    source_module_id: str = ""
    source_port: str = "OUT"
    data_type: str = "analog"
    unit: str = ""
    value: Any = None
    quality: str = "UNCERTAIN"
    timestamp: datetime | None = None
    native_identity: str = ""
    source_ref: str = ""
    direction: str = "output"

    def update_value(self, value: Any, quality: str, timestamp: datetime | None = None):
        self.value = value
        self.quality = str(quality).upper()
        self.timestamp = timestamp or _utcnow()
        self.updated_at = _utcnow()


class PointRuntimeService:
    """Single in-process value authority for physical and internal AVIC points.

    Drivers publish validated input samples here. FBD, graphics, alarms and history
    consume the same point identity/value/quality. This service does not open sockets,
    poll devices, or write field outputs by itself.
    """

    _QUALITY = {q.value for q in PointQuality}

    def __init__(self, repository):
        self.repository = repository
        self._lock = RLock()
        self._subscribers: dict[str, dict[str, Callable[[PointRuntimeValue], None]]] = {}
        self._subscriber_errors: list[str] = []

    @staticmethod
    def _quality(value: PointQuality | str) -> PointQuality:
        try:
            return value if isinstance(value, PointQuality) else PointQuality(str(value).upper())
        except ValueError as exc:
            raise ValueError(f"Недопустимое качество точки: {value}") from exc

    @staticmethod
    def _validate_value(point: Point, value: Any) -> Any:
        kind = str(point.data_type or "").strip().casefold()
        if kind in {"bool", "boolean", "binary", "digital", "digital input", "digital output"} or kind.startswith(("binary-", "digital-")):
            if not isinstance(value, bool):
                raise ValueError("Для булевой точки требуется bool")
            return value
        if kind in {"float", "double", "real", "analog", "numeric", "number", "float32", "float64"} or kind.startswith(("analog-", "real-")):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
                raise ValueError("Для аналоговой точки требуется конечное число")
            return float(value)
        integer_ranges = {
            "uint8": (0, 255), "uint16": (0, 65535), "uint32": (0, 4294967295),
            "uint64": (0, 18446744073709551615), "int8": (-128, 127),
            "int16": (-32768, 32767), "int32": (-2147483648, 2147483647),
            "int64": (-9223372036854775808, 9223372036854775807),
        }
        if kind in integer_ranges:
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Для целочисленной точки требуется int")
            lower, upper = integer_ranges[kind]
            if not lower <= value <= upper:
                raise ValueError(f"Значение вне диапазона {kind}")
            return value
        if kind in {"int", "integer", "uint", "counter", "long"} or kind.startswith(("multi-state", "integer-")):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError("Для целочисленной точки требуется int")
            return value
        if kind in {"string", "text", "char"}:
            if not isinstance(value, str):
                raise ValueError("Для строковой точки требуется str")
            return value
        if isinstance(value, (dict, list, tuple, set)):
            raise ValueError("Составные значения не поддерживаются в Point Runtime")
        return value

    def _read_entity(self, point_id: str):
        UUID(str(point_id))
        row = self.repository.get_record(str(point_id))
        if row.get("entity_type") == "FBDExposedPoint":
            point, version = self.repository.get(str(point_id), FBDExposedPoint)
            return point, version, None
        if row.get("entity_type") != "Point":
            raise ValueError("Объект не является доступной точкой Runtime")
        point, version = self.repository.get(str(point_id), Point)
        device = self.repository.get_record(point.device_id)
        if device.get("entity_type") != "Device":
            raise ValueError("У точки отсутствует корректное устройство-источник")
        return point, version, device

    def read(self, point_id: str) -> PointRuntimeValue:
        point, version, _ = self._read_entity(point_id)
        return PointRuntimeValue(
            point_id=point.id, value=point.value,
            quality=getattr(point.quality, "value", str(point.quality)).upper(),
            timestamp=point.timestamp, unit=point.unit, data_type=point.data_type,
            source=point.source_ref or point.native_identity or "unassigned",
            revision=version,
        )

    def snapshot(self, *, station_id: str | None = None) -> list[PointRuntimeValue]:
        devices = {r["entity_id"]: r for r in self.repository.list_records(entity_type="Device")}
        values = []
        for row in self.repository.list_records(entity_type="Point"):
            device = devices.get(row.get("payload", {}).get("device_id"))
            if not device:
                continue
            if station_id and device.get("payload", {}).get("station_id") != station_id:
                continue
            values.append(self.read(row["entity_id"]))
        for row in self.repository.list_records(entity_type="FBDExposedPoint"):
            if station_id and row.get("payload", {}).get("station_id") != station_id:
                continue
            values.append(self.read(row["entity_id"]))
        return values

    def publish_fbd(self, point_id: str, value: Any, *, quality: str = "GOOD", timestamp: datetime | None = None) -> PointRuntimeValue:
        """Publish a validated FBD output to its virtual point; this never writes a field device."""
        q = str(quality).upper()
        if q not in {"GOOD", "UNCERTAIN", "BAD", "STALE", "COMM_LOST", "BAD_COMMUNICATION", "BAD_CONFIGURATION"}:
            raise ValueError("Недопустимое качество FBD-точки")
        if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
            raise ValueError("Timestamp должен содержать часовой пояс")
        with self._lock:
            point, version, _ = self._read_entity(point_id)
            if not isinstance(point, FBDExposedPoint):
                raise ValueError("Публикация FBD разрешена только в виртуальную FBD-точку")
            checked = self._validate_value(point, value)
            point.update_value(checked, q, timestamp or _utcnow())
            new_version = self.repository.save(point, expected_version=version)
            result = PointRuntimeValue(point_id=point.id, value=point.value, quality=q, timestamp=point.timestamp,
                unit=point.unit, data_type=point.data_type, source=point.native_identity, revision=new_version)
            subscribers = tuple(self._subscribers.get(point.id, {}).values())
        for callback in subscribers:
            try:
                callback(result)
            except Exception as exc:
                with self._lock:
                    self._subscriber_errors.append(f"{point_id}: {type(exc).__name__}: {exc}")
                    self._subscriber_errors = self._subscriber_errors[-100:]
        return result

    def publish(self, point_id: str, value: Any, *, quality: PointQuality | str = PointQuality.GOOD,
                timestamp: datetime | None = None, source_driver_id: str | None = None) -> PointRuntimeValue:
        """Publish a sample from a trusted driver adapter; never performs field I/O."""
        q = self._quality(quality)
        with self._lock:
            point, version, device = self._read_entity(point_id)
            if not isinstance(point, Point) or device is None:
                raise ValueError("Драйвер не может публиковать в виртуальную FBD-точку")
            direction = getattr(point.direction, "value", str(point.direction)).lower()
            if direction == PointDirection.OUTPUT.value:
                raise ValueError("Драйвер не может публиковать входное измерение в OUTPUT-точку")
            owner = str(device.get("payload", {}).get("driver_instance_id") or "")
            # Adapter-originated samples must prove exact device ownership.
            # An absent owner is not a wildcard: fail closed for legacy/unbound devices.
            if source_driver_id is not None and source_driver_id != owner:
                raise ValueError("Источник публикации не совпадает с драйвером устройства")
            checked = self._validate_value(point, value)
            if timestamp is not None and (timestamp.tzinfo is None or timestamp.utcoffset() is None):
                raise ValueError("Timestamp должен содержать часовой пояс")
            point.update_value(checked, q, timestamp or _utcnow())
            new_version = self.repository.save(point, expected_version=version)
            result = PointRuntimeValue(
                point_id=point.id, value=point.value, quality=q.value, timestamp=point.timestamp,
                unit=point.unit, data_type=point.data_type,
                source=point.source_ref or point.native_identity or "unassigned", revision=new_version,
            )
            subscribers = tuple(self._subscribers.get(point.id, {}).values())
        # Never execute subscriber callbacks while holding the registry lock.
        for callback in subscribers:
            try:
                callback(result)
            except Exception as exc:
                # One broken consumer must not block delivery to other consumers
                # or make a successfully committed point update look unsuccessful.
                with self._lock:
                    self._subscriber_errors.append(f"{point_id}: {type(exc).__name__}: {exc}")
                    self._subscriber_errors = self._subscriber_errors[-100:]
        return result

    def mark_fbd_quality(self, point_id: str, quality: str) -> PointRuntimeValue:
        q = str(quality).upper()
        if q not in {"UNCERTAIN", "BAD", "STALE", "COMM_LOST", "BAD_CONFIGURATION"}:
            raise ValueError("Недопустимое качество FBD-точки")
        with self._lock:
            point, version, _ = self._read_entity(point_id)
            if not isinstance(point, FBDExposedPoint):
                raise ValueError("Качество можно менять только у FBD virtual point")
            point.quality = q
            point.updated_at = _utcnow()
            new_version = self.repository.save(point, expected_version=version)
            result = PointRuntimeValue(point_id=point.id, value=point.value, quality=q, timestamp=point.timestamp,
                unit=point.unit, data_type=point.data_type, source=point.native_identity, revision=new_version)
            subscribers = tuple(self._subscribers.get(point.id, {}).values())
        for callback in subscribers:
            try: callback(result)
            except Exception as exc:
                with self._lock:
                    self._subscriber_errors.append(f"{point_id}: {type(exc).__name__}: {exc}")
                    self._subscriber_errors = self._subscriber_errors[-100:]
        return result

    def mark_quality(self, point_id: str, quality: PointQuality | str, *,
                     source_driver_id: str | None = None) -> PointRuntimeValue:
        """Change input-point quality without replacing its last value or sample timestamp."""
        q = self._quality(quality)
        if q == PointQuality.GOOD:
            raise ValueError("mark_quality cannot restore GOOD without a new sample")
        with self._lock:
            point, version, device = self._read_entity(point_id)
            if not isinstance(point, Point) or device is None:
                raise ValueError("Only a physical input point can be marked by a driver")
            direction = getattr(point.direction, "value", str(point.direction)).lower()
            if direction == PointDirection.OUTPUT.value:
                raise ValueError("A driver cannot mark an OUTPUT point as an input measurement")
            owner = str(device.get("payload", {}).get("driver_instance_id") or "")
            # Quality changes are driver-originated too; unowned points cannot be
            # claimed implicitly by whichever adapter happens to reference them.
            if source_driver_id is not None and source_driver_id != owner:
                raise ValueError("Quality source does not match point's owning driver")
            point.quality = q
            point.updated_at = _utcnow()
            new_version = self.repository.save(point, expected_version=version)
            result = PointRuntimeValue(
                point_id=point.id, value=point.value, quality=q.value, timestamp=point.timestamp,
                unit=point.unit, data_type=point.data_type,
                source=point.source_ref or point.native_identity or "unassigned", revision=new_version,
            )
            subscribers = tuple(self._subscribers.get(point.id, {}).values())
        for callback in subscribers:
            try:
                callback(result)
            except Exception as exc:
                with self._lock:
                    self._subscriber_errors.append(f"{point_id}: {type(exc).__name__}: {exc}")
                    self._subscriber_errors = self._subscriber_errors[-100:]
        return result

    def subscriber_errors(self) -> tuple[str, ...]:
        with self._lock:
            return tuple(self._subscriber_errors)

    def subscribe(self, point_id: str, callback: Callable[[PointRuntimeValue], None]) -> str:
        self._read_entity(point_id)  # validate existence before registering
        if not callable(callback):
            raise TypeError("Подписчик должен быть callable")
        from uuid import uuid4
        token = str(uuid4())
        with self._lock:
            self._subscribers.setdefault(point_id, {})[token] = callback
        return token

    def unsubscribe(self, point_id: str, token: str) -> bool:
        with self._lock:
            callbacks = self._subscribers.get(point_id)
            if not callbacks or token not in callbacks:
                return False
            del callbacks[token]
            if not callbacks:
                self._subscribers.pop(point_id, None)
            return True
