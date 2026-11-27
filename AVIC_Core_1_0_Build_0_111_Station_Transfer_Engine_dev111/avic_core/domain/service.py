from __future__ import annotations
from dataclasses import asdict, is_dataclass
from typing import Any, Iterable

from avic_core.repository.sqlite_repository import SQLiteRepository
from avic_core.licensing.service import summarize_point_usage
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

    def assert_point_usage_transition(self, existing_records: Iterable[dict], point_items: Iterable[Point]) -> None:
        """Check newly activated unique points against the signed installation capacity."""
        candidates = [item for item in point_items if isinstance(item, Point)]
        if self.license_service is None or not candidates:
            return
        status = self.license_service.inspect(self.license_file).status
        existing_point_records = [
            {"entity_type": record["entity_type"], "entity_id": record["entity_id"],
             "payload": record["payload"]}
            for record in existing_records if record["entity_type"] == "Point"
        ]
        resulting_points = {record["entity_id"]: record for record in existing_point_records}
        for item in candidates:
            resulting_points[str(item.id)] = {
                "entity_type": "Point", "entity_id": str(item.id), "payload": asdict(item)
            }
        existing_active = set(summarize_point_usage(existing_point_records)["licensed_active_point_ids"])
        resulting_active = set(summarize_point_usage(resulting_points.values())["licensed_active_point_ids"])
        for point_id in sorted(resulting_active - existing_active):
            self.license_service.assert_can_create_point(status, existing_active, point_id)
            existing_active.add(point_id)

    def set_point_usage(self, source_key: str, point_ids: Iterable[str], *, connection=None) -> dict[str, int]:
        """Reconcile one engineering-use reference set and enforce licensing atomically.

        source_key is a stable owner such as logic:<document-id> or graphics:<document-id>.
        Multiple independent engineering objects can therefore reference the same point.
        """
        if not isinstance(source_key, str) or not any(
            source_key.startswith(prefix) for prefix in
            ("logic:", "graphics:", "alarm:", "history:", "schedule:", "control:")
        ):
            raise ValueError("Unsupported licensed point usage source")
        desired = {str(point_id) for point_id in point_ids if str(point_id)}
        records = self.repository.list_records(entity_type="Point", connection=connection)
        changed = []
        for record in records:
            point_id = record["entity_id"]
            usages = set(record["payload"].get("licensed_usage") or [])
            if source_key not in usages and point_id not in desired:
                continue
            point, version = self.repository.get(point_id, Point, connection=connection)
            had_tracked_usage = bool(point.licensed_usage)
            if point_id in desired:
                if not had_tracked_usage:
                    # Preserve legacy/manual activation separately from the
                    # activation contributed by this set of engineering references.
                    point.licensed_base_active = (
                        bool(point.licensed_active)
                        if point.licensed_active is not None
                        else point.point_type == "physical"
                    )
                usages.add(source_key)
            else:
                usages.discard(source_key)
            point.licensed_usage = sorted(usages)
            if point.licensed_usage:
                point.licensed_active = True
            elif had_tracked_usage:
                point.licensed_active = bool(point.licensed_base_active)
                point.licensed_base_active = None
            changed.append((point, version))
        self.assert_point_usage_transition(records, [point for point, _ in changed])
        versions = {}
        for point, version in changed:
            versions[str(point.id)] = self.repository.save(
                point, expected_version=version, connection=connection
            )
        return versions

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

            self.assert_point_usage_transition(existing, items)

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

            # Alarm domain objects are persistent alarm-rule configuration, unlike
            # transient AlarmService alarm occurrences. Only Point-backed rules
            # activate a licensed point; the reconciliation shares this transaction.
            for item in items:
                if isinstance(item, Alarm):
                    source_type = by_id.get(item.source_object_id, (None, {}))[0]
                    point_ids = [item.source_object_id] if source_type == "Point" else []
                    usage_versions = self.set_point_usage(
                        f"alarm:{item.id}", point_ids, connection=connection
                    )
                    for point_id, point_version in usage_versions.items():
                        if point_id in versions:
                            versions[point_id] = point_version
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
            records_by_id = {record["entity_id"]: record for record in records}

            # Release references from deleted Alarm rules, except when their
            # source Point is also in this deletion batch. In that case the Point
            # row itself is removed, so mutating it first would invalidate the
            # caller's optimistic version supplied for this atomic delete.
            alarm_usages_owned_by_deleted_points: dict[str, set[str]] = {}
            for entity_id in deleting:
                if records_by_id[entity_id]["entity_type"] != "Alarm":
                    continue
                payload = records_by_id[entity_id]["payload"]
                source_id = payload.get("source_object_id")
                source_record = records_by_id.get(source_id)
                if source_record and source_record["entity_type"] == "Point" and source_id in deleting:
                    alarm_usages_owned_by_deleted_points.setdefault(source_id, set()).add(f"alarm:{entity_id}")
                else:
                    self.set_point_usage(f"alarm:{entity_id}", [], connection=connection)

            for entity_id in deleting:
                if records_by_id[entity_id]["entity_type"] == "Point":
                    current = self.repository.get_record(entity_id, connection=connection)
                    usages = set(current.get("payload", {}).get("licensed_usage") or [])
                    usages.difference_update(alarm_usages_owned_by_deleted_points.get(entity_id, set()))
                    if usages:
                        raise DomainIntegrityError(
                            f"Cannot delete licensed Point {entity_id}; remove active usages first: {', '.join(sorted(usages))}"
                        )

            # Validate after usage reconciliation: a Point with a surviving
            # Alarm reference is rejected by the licensing guard above, while
            # deleting both objects in one batch leaves no dangling reference.
            self._validate_graph(remaining)
            for entity_id, expected_version in entity_versions.items():
                self.repository.delete(entity_id, expected_version=expected_version, connection=connection)
