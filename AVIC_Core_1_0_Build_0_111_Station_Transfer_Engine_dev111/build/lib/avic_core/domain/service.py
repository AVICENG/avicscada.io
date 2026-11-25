from __future__ import annotations
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from avic_core.repository.sqlite_repository import SQLiteRepository
from .models import (
    Project, Station, Device, Point, Component, Link, PropertyDefinition, Alarm,
    Event, HistoryRecord, DriverInstance, DriverPackage, RuntimeInstance,
)


class DomainIntegrityError(ValueError):
    pass


class CoreObjectService:
    """Validates cross-object references and commits a related object graph atomically."""
    def __init__(self, repository: SQLiteRepository, *, license_service=None, license_file=None):
        self.repository = repository
        if (license_service is None) != (license_file is None):
            raise ValueError("license_service и license_file должны передаваться вместе")
        self.license_service = license_service
        self.license_file = license_file

    @staticmethod
    def _record_station(entity_type: str, payload: dict[str, Any], by_id: dict[str, tuple[str, dict]]) -> str | None:
        if entity_type == "Station":
            return payload.get("id")
        if "station_id" in payload and payload.get("station_id"):
            return payload["station_id"]
        if entity_type == "Point":
            device = by_id.get(payload.get("device_id", ""))
            if device:
                return device[1].get("station_id")
        return None

    def _validate_graph(self, by_id: dict[str, tuple[str, dict]]):
        def require(ref_id: str | None, expected: set[str], context: str):
            if not ref_id:
                raise DomainIntegrityError(f"{context}: required reference is missing")
            found = by_id.get(ref_id)
            if found is None or found[0] not in expected:
                raise DomainIntegrityError(f"{context}: {ref_id} does not reference {', '.join(sorted(expected))}")
            return found

        for entity_id, (kind, payload) in by_id.items():
            if kind == "Project":
                if payload.get("platform_id"):
                    require(payload["platform_id"], {"Platform"}, f"Project {entity_id}.platform_id")
            elif kind == "Station":
                require(payload.get("project_id"), {"Project"}, f"Station {entity_id}.project_id")
            elif kind == "Device":
                require(payload.get("station_id"), {"Station"}, f"Device {entity_id}.station_id")
                if payload.get("driver_instance_id"):
                    require(payload["driver_instance_id"], {"DriverInstance"}, f"Device {entity_id}.driver_instance_id")
            elif kind == "Point":
                require(payload.get("device_id"), {"Device"}, f"Point {entity_id}.device_id")
            elif kind == "Component":
                require(payload.get("station_id"), {"Station"}, f"Component {entity_id}.station_id")
            elif kind == "PropertyDefinition":
                require(payload.get("owner_object_id"), {"Platform", "Project", "Station", "Device", "Point", "Component"}, f"PropertyDefinition {entity_id}.owner_object_id")
            elif kind == "Link":
                station_id = require(payload.get("station_id"), {"Station"}, f"Link {entity_id}.station_id")[1]["id"]
                for field in ("source_object_id", "target_object_id"):
                    ref = require(payload.get(field), {"Device", "Point", "Component"}, f"Link {entity_id}.{field}")
                    ref_station = self._record_station(ref[0], ref[1], by_id)
                    if ref_station != station_id:
                        raise DomainIntegrityError(f"Link {entity_id}: endpoints must belong to the same station")
            elif kind == "Alarm":
                require(payload.get("station_id"), {"Station"}, f"Alarm {entity_id}.station_id")
                if payload.get("source_object_id"):
                    source = require(payload["source_object_id"], {"Device", "Point", "Component"}, f"Alarm {entity_id}.source_object_id")
                    if self._record_station(source[0], source[1], by_id) != payload.get("station_id"):
                        raise DomainIntegrityError(f"Alarm {entity_id}: source belongs to another station")
            elif kind == "Event":
                require(payload.get("station_id"), {"Station"}, f"Event {entity_id}.station_id")
                if payload.get("source_object_id"):
                    source = require(payload["source_object_id"], {"Device", "Point", "Component", "Alarm"}, f"Event {entity_id}.source_object_id")
                    if self._record_station(source[0], source[1], by_id) != payload.get("station_id"):
                        raise DomainIntegrityError(f"Event {entity_id}: source belongs to another station")
            elif kind == "HistoryRecord":
                require(payload.get("station_id"), {"Station"}, f"HistoryRecord {entity_id}.station_id")
                point = require(payload.get("point_id"), {"Point"}, f"HistoryRecord {entity_id}.point_id")
                if self._record_station(point[0], point[1], by_id) != payload.get("station_id"):
                    raise DomainIntegrityError(f"HistoryRecord {entity_id}: point belongs to another station")
            elif kind == "DriverInstance":
                require(payload.get("station_id"), {"Station"}, f"DriverInstance {entity_id}.station_id")
                package_id = payload.get("package_id")
                if package_id and not any(k == "DriverPackage" and p.get("package_id") == package_id for k, p in by_id.values()):
                    raise DomainIntegrityError(f"DriverInstance {entity_id}: driver package {package_id} is not installed")
            elif kind == "RuntimeInstance":
                require(payload.get("station_id"), {"Station"}, f"RuntimeInstance {entity_id}.station_id")

    def save_graph(self, entities: Iterable[Any], *, expected_versions: dict[str, int] | None = None) -> dict[str, int]:
        items = list(entities)
        if not items:
            return {}
        if any(not is_dataclass(item) for item in items):
            raise TypeError("Core object graph accepts dataclass entities only")
        expected_versions = expected_versions or {}
        with self.repository.transaction() as connection:
            existing = self.repository.list_records(connection=connection)
            by_id: dict[str, tuple[str, dict]] = {
                record["entity_id"]: (record["entity_type"], record["payload"]) for record in existing
            }
            seen = set()
            for item in items:
                entity_id = str(item.id)
                if entity_id in seen:
                    raise DomainIntegrityError(f"Duplicate entity in transaction: {entity_id}")
                seen.add(entity_id)
                by_id[entity_id] = (item.__class__.__name__, asdict(item))

            # Enforce licensing inside the same repository transaction as Point creation.
            # Existing Point UUIDs are updates and do not consume another slot.
            new_points = [item for item in items
                          if isinstance(item, Point)
                          and not any(r["entity_id"] == str(item.id) and r["entity_type"] == "Point" for r in existing)]
            if new_points and self.license_service is not None:
                status = self.license_service.inspect(self.license_file).status
                current_point_ids = {r["entity_id"] for r in existing if r["entity_type"] == "Point"}
                for point in new_points:
                    self.license_service.assert_can_create_point(status, current_point_ids, str(point.id))
                    current_point_ids.add(str(point.id))

            self._validate_graph(by_id)
            versions = {}
            for item in items:
                entity_id = str(item.id)
                current = next((r for r in existing if r["entity_id"] == entity_id), None)
                expected = expected_versions.get(entity_id)
                if current is None and expected is not None:
                    raise DomainIntegrityError(f"New entity {entity_id} must not have an expected version")
                if current is not None and expected is None:
                    raise DomainIntegrityError(f"Updating {entity_id} requires expected_versions[{entity_id}]")
                versions[entity_id] = self.repository.save(item, expected_version=expected, connection=connection)
            return versions

    def delete_graph(self, entity_versions: dict[str, int]) -> None:
        """Delete a related set only when no remaining object references it."""
        if not entity_versions:
            return
        with self.repository.transaction() as connection:
            records = self.repository.list_records(connection=connection)
            deleting = set(entity_versions)
            existing_ids = {record["entity_id"] for record in records}
            if not deleting.issubset(existing_ids):
                missing = sorted(deleting - existing_ids)
                raise DomainIntegrityError(f"Cannot delete missing entities: {', '.join(missing)}")
            remaining = {
                record["entity_id"]: (record["entity_type"], record["payload"])
                for record in records if record["entity_id"] not in deleting
            }
            self._validate_graph(remaining)
            for entity_id, expected_version in entity_versions.items():
                self.repository.delete(entity_id, expected_version=expected_version, connection=connection)
