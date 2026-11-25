from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from avic_core.alarm.service import AlarmCategory, AlarmPriority, AlarmService


@dataclass(frozen=True)
class AlarmDefinition:
    definition_id: str
    station_id: str
    source_id: str
    alarm_key: str
    name: str
    message: str
    category: str = AlarmCategory.PROCESS.value
    priority: int = AlarmPriority.MEDIUM.value
    operator: str = ">"
    setpoint: float = 0.0
    hysteresis: float = 0.0
    on_delay: float = 0.0
    off_delay: float = 0.0
    latching: bool = False
    enabled: bool = True
    metadata: dict | None = None


class AlarmDefinitionManager:
    """Persistent alarm rules, deadband/delays, latching, shelving and suppression.

    `evaluate` is intended to be called by a station Runtime on value/quality updates.
    Time values are wall-clock seconds and pending transitions survive process restart.
    """
    OPERATORS = {">", ">=", "<", "<=", "==", "!="}

    def __init__(self, database_path: str | Path, alarm_service: AlarmService, *, audit_service=None):
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self.alarms = alarm_service
        self.audit_service = audit_service
        with self._db() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS alarm_definitions (
                definition_id TEXT PRIMARY KEY, station_id TEXT NOT NULL,
                source_id TEXT NOT NULL, alarm_key TEXT NOT NULL, definition_json TEXT NOT NULL,
                revision INTEGER NOT NULL DEFAULT 1, updated_at REAL NOT NULL,
                UNIQUE(station_id,source_id,alarm_key)
            );
            CREATE TABLE IF NOT EXISTS alarm_rule_state (
                definition_id TEXT PRIMARY KEY REFERENCES alarm_definitions(definition_id),
                condition_active INTEGER NOT NULL DEFAULT 0,
                pending_since REAL, latched INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS alarm_controls (
                definition_id TEXT PRIMARY KEY REFERENCES alarm_definitions(definition_id),
                shelved_until REAL, suppressed INTEGER NOT NULL DEFAULT 0,
                updated_at REAL NOT NULL
            );
            """)

    def _db(self):
        return sqlite3.connect(self.path, timeout=15)

    @classmethod
    def _validate(cls, d: AlarmDefinition):
        for field in ("station_id", "source_id", "alarm_key", "name", "message"):
            if not isinstance(getattr(d, field), str) or not getattr(d, field).strip():
                raise ValueError(f"{field} не может быть пустым")
        if d.operator not in cls.OPERATORS:
            raise ValueError("Неподдерживаемый оператор сравнения")
        for field in ("setpoint", "hysteresis", "on_delay", "off_delay"):
            value = getattr(d, field)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{field} должен быть числом")
        if d.hysteresis < 0 or d.on_delay < 0 or d.off_delay < 0:
            raise ValueError("hysteresis и задержки не могут быть отрицательными")
        if int(d.priority) not in range(1, 6):
            raise ValueError("priority должен быть от 1 до 5")
        if d.category not in {x.value for x in AlarmCategory}:
            raise ValueError("Неизвестная категория аварии")

    @staticmethod
    def _from_json(raw: str) -> AlarmDefinition:
        return AlarmDefinition(**json.loads(raw))

    def create(self, *, station_id: str, source_id: str, alarm_key: str,
               name: str, message: str, category: str = "PROCESS", priority: int = 3,
               operator: str = ">", setpoint: float = 0.0, hysteresis: float = 0.0,
               on_delay: float = 0.0, off_delay: float = 0.0, latching: bool = False,
               enabled: bool = True, metadata: dict | None = None) -> AlarmDefinition:
        d = AlarmDefinition(str(uuid4()), station_id, source_id, alarm_key, name, message,
                            category, int(priority), operator, float(setpoint), float(hysteresis),
                            float(on_delay), float(off_delay), bool(latching), bool(enabled), metadata or {})
        self._validate(d)
        now = time.time()
        with self._db() as db:
            try:
                db.execute("INSERT INTO alarm_definitions VALUES(?,?,?,?,?,1,?)",
                           (d.definition_id, d.station_id, d.source_id, d.alarm_key,
                            json.dumps(asdict(d), ensure_ascii=False, sort_keys=True), now))
                db.execute("INSERT INTO alarm_rule_state(definition_id,updated_at) VALUES(?,?)",
                           (d.definition_id, now))
                db.execute("INSERT INTO alarm_controls(definition_id,updated_at) VALUES(?,?)",
                           (d.definition_id, now))
            except sqlite3.IntegrityError as exc:
                raise ValueError("Определение с таким station/source/alarm_key уже существует") from exc
        return d

    def get(self, definition_id: str) -> AlarmDefinition:
        with self._db() as db:
            row = db.execute("SELECT definition_json FROM alarm_definitions WHERE definition_id=?",
                             (definition_id,)).fetchone()
        if row is None:
            raise KeyError(definition_id)
        return self._from_json(row[0])

    def list(self, *, station_id: str | None = None, enabled_only: bool = False) -> list[AlarmDefinition]:
        clauses, args = [], []
        if station_id:
            clauses.append("station_id=?"); args.append(station_id)
        if enabled_only:
            clauses.append("json_extract(definition_json,'$.enabled')=1")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self._db() as db:
            rows = db.execute("SELECT definition_json FROM alarm_definitions" + where +
                              " ORDER BY station_id,source_id,alarm_key", args).fetchall()
        return [self._from_json(x[0]) for x in rows]

    def update(self, definition_id: str, **changes: Any) -> AlarmDefinition:
        current = asdict(self.get(definition_id))
        allowed = set(current) - {"definition_id"}
        unknown = set(changes) - allowed
        if unknown:
            raise ValueError(f"Неизвестные поля: {', '.join(sorted(unknown))}")
        current.update(changes)
        d = AlarmDefinition(**current)
        self._validate(d)
        with self._db() as db:
            db.execute("UPDATE alarm_definitions SET definition_json=?,revision=revision+1,updated_at=? "
                       "WHERE definition_id=?", (json.dumps(asdict(d), ensure_ascii=False, sort_keys=True),
                       time.time(), definition_id))
        return d

    def _audit_control(self, actor_id: str, action: str, definition_id: str, details: dict):
        if not isinstance(actor_id, str) or not actor_id.strip():
            raise ValueError("actor_id обязателен")
        if self.audit_service is not None:
            self.audit_service.append(actor_id=actor_id, action=action,
                resource_type="alarm_definition", resource_id=definition_id,
                outcome="success", details=details)

    def get_control_state(self, definition_id: str) -> dict:
        self.get(definition_id)
        with self._db() as db:
            row = db.execute("SELECT shelved_until,suppressed FROM alarm_controls WHERE definition_id=?",
                             (definition_id,)).fetchone()
        now = time.time()
        return {"shelved": bool(row[0] is not None and row[0] > now),
                "shelved_until": row[0], "suppressed": bool(row[1]),
                "annunciation_suppressed": bool(row[1]) or bool(row[0] is not None and row[0] > now)}

    def set_shelved(self, definition_id: str, *, duration_seconds: float, actor_id: str = "system"):

        if duration_seconds <= 0 or duration_seconds > 30 * 86400:
            raise ValueError("Shelving должен быть от 1 секунды до 30 дней")
        self.get(definition_id)
        until = time.time() + duration_seconds
        with self._db() as db:
            db.execute("UPDATE alarm_controls SET shelved_until=?,updated_at=? WHERE definition_id=?",
                       (until, time.time(), definition_id))
        self._audit_control(actor_id, "alarm.definition.shelve", definition_id,
                            {"duration_seconds": duration_seconds, "shelved_until": until})
        return until

    def unshelve(self, definition_id: str, *, actor_id: str = "system"):

        self.get(definition_id)
        with self._db() as db:
            db.execute("UPDATE alarm_controls SET shelved_until=NULL,updated_at=? WHERE definition_id=?",
                       (time.time(), definition_id))
        self._audit_control(actor_id, "alarm.definition.unshelve", definition_id, {})

    def set_suppressed(self, definition_id: str, suppressed: bool, *, actor_id: str = "system"):
        if not isinstance(suppressed, bool):
            raise ValueError("suppressed должен быть bool")

        self.get(definition_id)
        with self._db() as db:
            db.execute("UPDATE alarm_controls SET suppressed=?,updated_at=? WHERE definition_id=?",
                       (int(suppressed), time.time(), definition_id))
        self._audit_control(actor_id, "alarm.definition.suppress" if suppressed else "alarm.definition.unsuppress",
                            definition_id, {"suppressed": suppressed})

    def evaluate(self, definition_id: str, value: Any, *, quality: str = "Good",
                 now: float | None = None):
        """Evaluate one sample. Bad/Uncertain/Stale quality never creates a new alarm."""
        d = self.get(definition_id)
        now = time.time() if now is None else float(now)
        if not d.enabled:
            return None
        if quality != "Good":
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError("Для числового определения требуется числовое значение")
        with self._db() as db:
            db.row_factory = sqlite3.Row
            control = db.execute("SELECT * FROM alarm_controls WHERE definition_id=?", (definition_id,)).fetchone()
            state = db.execute("SELECT * FROM alarm_rule_state WHERE definition_id=?", (definition_id,)).fetchone()
            active = bool(state["condition_active"])
            latched = bool(state["latched"])
            blocked = bool(control["suppressed"]) or (control["shelved_until"] is not None and control["shelved_until"] > now)
            op = d.operator
            raw = {">": value > d.setpoint, ">=": value >= d.setpoint,
                   "<": value < d.setpoint, "<=": value <= d.setpoint,
                   "==": value == d.setpoint, "!=": value != d.setpoint}[op]
            if active:
                if op in (">", ">="):
                    condition = value > d.setpoint - d.hysteresis if op == ">" else value >= d.setpoint - d.hysteresis
                elif op in ("<", "<="):
                    condition = value < d.setpoint + d.hysteresis if op == "<" else value <= d.setpoint + d.hysteresis
                else:
                    condition = raw
            else:
                condition = raw
            pending_since = state["pending_since"]
            stable_active = condition == active and active
            if condition == active:
                db.execute("UPDATE alarm_rule_state SET pending_since=NULL,updated_at=? WHERE definition_id=?",
                           (now, definition_id))
            elif pending_since is None:
                db.execute("UPDATE alarm_rule_state SET pending_since=?,updated_at=? WHERE definition_id=?",
                           (now, now, definition_id))
                return None
            else:
                delay = d.on_delay if condition else d.off_delay
                if now - float(pending_since) < delay:
                    return None
                db.execute("UPDATE alarm_rule_state SET condition_active=?,pending_since=NULL,"
                           "latched=CASE WHEN ?=1 THEN 1 WHEN ?=0 AND ?=0 THEN 0 ELSE latched END,updated_at=? "
                           "WHERE definition_id=?", (int(condition), int(condition), int(condition),
                           int(d.latching), now, definition_id))
        control_state = self.get_control_state(definition_id)
        alarm_metadata = {**(d.metadata or {}), "value": value, "setpoint": d.setpoint,
                          "definition_id": definition_id, "quality": quality,
                          "shelved": control_state["shelved"],
                          "suppressed": control_state["suppressed"],
                          "annunciation_suppressed": control_state["annunciation_suppressed"]}
        if stable_active:
            try:
                return self.alarms.get_alarm_by_key(d.station_id, d.source_id, d.alarm_key)
            except KeyError:
                return self.alarms.raise_alarm(station_id=d.station_id, source_id=d.source_id,
                    alarm_key=d.alarm_key, name=d.name, message=d.message,
                    category=d.category, priority=d.priority, metadata=alarm_metadata)
        if condition:
            return self.alarms.raise_alarm(station_id=d.station_id, source_id=d.source_id,
                alarm_key=d.alarm_key, name=d.name, message=d.message,
                category=d.category, priority=d.priority, metadata=alarm_metadata)
        if d.latching:
            with self._db() as db:
                row = db.execute("SELECT latched FROM alarm_rule_state WHERE definition_id=?",
                                 (definition_id,)).fetchone()
            if row and row[0]:
                return self.alarms.get_alarm_by_key(d.station_id, d.source_id, d.alarm_key)
        try:
            alarm = self.alarms.get_alarm_by_key(d.station_id, d.source_id, d.alarm_key)
        except KeyError:
            return None
        return self.alarms.return_to_normal(alarm.alarm_id, details={"definition_id": definition_id,
            "value": value, "setpoint": d.setpoint, "quality": quality})

    def acknowledge(self, definition_id: str, *, actor_id: str, comment: str = ""):
        d = self.get(definition_id)
        alarm = self.alarms.get_alarm_by_key(d.station_id, d.source_id, d.alarm_key)
        result = self.alarms.acknowledge(alarm.alarm_id, actor_id=actor_id, comment=comment)
        with self._db() as db:
            state = db.execute("SELECT condition_active,latched FROM alarm_rule_state WHERE definition_id=?",
                               (definition_id,)).fetchone()
            if d.latching and state and not state[0] and state[1]:
                db.execute("UPDATE alarm_rule_state SET latched=0,updated_at=? WHERE definition_id=?",
                           (time.time(), definition_id))
                return self.alarms.return_to_normal(result.alarm_id,
                    message="Защёлкнутая авария подтверждена оператором и условие нормализовано",
                    details={"definition_id": definition_id, "latch_reset_by": actor_id})
        return result
