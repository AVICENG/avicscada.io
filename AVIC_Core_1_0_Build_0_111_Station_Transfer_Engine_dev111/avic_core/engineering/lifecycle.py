"""Persistent project lifecycle workflow for AVIC Core.

This service manages engineering stage records and their transactional history.
It does not execute control commands, commission devices, or provide a UI.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from uuid import uuid4

from avic_core.contracts.engineering import LifecycleRecord, LifecycleStage, WorkStatus


class LifecycleError(RuntimeError):
    """Base class for lifecycle workflow errors."""


class LifecycleNotFound(LifecycleError):
    pass


class LifecycleConflict(LifecycleError):
    pass


class LifecycleTransitionError(LifecycleError):
    pass


@dataclass(frozen=True, slots=True)
class VersionedLifecycleRecord:
    record: LifecycleRecord
    version: int


@dataclass(frozen=True, slots=True)
class LifecycleEvent:
    event_id: str
    project_ref: str
    stage: LifecycleStage
    actor: str
    action: str
    from_status: WorkStatus | None
    to_status: WorkStatus
    occurred_at: datetime
    details: dict[str, object]


_ALLOWED_TRANSITIONS: dict[WorkStatus, frozenset[WorkStatus]] = {
    WorkStatus.NOT_STARTED: frozenset({WorkStatus.IN_PROGRESS, WorkStatus.CANCELLED}),
    WorkStatus.IN_PROGRESS: frozenset({WorkStatus.BLOCKED, WorkStatus.IN_REVIEW, WorkStatus.CANCELLED}),
    WorkStatus.BLOCKED: frozenset({WorkStatus.IN_PROGRESS, WorkStatus.CANCELLED}),
    WorkStatus.IN_REVIEW: frozenset({WorkStatus.IN_PROGRESS, WorkStatus.BLOCKED, WorkStatus.DONE}),
    WorkStatus.DONE: frozenset(),
    WorkStatus.CANCELLED: frozenset(),
}

# Stages that may proceed in parallel after the point model is approved.
_PREREQUISITES: dict[LifecycleStage, tuple[LifecycleStage, ...]] = {
    LifecycleStage.DESIGN: (),
    LifecycleStage.DOCUMENT_REVIEW: (LifecycleStage.DESIGN,),
    LifecycleStage.EQUIPMENT_MODEL: (LifecycleStage.DOCUMENT_REVIEW,),
    LifecycleStage.POINT_MODEL: (LifecycleStage.EQUIPMENT_MODEL,),
    LifecycleStage.LOGIC: (LifecycleStage.POINT_MODEL,),
    LifecycleStage.GRAPHICS: (LifecycleStage.POINT_MODEL,),
    LifecycleStage.CONTROLLER_INTEGRATION: (LifecycleStage.LOGIC, LifecycleStage.GRAPHICS),
    LifecycleStage.COMMISSIONING: (LifecycleStage.CONTROLLER_INTEGRATION,),
    LifecycleStage.TESTING: (LifecycleStage.COMMISSIONING,),
    LifecycleStage.HANDOVER: (LifecycleStage.TESTING,),
    LifecycleStage.OPERATIONS: (LifecycleStage.HANDOVER,),
    LifecycleStage.MAINTENANCE: (LifecycleStage.OPERATIONS,),
    LifecycleStage.MODERNIZATION: (LifecycleStage.OPERATIONS,),
    LifecycleStage.ARCHIVED: (LifecycleStage.OPERATIONS,),
}


def _record_from_row(row: sqlite3.Row) -> VersionedLifecycleRecord:
    record = LifecycleRecord(
        project_ref=row["project_ref"],
        stage=LifecycleStage(row["stage"]),
        status=WorkStatus(row["status"]),
        updated_by=row["updated_by"],
        updated_at=datetime.fromisoformat(row["updated_at"]),
        assignee=row["assignee"],
        document_refs=tuple(json.loads(row["document_refs_json"])),
        issue_refs=tuple(json.loads(row["issue_refs_json"])),
        notes=row["notes"],
        record_id=row["record_id"],
    )
    return VersionedLifecycleRecord(record, int(row["version"]))


class EngineeringLifecycleService:
    """SQLite-backed workflow for project stages with optimistic concurrency.

    Every state/metadata change and its immutable event are committed in one
    SQLite transaction. Audit events here are workflow history, not a replacement
    for the platform-wide security audit chain.
    """

    def __init__(self, database: str | Path):
        self.database = str(database)
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS lifecycle_records (
                record_id TEXT PRIMARY KEY,
                project_ref TEXT NOT NULL,
                stage TEXT NOT NULL,
                status TEXT NOT NULL,
                updated_by TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                assignee TEXT,
                document_refs_json TEXT NOT NULL,
                issue_refs_json TEXT NOT NULL,
                notes TEXT NOT NULL,
                version INTEGER NOT NULL,
                UNIQUE(project_ref, stage)
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_lifecycle_project ON lifecycle_records(project_ref)")
            db.execute("""CREATE TABLE IF NOT EXISTS lifecycle_events (
                event_id TEXT PRIMARY KEY,
                project_ref TEXT NOT NULL,
                stage TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                from_status TEXT,
                to_status TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                details_json TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_lifecycle_events_project ON lifecycle_events(project_ref, occurred_at)")
            db.commit()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @staticmethod
    def _append_event(db: sqlite3.Connection, *, project_ref: str, stage: LifecycleStage,
                      actor: str, action: str, old: WorkStatus | None, new: WorkStatus,
                      occurred_at: datetime, details: dict[str, object] | None = None) -> None:
        db.execute(
            "INSERT INTO lifecycle_events VALUES(?,?,?,?,?,?,?,?,?)",
            (str(uuid4()), project_ref, stage.value, actor, action,
             old.value if old else None, new.value, occurred_at.isoformat(),
             json.dumps(details or {}, ensure_ascii=False, sort_keys=True)),
        )

    def initialize_project(self, project_ref: str, *, created_by: str,
                           at: datetime | None = None) -> tuple[VersionedLifecycleRecord, ...]:
        if not isinstance(project_ref, str) or not project_ref.strip():
            raise ValueError("project_ref is required")
        if not isinstance(created_by, str) or not created_by.strip():
            raise ValueError("created_by is required")
        occurred = at or datetime.now(timezone.utc)
        if occurred.tzinfo is None or occurred.utcoffset() is None:
            raise ValueError("at must be timezone-aware")
        created: list[VersionedLifecycleRecord] = []
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                existing = db.execute("SELECT 1 FROM lifecycle_records WHERE project_ref=? LIMIT 1", (project_ref,)).fetchone()
                if existing:
                    raise LifecycleConflict(f"Lifecycle already initialized for project {project_ref}")
                for stage in LifecycleStage:
                    record_id = str(uuid4())
                    db.execute(
                        """INSERT INTO lifecycle_records VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                        (record_id, project_ref, stage.value, WorkStatus.NOT_STARTED.value,
                         created_by, occurred.isoformat(), None, "[]", "[]", "", 1),
                    )
                    self._append_event(db, project_ref=project_ref, stage=stage, actor=created_by,
                                       action="stage.initialized", old=None, new=WorkStatus.NOT_STARTED,
                                       occurred_at=occurred)
                    row = db.execute("SELECT * FROM lifecycle_records WHERE record_id=?", (record_id,)).fetchone()
                    created.append(_record_from_row(row))
                db.commit()
            except Exception:
                db.rollback()
                raise
        return tuple(created)

    def get_stage(self, project_ref: str, stage: LifecycleStage) -> VersionedLifecycleRecord:
        with closing(self._connect()) as db:
            row = db.execute("SELECT * FROM lifecycle_records WHERE project_ref=? AND stage=?",
                             (project_ref, stage.value)).fetchone()
        if row is None:
            raise LifecycleNotFound(f"No lifecycle stage {stage.value} for project {project_ref}")
        return _record_from_row(row)

    def list_project(self, project_ref: str) -> tuple[VersionedLifecycleRecord, ...]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM lifecycle_records WHERE project_ref=?", (project_ref,)).fetchall()
        if not rows:
            raise LifecycleNotFound(f"No lifecycle records for project {project_ref}")
        by_stage = {row["stage"]: _record_from_row(row) for row in rows}
        return tuple(by_stage[stage.value] for stage in LifecycleStage if stage.value in by_stage)

    def update_stage(self, project_ref: str, stage: LifecycleStage, status: WorkStatus, *,
                     updated_by: str, expected_version: int, assignee: str | None = None,
                     document_refs: Iterable[str] | None = None,
                     issue_refs: Iterable[str] | None = None, notes: str | None = None,
                     at: datetime | None = None) -> VersionedLifecycleRecord:
        if not isinstance(project_ref, str) or not project_ref.strip():
            raise ValueError("project_ref is required")
        if not isinstance(stage, LifecycleStage):
            raise ValueError("stage must be a LifecycleStage")
        if not isinstance(status, WorkStatus):
            raise ValueError("status must be a WorkStatus")
        if not isinstance(updated_by, str) or not updated_by.strip():
            raise ValueError("updated_by is required")
        if expected_version < 1:
            raise ValueError("expected_version must be >= 1")
        occurred = at or datetime.now(timezone.utc)
        if occurred.tzinfo is None or occurred.utcoffset() is None:
            raise ValueError("at must be timezone-aware")
        docs = tuple(document_refs) if document_refs is not None else None
        issues = tuple(issue_refs) if issue_refs is not None else None
        if docs is not None and any(not isinstance(item, str) or not item.strip() for item in docs):
            raise ValueError("document_refs must contain non-empty strings")
        if issues is not None and any(not isinstance(item, str) or not item.strip() for item in issues):
            raise ValueError("issue_refs must contain non-empty strings")

        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute("SELECT * FROM lifecycle_records WHERE project_ref=? AND stage=?",
                                 (project_ref, stage.value)).fetchone()
                if row is None:
                    raise LifecycleNotFound(f"No lifecycle stage {stage.value} for project {project_ref}")
                current = _record_from_row(row)
                if current.version != expected_version:
                    raise LifecycleConflict(
                        f"Version conflict for {project_ref}/{stage.value}: current={current.version}, expected={expected_version}"
                    )
                old_status = current.record.status
                if status != old_status and status not in _ALLOWED_TRANSITIONS[old_status]:
                    raise LifecycleTransitionError(f"Transition {old_status.value} -> {status.value} is not allowed")
                if status is WorkStatus.IN_PROGRESS and old_status is not WorkStatus.IN_PROGRESS:
                    for prerequisite in _PREREQUISITES[stage]:
                        prereq = db.execute(
                            "SELECT status FROM lifecycle_records WHERE project_ref=? AND stage=?",
                            (project_ref, prerequisite.value),
                        ).fetchone()
                        if prereq is None or prereq["status"] != WorkStatus.DONE.value:
                            raise LifecycleTransitionError(
                                f"Stage {stage.value} requires {prerequisite.value}=DONE"
                            )
                if stage is LifecycleStage.ARCHIVED and status is WorkStatus.IN_PROGRESS:
                    active = db.execute(
                        """SELECT stage,status FROM lifecycle_records WHERE project_ref=?
                           AND stage<>? AND status IN (?,?,?)""",
                        (project_ref, LifecycleStage.ARCHIVED.value, WorkStatus.IN_PROGRESS.value,
                         WorkStatus.BLOCKED.value, WorkStatus.IN_REVIEW.value),
                    ).fetchall()
                    if active:
                        raise LifecycleTransitionError("Project cannot be archived while any stage is active or blocked")
                next_docs = docs if docs is not None else current.record.document_refs
                next_issues = issues if issues is not None else current.record.issue_refs
                next_assignee = assignee if assignee is not None else current.record.assignee
                next_notes = notes if notes is not None else current.record.notes
                next_version = current.version + 1
                cursor = db.execute(
                    """UPDATE lifecycle_records SET status=?,updated_by=?,updated_at=?,assignee=?,
                       document_refs_json=?,issue_refs_json=?,notes=?,version=?
                       WHERE record_id=? AND version=?""",
                    (status.value, updated_by, occurred.isoformat(), next_assignee,
                     json.dumps(next_docs, ensure_ascii=False), json.dumps(next_issues, ensure_ascii=False),
                     next_notes, next_version, current.record.record_id, expected_version),
                )
                if cursor.rowcount != 1:
                    raise LifecycleConflict("Lifecycle record changed concurrently")
                self._append_event(db, project_ref=project_ref, stage=stage, actor=updated_by,
                                   action="stage.updated", old=old_status, new=status, occurred_at=occurred,
                                   details={"version": next_version, "assignee": next_assignee,
                                            "document_refs": list(next_docs), "issue_refs": list(next_issues),
                                            "notes": next_notes})
                saved = db.execute("SELECT * FROM lifecycle_records WHERE record_id=?",
                                   (current.record.record_id,)).fetchone()
                db.commit()
                return _record_from_row(saved)
            except Exception:
                db.rollback()
                raise

    def history(self, project_ref: str) -> tuple[LifecycleEvent, ...]:
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT * FROM lifecycle_events WHERE project_ref=? ORDER BY rowid", (project_ref,)
            ).fetchall()
        if not rows:
            raise LifecycleNotFound(f"No lifecycle history for project {project_ref}")
        return tuple(LifecycleEvent(
            event_id=row["event_id"], project_ref=row["project_ref"], stage=LifecycleStage(row["stage"]),
            actor=row["actor"], action=row["action"],
            from_status=WorkStatus(row["from_status"]) if row["from_status"] else None,
            to_status=WorkStatus(row["to_status"]), occurred_at=datetime.fromisoformat(row["occurred_at"]),
            details=json.loads(row["details_json"]),
        ) for row in rows)
