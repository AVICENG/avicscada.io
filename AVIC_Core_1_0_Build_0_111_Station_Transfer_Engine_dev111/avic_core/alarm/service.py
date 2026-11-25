from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Callable
from uuid import uuid4


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AlarmState(str, Enum):
    NORMAL = "NORMAL"
    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RETURNED_TO_NORMAL = "RETURNED_TO_NORMAL"


class AlarmCategory(str, Enum):
    PROCESS = "PROCESS"
    EQUIPMENT = "EQUIPMENT"
    COMMUNICATION = "COMMUNICATION"
    SYSTEM = "SYSTEM"
    SECURITY = "SECURITY"
    CUSTOM = "CUSTOM"


class AlarmPriority(int, Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    INFORMATION = 5


@dataclass(frozen=True)
class AlarmRecord:
    alarm_id: str
    station_id: str
    source_id: str
    alarm_key: str
    name: str
    message: str
    category: str
    priority: int
    state: AlarmState
    active_since: str | None
    acknowledged_by: str | None
    acknowledged_at: str | None
    returned_at: str | None
    occurrence_count: int
    metadata: dict


@dataclass(frozen=True)
class AlarmEvent:
    event_id: str
    alarm_id: str
    station_id: str
    event_type: str
    occurred_at: str
    actor_id: str | None
    from_state: str
    to_state: str
    message: str
    details: dict


class AlarmService:
    """Persistent alarm state machine with an append-only transition journal.

    Lower numeric priority is more severe. `alarm_key` is stable per source/station.
    State changes commit before optional event callbacks are invoked.
    """
    def __init__(self, database_path: str | Path, *, audit_service=None,
                 event_publisher: Callable[[AlarmEvent], None] | None = None):
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.audit_service = audit_service
        self.event_publisher = event_publisher
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
            CREATE TABLE IF NOT EXISTS alarms (
                alarm_id TEXT PRIMARY KEY,
                station_id TEXT NOT NULL,
                source_id TEXT NOT NULL,
                alarm_key TEXT NOT NULL,
                name TEXT NOT NULL,
                message TEXT NOT NULL,
                category TEXT NOT NULL,
                priority INTEGER NOT NULL CHECK(priority BETWEEN 1 AND 5),
                state TEXT NOT NULL,
                active_since TEXT,
                acknowledged_by TEXT,
                acknowledged_at TEXT,
                returned_at TEXT,
                occurrence_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(station_id, source_id, alarm_key)
            );
            CREATE INDEX IF NOT EXISTS idx_alarms_station_state_priority
                ON alarms(station_id, state, priority);
            CREATE INDEX IF NOT EXISTS idx_alarms_active_since ON alarms(active_since);
            CREATE TABLE IF NOT EXISTS alarm_events (
                event_id TEXT PRIMARY KEY,
                alarm_id TEXT NOT NULL REFERENCES alarms(alarm_id),
                station_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                actor_id TEXT,
                from_state TEXT NOT NULL,
                to_state TEXT NOT NULL,
                message TEXT NOT NULL,
                details_json TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_alarm_events_alarm_time
                ON alarm_events(alarm_id, occurred_at);
            CREATE INDEX IF NOT EXISTS idx_alarm_events_station_time
                ON alarm_events(station_id, occurred_at);
            CREATE TABLE IF NOT EXISTS alarm_outbox (
                event_id TEXT PRIMARY KEY REFERENCES alarm_events(event_id),
                payload_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'PENDING' CHECK(status IN ('PENDING','IN_FLIGHT','DELIVERED')),
                lease_until REAL,
                attempts INTEGER NOT NULL DEFAULT 0,
                next_attempt_at REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                delivered_at TEXT,
                last_error TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_alarm_outbox_pending
                ON alarm_outbox(status, next_attempt_at, created_at);
            CREATE TABLE IF NOT EXISTS alarm_notes (
                note_id TEXT PRIMARY KEY,
                alarm_id TEXT NOT NULL REFERENCES alarms(alarm_id),
                station_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_alarm_notes_alarm_time
                ON alarm_notes(alarm_id, created_at);
            """)

    def _db(self):
        return sqlite3.connect(self.path, timeout=15)

    @staticmethod
    def _record(row) -> AlarmRecord:
        return AlarmRecord(
            row["alarm_id"], row["station_id"], row["source_id"], row["alarm_key"],
            row["name"], row["message"], row["category"], row["priority"],
            AlarmState(row["state"]), row["active_since"], row["acknowledged_by"],
            row["acknowledged_at"], row["returned_at"], row["occurrence_count"],
            json.loads(row["metadata_json"]),
        )

    @staticmethod
    def _event(row) -> AlarmEvent:
        return AlarmEvent(row["event_id"], row["alarm_id"], row["station_id"],
                          row["event_type"], row["occurred_at"], row["actor_id"],
                          row["from_state"], row["to_state"], row["message"],
                          json.loads(row["details_json"]))

    def _emit(self, event: AlarmEvent) -> None:
        if self.audit_service is not None:
            self.audit_service.append(
                actor_id=event.actor_id or "system", action=f"alarm.{event.event_type.lower()}",
                resource_type="alarm", resource_id=event.alarm_id,
                outcome="success", details={"station_id": event.station_id,
                                            "from_state": event.from_state,
                                            "to_state": event.to_state,
                                            "message": event.message},
            )
        if self.event_publisher is not None:
            # Delivery is attempted from the durable outbox. Failures remain pending.
            self.dispatch_outbox(limit=100)

    def _append_event(self, db, *, alarm_id: str, station_id: str, event_type: str,
                      actor_id: str | None, from_state: AlarmState, to_state: AlarmState,
                      message: str, details: dict | None = None) -> AlarmEvent:
        event = AlarmEvent(str(uuid4()), alarm_id, station_id, event_type, _now(),
                           actor_id, from_state.value, to_state.value, message, details or {})
        details_json = json.dumps(event.details, ensure_ascii=False, sort_keys=True)
        db.execute("""INSERT INTO alarm_events
            (event_id,alarm_id,station_id,event_type,occurred_at,actor_id,from_state,to_state,message,details_json)
            VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (event.event_id, event.alarm_id, event.station_id, event.event_type,
             event.occurred_at, event.actor_id, event.from_state, event.to_state,
             event.message, details_json))
        payload = {"event_id": event.event_id, "alarm_id": event.alarm_id,
                   "station_id": event.station_id, "event_type": event.event_type,
                   "occurred_at": event.occurred_at, "actor_id": event.actor_id,
                   "from_state": event.from_state, "to_state": event.to_state,
                   "message": event.message, "details": event.details}
        db.execute("INSERT INTO alarm_outbox(event_id,payload_json,created_at) VALUES(?,?,?)",
                   (event.event_id, json.dumps(payload, ensure_ascii=False, sort_keys=True), event.occurred_at))
        return event

    def raise_alarm(self, *, station_id: str, source_id: str, alarm_key: str,
                    name: str, message: str, category: AlarmCategory | str = AlarmCategory.CUSTOM,
                    priority: AlarmPriority | int = AlarmPriority.MEDIUM,
                    metadata: dict | None = None) -> AlarmRecord:
        for field, value in (("station_id", station_id), ("source_id", source_id),
                             ("alarm_key", alarm_key), ("name", name), ("message", message)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} не может быть пустым")
        cat = category.value if isinstance(category, AlarmCategory) else str(category)
        if cat not in {x.value for x in AlarmCategory}:
            raise ValueError("Неизвестная категория аварии")
        prio = int(priority)
        if prio not in {x.value for x in AlarmPriority}:
            raise ValueError("Приоритет должен быть от 1 (критический) до 5 (информационный)")
        meta = metadata or {}
        if not isinstance(meta, dict):
            raise ValueError("metadata должен быть объектом")
        now = _now()
        event = None
        with self._db() as raw:
            raw.row_factory = sqlite3.Row
            db = raw
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT * FROM alarms
                WHERE station_id=? AND source_id=? AND alarm_key=?""",
                (station_id, source_id, alarm_key)).fetchone()
            if row is None:
                alarm_id = str(uuid4())
                db.execute("""INSERT INTO alarms
                    (alarm_id,station_id,source_id,alarm_key,name,message,category,priority,state,
                     active_since,occurrence_count,metadata_json,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (alarm_id, station_id, source_id, alarm_key, name, message, cat, prio,
                     AlarmState.ACTIVE.value, now, 1, json.dumps(meta, ensure_ascii=False, sort_keys=True),
                     now, now))
                event = self._append_event(db, alarm_id=alarm_id, station_id=station_id,
                    event_type="RAISED", actor_id=None, from_state=AlarmState.NORMAL,
                    to_state=AlarmState.ACTIVE, message=message, details=meta)
            elif row["state"] in (AlarmState.ACTIVE.value, AlarmState.ACKNOWLEDGED.value):
                alarm_id = row["alarm_id"]
                # Duplicate active input updates presentation details but does not create a new occurrence.
                db.execute("""UPDATE alarms SET name=?,message=?,category=?,priority=?,metadata_json=?,updated_at=?
                    WHERE alarm_id=?""",
                    (name, message, cat, prio, json.dumps(meta, ensure_ascii=False, sort_keys=True),
                     now, alarm_id))
            else:
                alarm_id = row["alarm_id"]
                previous = AlarmState(row["state"])
                db.execute("""UPDATE alarms SET name=?,message=?,category=?,priority=?,state=?,
                    active_since=?,acknowledged_by=NULL,acknowledged_at=NULL,returned_at=NULL,
                    occurrence_count=occurrence_count+1,metadata_json=?,updated_at=? WHERE alarm_id=?""",
                    (name, message, cat, prio, AlarmState.ACTIVE.value, now,
                     json.dumps(meta, ensure_ascii=False, sort_keys=True), now, alarm_id))
                event = self._append_event(db, alarm_id=alarm_id, station_id=station_id,
                    event_type="RAISED", actor_id=None, from_state=previous,
                    to_state=AlarmState.ACTIVE, message=message,
                    details={"new_occurrence": True, **meta})
            row = db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone()
            result = self._record(row)
        if event:
            self._emit(event)
        return result

    def acknowledge(self, alarm_id: str, *, actor_id: str, comment: str = "") -> AlarmRecord:
        if not actor_id or not actor_id.strip():
            raise ValueError("actor_id обязателен")
        event = None
        with self._db() as raw:
            raw.row_factory = sqlite3.Row
            db = raw
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone()
            if row is None:
                raise KeyError(alarm_id)
            old = AlarmState(row["state"])
            if old == AlarmState.ACTIVE:
                new = AlarmState.ACKNOWLEDGED
            elif old == AlarmState.RETURNED_TO_NORMAL:
                new = AlarmState.NORMAL
            elif old in (AlarmState.ACKNOWLEDGED, AlarmState.NORMAL):
                return self._record(row)
            else:
                raise RuntimeError(f"Нельзя подтвердить тревогу в состоянии {old.value}")
            now = _now()
            db.execute("""UPDATE alarms SET state=?,acknowledged_by=?,acknowledged_at=?,updated_at=?
                WHERE alarm_id=?""", (new.value, actor_id, now, now, alarm_id))
            event = self._append_event(db, alarm_id=alarm_id, station_id=row["station_id"],
                event_type="ACKNOWLEDGED", actor_id=actor_id, from_state=old, to_state=new,
                message=comment or "Авария подтверждена", details={"comment": comment})
            result = self._record(db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone())
        self._emit(event)
        return result

    def return_to_normal(self, alarm_id: str, *, message: str = "Условие аварии нормализовано",
                         details: dict | None = None) -> AlarmRecord:
        event = None
        with self._db() as raw:
            raw.row_factory = sqlite3.Row
            db = raw
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone()
            if row is None:
                raise KeyError(alarm_id)
            old = AlarmState(row["state"])
            if old in (AlarmState.NORMAL, AlarmState.RETURNED_TO_NORMAL):
                return self._record(row)
            new = AlarmState.NORMAL if old == AlarmState.ACKNOWLEDGED else AlarmState.RETURNED_TO_NORMAL
            now = _now()
            db.execute("UPDATE alarms SET state=?,returned_at=?,updated_at=? WHERE alarm_id=?",
                       (new.value, now, now, alarm_id))
            event = self._append_event(db, alarm_id=alarm_id, station_id=row["station_id"],
                event_type="RETURNED_TO_NORMAL", actor_id=None, from_state=old, to_state=new,
                message=message, details=details or {})
            result = self._record(db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone())
        self._emit(event)
        return result

    def get_alarm_by_key(self, station_id: str, source_id: str, alarm_key: str) -> AlarmRecord:
        with self._db() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM alarms WHERE station_id=? AND source_id=? AND alarm_key=?",
                             (station_id, source_id, alarm_key)).fetchone()
        if row is None:
            raise KeyError((station_id, source_id, alarm_key))
        return self._record(row)

    def get_alarm(self, alarm_id: str) -> AlarmRecord:
        with self._db() as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone()
        if row is None:
            raise KeyError(alarm_id)
        return self._record(row)

    def list_alarms(self, *, station_id: str | None = None,
                    states: list[AlarmState | str] | None = None,
                    priorities: list[int] | None = None,
                    categories: list[AlarmCategory | str] | None = None,
                    source_id: str | None = None, search: str | None = None,
                    limit: int = 200, offset: int = 0) -> list[AlarmRecord]:
        if not 1 <= limit <= 1000 or offset < 0:
            raise ValueError("limit должен быть 1–1000, offset неотрицательный")
        clauses, args = [], []
        if station_id:
            clauses.append("station_id=?"); args.append(station_id)
        if source_id:
            clauses.append("source_id=?"); args.append(source_id)
        if states:
            vals = [x.value if isinstance(x, AlarmState) else str(x) for x in states]
            clauses.append("state IN (" + ",".join("?" for _ in vals) + ")"); args.extend(vals)
        if priorities:
            if any(int(x) not in range(1, 6) for x in priorities):
                raise ValueError("Приоритеты должны быть от 1 до 5")
            clauses.append("priority IN (" + ",".join("?" for _ in priorities) + ")")
            args.extend(int(x) for x in priorities)
        if categories:
            vals = [x.value if isinstance(x, AlarmCategory) else str(x) for x in categories]
            clauses.append("category IN (" + ",".join("?" for _ in vals) + ")"); args.extend(vals)
        if search:
            clauses.append("(name LIKE ? OR message LIKE ? OR alarm_key LIKE ?)")
            pattern = f"%{search}%"; args.extend([pattern, pattern, pattern])
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._db() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM alarms" + where +
                              " ORDER BY state IN ('ACTIVE','ACKNOWLEDGED','RETURNED_TO_NORMAL') DESC,"
                              "priority ASC, active_since DESC LIMIT ? OFFSET ?",
                              (*args, limit, offset)).fetchall()
        return [self._record(row) for row in rows]

    def history(self, *, alarm_id: str | None = None, station_id: str | None = None,
                event_types: list[str] | None = None, limit: int = 500,
                offset: int = 0) -> list[AlarmEvent]:
        if not 1 <= limit <= 2000 or offset < 0:
            raise ValueError("limit должен быть 1–2000, offset неотрицательный")
        clauses, args = [], []
        if alarm_id:
            clauses.append("alarm_id=?"); args.append(alarm_id)
        if station_id:
            clauses.append("station_id=?"); args.append(station_id)
        if event_types:
            clauses.append("event_type IN (" + ",".join("?" for _ in event_types) + ")")
            args.extend(event_types)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._db() as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM alarm_events" + where +
                              " ORDER BY occurred_at DESC LIMIT ? OFFSET ?",
                              (*args, limit, offset)).fetchall()
        return [self._event(row) for row in rows]

    def add_note(self, alarm_id: str, *, actor_id: str, note: str) -> dict:
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id обязателен")
        if not isinstance(note, str) or not note.strip() or len(note) > 4000:
            raise ValueError("Примечание должно содержать от 1 до 4000 символов")
        note_id = str(uuid4())
        created_at = _now()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            alarm = db.execute("SELECT station_id FROM alarms WHERE alarm_id=?", (alarm_id,)).fetchone()
            if alarm is None:
                raise KeyError(alarm_id)
            db.execute("INSERT INTO alarm_notes(note_id,alarm_id,station_id,actor_id,note,created_at) VALUES(?,?,?,?,?,?)",
                       (note_id, alarm_id, alarm[0], actor_id.strip(), note.strip(), created_at))
        if self.audit_service is not None:
            self.audit_service.append(actor_id=actor_id.strip(), action="alarm.note.added",
                resource_type="alarm", resource_id=alarm_id, outcome="success",
                details={"note_id": note_id, "station_id": alarm[0]})
        return {"note_id": note_id, "alarm_id": alarm_id, "station_id": alarm[0],
                "actor_id": actor_id.strip(), "note": note.strip(), "created_at": created_at}

    def list_notes(self, alarm_id: str) -> list[dict]:
        self.get_alarm(alarm_id)
        with self._db() as db:
            rows = db.execute("SELECT note_id,alarm_id,station_id,actor_id,note,created_at FROM alarm_notes WHERE alarm_id=? ORDER BY created_at DESC",
                              (alarm_id,)).fetchall()
        keys = ("note_id", "alarm_id", "station_id", "actor_id", "note", "created_at")
        return [dict(zip(keys, row)) for row in rows]

    def dispatch_outbox(self, *, limit: int = 100, base_retry_seconds: float = 1.0,
                        max_retry_seconds: float = 300.0, force: bool = False) -> dict:
        """Deliver durable alarm events at-least-once; pending rows survive restart.

        Consumers should deduplicate by event_id because a process crash after consumer
        acceptance but before marking DELIVERED can cause a repeated delivery.
        """
        if self.event_publisher is None:
            return {"delivered": 0, "pending": self.outbox_pending_count()}
        if not 1 <= limit <= 1000 or base_retry_seconds <= 0 or max_retry_seconds < base_retry_seconds:
            raise ValueError("Некорректные параметры доставки outbox")
        delivered = 0
        import time
        now = time.time()
        # Claim rows atomically so concurrent dispatchers cannot both own one event.
        with self._db() as db:
            db.row_factory = sqlite3.Row
            db.execute("BEGIN IMMEDIATE")
            if force:
                db.execute("UPDATE alarm_outbox SET status='PENDING',lease_until=NULL WHERE status='IN_FLIGHT'")
            else:
                db.execute("UPDATE alarm_outbox SET status='PENDING',lease_until=NULL "
                           "WHERE status='IN_FLIGHT' AND lease_until<=?", (now,))
            due_clause = "" if force else " AND next_attempt_at<=?"
            params = (limit,) if force else (now, limit)
            rows = db.execute("SELECT event_id,payload_json,attempts FROM alarm_outbox "
                              "WHERE status='PENDING'" + due_clause +
                              " ORDER BY created_at LIMIT ?", params).fetchall()
            for row in rows:
                db.execute("UPDATE alarm_outbox SET status='IN_FLIGHT',lease_until=? "
                           "WHERE event_id=? AND status='PENDING'", (now + 30.0, row["event_id"]))
        for row in rows:
            try:
                payload = json.loads(row["payload_json"])
                self.event_publisher(AlarmEvent(
                    payload["event_id"], payload["alarm_id"], payload["station_id"],
                    payload["event_type"], payload["occurred_at"], payload["actor_id"],
                    payload["from_state"], payload["to_state"], payload["message"],
                    payload["details"]))
            except Exception as exc:
                attempts = int(row["attempts"]) + 1
                delay = min(max_retry_seconds, base_retry_seconds * (2 ** min(attempts - 1, 16)))
                with self._db() as db:
                    db.execute("UPDATE alarm_outbox SET status='PENDING',lease_until=NULL,attempts=?,"
                               "next_attempt_at=?,last_error=? WHERE event_id=? AND status='IN_FLIGHT'",
                               (attempts, time.time() + delay, str(exc)[:1000], row["event_id"]))
            else:
                with self._db() as db:
                    db.execute("UPDATE alarm_outbox SET status='DELIVERED',lease_until=NULL,attempts=attempts+1,"
                               "delivered_at=?,last_error=NULL WHERE event_id=? AND status='IN_FLIGHT'",
                               (_now(), row["event_id"]))
                delivered += 1
        return {"delivered": delivered, "pending": self.outbox_pending_count()}

    def outbox_pending_count(self) -> int:
        with self._db() as db:
            return int(db.execute("SELECT COUNT(*) FROM alarm_outbox WHERE status IN ('PENDING','IN_FLIGHT')").fetchone()[0])

    def active_count(self, *, station_id: str | None = None) -> int:
        where, args = "state IN ('ACTIVE','ACKNOWLEDGED')", []
        if station_id:
            where += " AND station_id=?"; args.append(station_id)
        with self._db() as db:
            return int(db.execute("SELECT COUNT(*) FROM alarms WHERE " + where, args).fetchone()[0])
