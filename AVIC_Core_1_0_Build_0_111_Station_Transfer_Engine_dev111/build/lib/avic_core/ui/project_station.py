from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from avic_core.domain.models import Project, Station
from avic_core.repository.sqlite_repository import ConcurrencyConflict, EntityNotFound


class ProjectStationService:
    """Persistent Project/Station operations over the existing Core SQLite repository."""
    def __init__(self, core):
        self.core = core

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        payload = record["payload"]
        return {
            "id": record["entity_id"], "type": record["entity_type"],
            "name": record["name"], "description": payload.get("description", ""),
            "archived": bool(payload.get("archived", False)),
            "version": int(record["version"]),
            "created_at": record["created_at"], "updated_at": record["updated_at"],
            "project_id": payload.get("project_id"),
        }

    def tree(self, *, include_archived: bool = False) -> dict[str, list[dict[str, Any]]]:
        projects = [self._public(r) for r in self.core.repository.list_records(entity_type="Project")]
        stations = [self._public(r) for r in self.core.repository.list_records(entity_type="Station")]
        if not include_archived:
            projects = [x for x in projects if not x["archived"]]
            stations = [x for x in stations if not x["archived"]]
        project_ids = {x["id"] for x in projects}
        stations = [x for x in stations if x["project_id"] in project_ids]
        return {"projects": projects, "stations": stations}

    def create_project(self, name: str, description: str = "", actor: str = "local-engineer") -> dict:
        entity = Project(name=name.strip(), description=description.strip())
        version = self.core.repository.save(entity)
        self.core.audit.append(actor_id=actor, action="project.created", resource_type="project",
                              resource_id=entity.id, details={"name": entity.name, "version": version})
        return self._public(self.core.repository.get_record(entity.id))

    def create_station(self, project_id: str, name: str, description: str = "", actor: str = "local-engineer") -> dict:
        project_record = self.core.repository.get_record(project_id)
        if project_record["entity_type"] != "Project":
            raise ValueError("Родительский объект не является проектом")
        if project_record["payload"].get("archived", False):
            raise ValueError("Нельзя создавать станцию в архивном проекте")
        entity = Station(name=name.strip(), description=description.strip(), project_id=project_id)
        version = self.core.repository.save(entity)
        self.core.audit.append(actor_id=actor, action="station.created", resource_type="station",
                              resource_id=entity.id, details={"project_id": project_id, "name": entity.name, "version": version})
        return self._public(self.core.repository.get_record(entity.id))

    def update(self, entity_id: str, *, expected_version: int, name: str | None = None,
               description: str | None = None, archived: bool | None = None,
               actor: str = "local-engineer") -> dict:
        record = self.core.repository.get_record(entity_id)
        if record["entity_type"] not in {"Project", "Station"}:
            raise ValueError("Допускается изменение только Project или Station")
        model = Project if record["entity_type"] == "Project" else Station
        entity, version = self.core.repository.get(entity_id, model)
        if version != expected_version:
            raise ConcurrencyConflict(f"Версия объекта {version}; ожидалась {expected_version}")
        if name is not None:
            if not name.strip():
                raise ValueError("Название не может быть пустым")
            entity.name = name.strip()
        if description is not None:
            entity.description = description.strip()
        if archived is not None:
            entity.archived = bool(archived)
        entity.updated_at = datetime.now(timezone.utc)
        new_version = self.core.repository.save(entity, expected_version=expected_version)
        action = "archived" if archived is True else "restored" if archived is False else "updated"
        self.core.audit.append(actor_id=actor, action=f"{record['entity_type'].lower()}.{action}",
                              resource_type=record["entity_type"].lower(), resource_id=entity_id,
                              details={"version": new_version, "name": entity.name, "archived": entity.archived})
        return self._public(self.core.repository.get_record(entity_id))
    def _delete_scope(self, entity_id: str) -> tuple[dict[str, Any], set[str], list[dict[str, Any]]]:
        """Resolve the complete AVIC-owned dependency scope without touching field controllers."""
        target = self.core.repository.get_record(entity_id)
        kind = target["entity_type"]
        if kind == "Station":
            station_ids = {entity_id}
            project_ids: set[str] = set()
        elif kind == "Project":
            project_ids = {entity_id}
            station_ids = {r["entity_id"] for r in self.core.repository.list_records(entity_type="Station")
                           if r["payload"].get("project_id") == entity_id}
        else:
            raise ValueError("Удалять через эту операцию можно только проект или станцию")
        records = self.core.repository.list_records()
        selected = {entity_id}
        selected.update(station_ids)
        # Include records explicitly scoped to the project/stations.
        for row in records:
            payload = row.get("payload", {})
            if row.get("project_id") in project_ids or row.get("station_id") in station_ids or payload.get("project_id") in project_ids or payload.get("station_id") in station_ids:
                selected.add(row["entity_id"])
        # Resolve reference-only children (notably Points -> Device, plus graphics/layout references).
        changed = True
        while changed:
            changed = False
            for row in records:
                rid = row["entity_id"]
                if rid in selected:
                    continue
                payload = row.get("payload", {})
                refs = {str(v) for v in payload.values() if isinstance(v, str)}
                refs.update(str(v) for v in payload.get("graphic_ids", []) if isinstance(v, str))
                if refs.intersection(selected):
                    selected.add(rid); changed = True
        chosen = [r for r in records if r["entity_id"] in selected]
        # Delete leaf/reference objects first; project/station containers last.
        chosen.sort(key=lambda r: (r["entity_type"] in {"Project", "Station"}, r["entity_type"], r["entity_id"]))
        return target, selected, chosen

    def delete_preview(self, entity_id: str) -> dict[str, Any]:
        target, selected, chosen = self._delete_scope(entity_id)
        counts: dict[str, int] = {}
        for row in chosen:
            counts[row["entity_type"]] = counts.get(row["entity_type"], 0) + 1
        return {"id": entity_id, "type": target["entity_type"], "name": target["name"],
                "total_objects": len(chosen), "counts": counts,
                "requires_cascade": len(chosen) > 1,
                "warning": "Будут удалены только конфигурационные данные AVIC. Физические контроллеры и оборудование не изменяются."}

    def delete(self, entity_id: str, *, cascade: bool = False, actor: str = "local-engineer") -> dict[str, Any]:
        target, selected, chosen = self._delete_scope(entity_id)
        if len(chosen) > 1 and not cascade:
            raise ValueError("У объекта есть дочерние или связанные записи. Сначала запросите delete-preview и подтвердите cascade=true")
        with self.core.repository.transaction() as conn:
            for row in chosen:
                self.core.repository.delete(row["entity_id"], expected_version=int(row["version"]), connection=conn)
        self.core.audit.append(actor_id=actor, action=f"{target['entity_type'].lower()}.deleted",
            resource_type=target["entity_type"].lower(), resource_id=entity_id,
            details={"deleted_objects": len(chosen), "cascade": bool(cascade),
                     "deleted_types": {k: sum(1 for r in chosen if r["entity_type"] == k) for k in sorted({r["entity_type"] for r in chosen})}})
        return {"deleted": True, "id": entity_id, "type": target["entity_type"],
                "deleted_objects": len(chosen), "field_equipment_unchanged": True}

