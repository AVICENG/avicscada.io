from __future__ import annotations

import json
import math
import sqlite3
from contextlib import closing
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class ScheduleError(ValueError):
    pass


class ScheduleNotFound(KeyError):
    pass


class ScheduleConflict(RuntimeError):
    pass


_VALUE_TYPES = {"BOOLEAN", "NUMERIC", "ENUM", "STRING"}


def _id() -> str:
    return str(uuid4())


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _typed_value(value_type: str, value: Any) -> Any:
    kind = value_type.upper()
    if kind not in _VALUE_TYPES:
        raise ScheduleError(f"Неподдерживаемый тип расписания: {value_type}")
    if kind == "BOOLEAN":
        if not isinstance(value, bool):
            raise ScheduleError("Для BOOLEAN требуется true или false")
        return value
    if kind == "NUMERIC":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ScheduleError("Для NUMERIC требуется число")
        if not math.isfinite(float(value)) or not (-1e15 < float(value) < 1e15):
            raise ScheduleError("Числовое значение вне допустимого диапазона")
        return value
    if kind == "ENUM":
        if isinstance(value, (dict, list)) or value is None:
            raise ScheduleError("Для ENUM требуется строковое или числовое значение")
        if not isinstance(value, (str, int, float, bool)):
            raise ScheduleError("Недопустимое значение ENUM")
        return value
    if not isinstance(value, str):
        raise ScheduleError("Для STRING требуется текст")
    if len(value) > 4096:
        raise ScheduleError("Строковое значение слишком длинное")
    return value


def _minute(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 1440:
        raise ScheduleError(f"{field}: значение должно быть от 0 до 1440 минут")
    return value


def _enum_text(value: Any, default: str = "") -> str:
    if isinstance(value, dict) and value.get("__type__") == "enum":
        return str(value.get("value", default))
    return str(getattr(value, "value", value if value is not None else default))


class ScheduleService:
    """Persistent typed weekly/calendar schedules. Evaluation creates intent only;
    it never writes to physical controllers or point values.
    """

    def __init__(self, database_path: str | Path, *, repository=None, audit_service=None, point_usage_service=None):
        self.path = str(database_path)
        self.repository = repository
        self.audit = audit_service
        self.point_usage_service = point_usage_service
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS schedules (
                schedule_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, name TEXT NOT NULL,
                value_type TEXT NOT NULL, timezone TEXT NOT NULL, default_json TEXT NOT NULL,
                effective_start TEXT, effective_end TEXT, enabled INTEGER NOT NULL,
                revision INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(station_id, name));
            CREATE TABLE IF NOT EXISTS weekly_events (
                event_id TEXT PRIMARY KEY, schedule_id TEXT NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
                day_of_week INTEGER NOT NULL, start_minute INTEGER NOT NULL, end_minute INTEGER NOT NULL,
                value_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
            CREATE INDEX IF NOT EXISTS ix_weekly_schedule_day ON weekly_events(schedule_id, day_of_week, start_minute);
            CREATE TABLE IF NOT EXISTS special_events (
                event_id TEXT PRIMARY KEY, schedule_id TEXT NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
                name TEXT NOT NULL, start_date TEXT NOT NULL, end_date TEXT NOT NULL,
                start_minute INTEGER NOT NULL, end_minute INTEGER NOT NULL, priority INTEGER NOT NULL,
                value_json TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1);
            CREATE INDEX IF NOT EXISTS ix_special_schedule_dates ON special_events(schedule_id, start_date, end_date, priority);
            CREATE TABLE IF NOT EXISTS schedule_bindings (
                schedule_id TEXT NOT NULL REFERENCES schedules(schedule_id) ON DELETE CASCADE,
                point_id TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(schedule_id, point_id));
            CREATE TABLE IF NOT EXISTS schedule_overrides (
                schedule_id TEXT PRIMARY KEY REFERENCES schedules(schedule_id) ON DELETE CASCADE,
                value_json TEXT NOT NULL, expires_at TEXT NOT NULL, actor_id TEXT NOT NULL,
                reason TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def _audit(self, actor: str, action: str, schedule_id: str, details: dict):
        if self.audit is not None:
            self.audit.append(actor_id=actor, action=action, resource_type="schedule",
                              resource_id=schedule_id, details=details)

    def create(self, *, station_id: str, name: str, value_type: str,
               timezone_name: str = "UTC", default_value: Any = False,
               effective_start: str | None = None, effective_end: str | None = None,
               enabled: bool = True, actor_id: str = "local-engineer") -> dict:
        if not station_id or not station_id.strip():
            raise ScheduleError("station_id обязателен")
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise ScheduleError("Название расписания обязательно (до 160 символов)")
        kind = value_type.upper()
        default = _typed_value(kind, default_value)
        try:
            ZoneInfo(timezone_name)
        except (ZoneInfoNotFoundError, ValueError):
            raise ScheduleError(f"Неизвестная временная зона: {timezone_name}")
        try:
            start_date = date.fromisoformat(effective_start) if effective_start else None
            end_date = date.fromisoformat(effective_end) if effective_end else None
        except ValueError as exc:
            raise ScheduleError("Период действия должен использовать формат YYYY-MM-DD") from exc
        if start_date and end_date and start_date > end_date:
            raise ScheduleError("Дата начала действия позже даты окончания")
        now = datetime.now(timezone.utc).isoformat()
        schedule_id = _id()
        with closing(self._connect()) as db:
            try:
                db.execute("INSERT INTO schedules VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (schedule_id, station_id, name.strip(), kind, timezone_name, _json(default),
                     effective_start, effective_end, int(bool(enabled)), 1, now, now))
                db.commit()
            except sqlite3.IntegrityError as exc:
                raise ScheduleConflict("Расписание с таким именем уже существует на станции") from exc
        self._audit(actor_id, "schedule.created", schedule_id,
                    {"station_id": station_id, "name": name.strip(), "value_type": kind})
        return self.get(schedule_id)

    def _row(self, schedule_id: str, db=None):
        if db is None:
            with closing(self._connect()) as conn:
                row = conn.execute("SELECT * FROM schedules WHERE schedule_id=?", (schedule_id,)).fetchone()
        else:
            row = db.execute("SELECT * FROM schedules WHERE schedule_id=?", (schedule_id,)).fetchone()
        if row is None:
            raise ScheduleNotFound(schedule_id)
        return row

    def _serialize(self, row, db) -> dict:
        sid = row["schedule_id"]
        weekly = db.execute("SELECT * FROM weekly_events WHERE schedule_id=? ORDER BY day_of_week,start_minute", (sid,)).fetchall()
        special = db.execute("SELECT * FROM special_events WHERE schedule_id=? ORDER BY start_date,priority DESC,start_minute", (sid,)).fetchall()
        bindings = db.execute("SELECT point_id FROM schedule_bindings WHERE schedule_id=? ORDER BY point_id", (sid,)).fetchall()
        return {"id": sid, "station_id": row["station_id"], "name": row["name"],
            "value_type": row["value_type"], "timezone": row["timezone"],
            "default_value": json.loads(row["default_json"]), "effective_start": row["effective_start"],
            "effective_end": row["effective_end"], "enabled": bool(row["enabled"]),
            "revision": row["revision"], "created_at": row["created_at"], "updated_at": row["updated_at"],
            "weekly_events": [{"id": x["event_id"], "day_of_week": x["day_of_week"],
                "start_minute": x["start_minute"], "end_minute": x["end_minute"],
                "value": json.loads(x["value_json"]), "revision": x["revision"]} for x in weekly],
            "special_events": [{"id": x["event_id"], "name": x["name"], "start_date": x["start_date"],
                "end_date": x["end_date"], "start_minute": x["start_minute"], "end_minute": x["end_minute"],
                "priority": x["priority"], "value": json.loads(x["value_json"]), "revision": x["revision"]} for x in special],
            "point_ids": [x["point_id"] for x in bindings]}

    def get(self, schedule_id: str) -> dict:
        with closing(self._connect()) as db:
            return self._serialize(self._row(schedule_id, db), db)

    def list(self, *, station_id: str) -> list[dict]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM schedules WHERE station_id=? ORDER BY name", (station_id,)).fetchall()
            return [self._serialize(row, db) for row in rows]

    def _bump(self, db, schedule_id: str, expected_revision: int | None):
        row = self._row(schedule_id, db)
        if expected_revision is not None and row["revision"] != expected_revision:
            raise ScheduleConflict(f"CONCURRENCY_CONFLICT: expected {expected_revision}, current {row['revision']}")
        db.execute("UPDATE schedules SET revision=revision+1,updated_at=? WHERE schedule_id=?",
                   (datetime.now(timezone.utc).isoformat(), schedule_id))

    def add_weekly_event(self, schedule_id: str, *, day_of_week: int, start_minute: int,
                         end_minute: int, value: Any, expected_revision: int | None = None,
                         actor_id: str = "local-engineer") -> dict:
        if isinstance(day_of_week, bool) or not isinstance(day_of_week, int) or not 0 <= day_of_week <= 6:
            raise ScheduleError("day_of_week должен быть от 0 (понедельник) до 6 (воскресенье)")
        start, end = _minute(start_minute, "start_minute"), _minute(end_minute, "end_minute")
        if start >= end:
            raise ScheduleError("Время окончания должно быть позже времени начала; ночной интервал разделите на два")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._row(schedule_id, db)
            typed = _typed_value(row["value_type"], value)
            overlap = db.execute("SELECT 1 FROM weekly_events WHERE schedule_id=? AND day_of_week=? AND NOT(end_minute<=? OR start_minute>=?) LIMIT 1",
                                 (schedule_id, day_of_week, start, end)).fetchone()
            if overlap:
                raise ScheduleConflict("Интервал пересекается с уже существующим событием этого дня")
            event_id = _id()
            db.execute("INSERT INTO weekly_events(event_id,schedule_id,day_of_week,start_minute,end_minute,value_json) VALUES(?,?,?,?,?,?)",
                       (event_id, schedule_id, day_of_week, start, end, _json(typed)))
            self._bump(db, schedule_id, expected_revision)
            db.commit()
        self._audit(actor_id, "schedule.weekly_event.created", schedule_id,
                    {"event_id": event_id, "day_of_week": day_of_week, "start_minute": start, "end_minute": end})
        return self.get(schedule_id)

    def copy_weekly_day(self, schedule_id: str, *, source_day: int, target_days: list[int],
                        expected_revision: int | None = None,
                        actor_id: str = "local-engineer") -> dict:
        """Replace target weekdays with a copy of source_day in one transaction.

        This is the backend operation used by Copy Day / Paste Day / Apply M-F.
        Destination events are replaced atomically; source day is never modified.
        """
        if isinstance(source_day, bool) or not isinstance(source_day, int) or not 0 <= source_day <= 6:
            raise ScheduleError("source_day должен быть от 0 (понедельник) до 6 (воскресенье)")
        if not isinstance(target_days, list) or not target_days:
            raise ScheduleError("Необходимо указать хотя бы один день назначения")
        normalized: list[int] = []
        for day in target_days:
            if isinstance(day, bool) or not isinstance(day, int) or not 0 <= day <= 6:
                raise ScheduleError("Каждый день назначения должен быть от 0 до 6")
            if day == source_day:
                raise ScheduleError("День-источник нельзя указывать среди дней назначения")
            if day in normalized:
                raise ScheduleError("Дни назначения не должны повторяться")
            normalized.append(day)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._row(schedule_id, db)
            if expected_revision is not None:
                current = self._row(schedule_id, db)["revision"]
                if current != expected_revision:
                    raise ScheduleConflict(f"CONCURRENCY_CONFLICT: expected {expected_revision}, current {current}")
            source = db.execute(
                "SELECT start_minute,end_minute,value_json FROM weekly_events WHERE schedule_id=? AND day_of_week=? ORDER BY start_minute",
                (schedule_id, source_day)).fetchall()
            for target in normalized:
                db.execute("DELETE FROM weekly_events WHERE schedule_id=? AND day_of_week=?", (schedule_id, target))
                for event in source:
                    db.execute("INSERT INTO weekly_events(event_id,schedule_id,day_of_week,start_minute,end_minute,value_json) VALUES(?,?,?,?,?,?)",
                        (_id(), schedule_id, target, event["start_minute"], event["end_minute"], event["value_json"]))
            self._bump(db, schedule_id, expected_revision)
            db.commit()
        self._audit(actor_id, "schedule.weekly_day.copied", schedule_id,
                    {"source_day": source_day, "target_days": normalized, "events_copied_per_day": len(source)})
        return self.get(schedule_id)

    def delete_weekly_event(self, schedule_id: str, event_id: str, *, expected_revision: int | None = None,
                            actor_id: str = "local-engineer") -> dict:
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._row(schedule_id, db)
            cur = db.execute("DELETE FROM weekly_events WHERE schedule_id=? AND event_id=?", (schedule_id, event_id))
            if cur.rowcount != 1:
                raise ScheduleNotFound(event_id)
            self._bump(db, schedule_id, expected_revision)
            db.commit()
        self._audit(actor_id, "schedule.weekly_event.deleted", schedule_id, {"event_id": event_id})
        return self.get(schedule_id)

    def add_special_event(self, schedule_id: str, *, name: str, start_date: str, end_date: str,
                          start_minute: int = 0, end_minute: int = 1440, priority: int = 1,
                          value: Any, expected_revision: int | None = None,
                          actor_id: str = "local-engineer") -> dict:
        try:
            start_d, end_d = date.fromisoformat(start_date), date.fromisoformat(end_date)
        except ValueError as exc:
            raise ScheduleError("Даты исключения должны быть в формате YYYY-MM-DD") from exc
        if end_d < start_d:
            raise ScheduleError("Окончание исключения раньше начала")
        start, end = _minute(start_minute, "start_minute"), _minute(end_minute, "end_minute")
        if start >= end:
            raise ScheduleError("Время окончания должно быть позже времени начала")
        if not isinstance(name, str) or not name.strip() or len(name) > 160:
            raise ScheduleError("Название исключения обязательно")
        if isinstance(priority, bool) or not isinstance(priority, int) or not 1 <= priority <= 16:
            raise ScheduleError("Приоритет исключения должен быть от 1 до 16")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = self._row(schedule_id, db)
            typed = _typed_value(row["value_type"], value)
            conflict = db.execute("""SELECT 1 FROM special_events WHERE schedule_id=? AND priority=?
                AND start_date<=? AND end_date>=? AND NOT(end_minute<=? OR start_minute>=?) LIMIT 1""",
                (schedule_id, priority, end_date, start_date, start, end)).fetchone()
            if conflict:
                raise ScheduleConflict("Календарные исключения одного приоритета пересекаются; измените даты, время или приоритет")
            event_id = _id()
            db.execute("INSERT INTO special_events(event_id,schedule_id,name,start_date,end_date,start_minute,end_minute,priority,value_json) VALUES(?,?,?,?,?,?,?,?,?)",
                       (event_id, schedule_id, name.strip(), start_date, end_date, start, end, priority, _json(typed)))
            self._bump(db, schedule_id, expected_revision)
            db.commit()
        self._audit(actor_id, "schedule.special_event.created", schedule_id,
                    {"event_id": event_id, "name": name.strip(), "start_date": start_date,
                     "end_date": end_date, "priority": priority})
        return self.get(schedule_id)

    def delete_special_event(self, schedule_id: str, event_id: str, *, expected_revision: int | None = None,
                             actor_id: str = "local-engineer") -> dict:
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._row(schedule_id, db)
            cur = db.execute("DELETE FROM special_events WHERE schedule_id=? AND event_id=?", (schedule_id, event_id))
            if cur.rowcount != 1:
                raise ScheduleNotFound(event_id)
            self._bump(db, schedule_id, expected_revision)
            db.commit()
        self._audit(actor_id, "schedule.special_event.deleted", schedule_id, {"event_id": event_id})
        return self.get(schedule_id)

    def list_bindable_points(self, station_id: str, value_type: str) -> list[dict]:
        if self.repository is None:
            return []
        kind = value_type.upper()
        compatible = {"BOOLEAN": {"bool", "boolean"}, "NUMERIC": {"float", "double", "number", "numeric", "int", "integer"},
                      "ENUM": {"enum", "string", "int", "integer"}, "STRING": {"string", "str"}}
        if kind not in compatible:
            raise ScheduleError(f"Неподдерживаемый тип расписания: {value_type}")
        result = []
        for row in self.repository.list_records(entity_type="Point"):
            p = row.get("payload", {})
            direction = _enum_text(p.get("direction"), "input").lower()
            data_type = _enum_text(p.get("data_type"), "").lower()
            if direction not in {"output", "inout"} or data_type not in compatible[kind]:
                continue
            try:
                device = self.repository.get_record(p.get("device_id", ""))
            except Exception:
                continue
            if device.get("payload", {}).get("station_id") != station_id:
                continue
            result.append({"id": row["entity_id"], "name": p.get("name", row.get("name", row["entity_id"])),
                           "device_id": p.get("device_id"), "data_type": data_type, "direction": direction,
                           "unit": p.get("unit", "")})
        return sorted(result, key=lambda x: (x["name"].casefold(), x["id"]))

    def bind_point(self, schedule_id: str, point_id: str, *, actor_id: str = "local-engineer") -> dict:
        if self.repository is None:
            raise ScheduleError("Репозиторий точек не подключён")
        schedule = self.get(schedule_id)
        try:
            point = self.repository.get_record(point_id)
        except Exception as exc:
            raise ScheduleError("Точка не найдена") from exc
        if point.get("entity_type") != "Point":
            raise ScheduleError("Можно привязывать только инженерные точки")
        p = point["payload"]
        direction = _enum_text(p.get("direction"), "input").lower()
        if direction not in {"output", "inout"}:
            raise ScheduleError("Расписание можно привязать только к выходной или двунаправленной точке")
        data_type = _enum_text(p.get("data_type"), "").lower()
        compatible = {"BOOLEAN": {"bool", "boolean"}, "NUMERIC": {"float", "double", "number", "numeric", "int", "integer"},
                      "ENUM": {"enum", "string", "int", "integer"}, "STRING": {"string", "str"}}
        if data_type not in compatible[schedule["value_type"]]:
            raise ScheduleError(f"Тип точки {data_type} несовместим с {schedule['value_type']}")
        device = self.repository.get_record(p.get("device_id", ""))
        if device.get("payload", {}).get("station_id") != schedule["station_id"]:
            raise ScheduleError("Точка принадлежит другой станции")
        previous_point_ids = list(schedule["point_ids"])
        desired_point_ids = sorted(set(previous_point_ids) | {point_id})
        # Activate the license reference before committing the scheduler binding.
        # If the schedule transaction fails, compensate by restoring its prior set.
        if self.point_usage_service is not None:
            self.point_usage_service.set_point_usage(f"schedule:{schedule_id}", desired_point_ids)
        try:
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT OR IGNORE INTO schedule_bindings(schedule_id,point_id,created_at) VALUES(?,?,?)",
                           (schedule_id, point_id, datetime.now(timezone.utc).isoformat()))
                self._bump(db, schedule_id, None)
                db.commit()
        except Exception:
            if self.point_usage_service is not None:
                self.point_usage_service.set_point_usage(f"schedule:{schedule_id}", previous_point_ids)
            raise
        self._audit(actor_id, "schedule.point.bound", schedule_id, {"point_id": point_id})
        return self.get(schedule_id)

    def unbind_point(self, schedule_id: str, point_id: str, *, actor_id: str = "local-engineer") -> dict:
        schedule = self.get(schedule_id)
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            self._row(schedule_id, db)
            db.execute("DELETE FROM schedule_bindings WHERE schedule_id=? AND point_id=?", (schedule_id, point_id))
            self._bump(db, schedule_id, None)
            db.commit()
        remaining_point_ids = [item for item in schedule["point_ids"] if item != point_id]
        if self.point_usage_service is not None:
            self.point_usage_service.set_point_usage(f"schedule:{schedule_id}", remaining_point_ids)
        self._audit(actor_id, "schedule.point.unbound", schedule_id, {"point_id": point_id})
        return self.get(schedule_id)

    def set_override(self, schedule_id: str, *, value: Any, duration_seconds: int,
                     actor_id: str, reason: str) -> dict:
        if isinstance(duration_seconds, bool) or not isinstance(duration_seconds, int) or not 1 <= duration_seconds <= 7 * 86400:
            raise ScheduleError("Временное переопределение должно длиться от 1 секунды до 7 дней")
        if not actor_id.strip() or not reason.strip():
            raise ScheduleError("Для ручного переопределения обязательны оператор и причина")
        schedule = self.get(schedule_id)
        typed = _typed_value(schedule["value_type"], value)
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=duration_seconds)
        with closing(self._connect()) as db:
            db.execute("INSERT INTO schedule_overrides(schedule_id,value_json,expires_at,actor_id,reason,created_at) VALUES(?,?,?,?,?,?) "
                       "ON CONFLICT(schedule_id) DO UPDATE SET value_json=excluded.value_json,expires_at=excluded.expires_at,actor_id=excluded.actor_id,reason=excluded.reason,created_at=excluded.created_at",
                       (schedule_id, _json(typed), expires.isoformat(), actor_id, reason.strip(), now.isoformat()))
            self._bump(db, schedule_id, None)
            db.commit()
        self._audit(actor_id, "schedule.override.created", schedule_id,
                    {"value": typed, "expires_at": expires.isoformat(), "reason": reason.strip()})
        return self.evaluate(schedule_id, now=now)

    def clear_override(self, schedule_id: str, *, actor_id: str = "local-engineer") -> None:
        with closing(self._connect()) as db:
            self._row(schedule_id, db)
            db.execute("DELETE FROM schedule_overrides WHERE schedule_id=?", (schedule_id,))
            self._bump(db, schedule_id, None)
            db.commit()
        self._audit(actor_id, "schedule.override.cleared", schedule_id, {})

    def _resolve(self, schedule: dict, instant: datetime, tz: ZoneInfo) -> dict:
        local = instant.astimezone(tz)
        active_period = ((not schedule["effective_start"] or local.date().isoformat() >= schedule["effective_start"])
                         and (not schedule["effective_end"] or local.date().isoformat() <= schedule["effective_end"]))
        if not schedule["enabled"] or not active_period:
            return {"value": schedule["default_value"], "source": "DEFAULT", "source_id": None}
        with closing(self._connect()) as db:
            override = db.execute("SELECT * FROM schedule_overrides WHERE schedule_id=?", (schedule["id"],)).fetchone()
            special = db.execute("SELECT * FROM special_events WHERE schedule_id=? AND start_date<=? AND end_date>=?",
                                 (schedule["id"], local.date().isoformat(), local.date().isoformat())).fetchall()
            weekly = db.execute("SELECT * FROM weekly_events WHERE schedule_id=? AND day_of_week=?",
                                (schedule["id"], local.weekday())).fetchall()
        if override and datetime.fromisoformat(override["expires_at"]) > instant.astimezone(timezone.utc):
            return {"value": json.loads(override["value_json"]), "source": "MANUAL_OVERRIDE", "source_id": None}
        minute = local.hour * 60 + local.minute
        matching_special = [x for x in special if x["start_minute"] <= minute < x["end_minute"]]
        if matching_special:
            winner = max(matching_special, key=lambda x: (x["priority"], x["revision"], x["event_id"]))
            return {"value": json.loads(winner["value_json"]), "source": "SPECIAL_EVENT", "source_id": winner["event_id"]}
        matching_weekly = [x for x in weekly if x["start_minute"] <= minute < x["end_minute"]]
        if matching_weekly:
            winner = matching_weekly[0]
            return {"value": json.loads(winner["value_json"]), "source": "WEEKLY_SCHEDULE", "source_id": winner["event_id"]}
        return {"value": schedule["default_value"], "source": "DEFAULT", "source_id": None}

    def evaluate(self, schedule_id: str, *, now: datetime | None = None) -> dict:
        schedule = self.get(schedule_id)
        try:
            tz = ZoneInfo(schedule["timezone"])
        except ZoneInfoNotFoundError as exc:
            raise ScheduleError("Часовой пояс расписания недоступен") from exc
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None:
            raise ScheduleError("Время вычисления должно содержать часовой пояс")
        instant = instant.astimezone(timezone.utc)
        local = instant.astimezone(tz)
        resolved = self._resolve(schedule, instant, tz)
        next_change = self._next_change(schedule, instant, tz, resolved)
        return {"schedule_id": schedule_id, "station_id": schedule["station_id"],
                "value": resolved["value"], "value_type": schedule["value_type"],
                "source": resolved["source"], "source_id": resolved["source_id"],
                "evaluated_at": instant.isoformat(), "local_time": local.isoformat(),
                "timezone": schedule["timezone"], "next_change": next_change,
                "point_ids": schedule["point_ids"],
                "output_mode": "INTENT_ONLY_NO_FIELD_WRITE"}

    def _next_change(self, schedule: dict, instant: datetime, tz: ZoneInfo,
                     current: dict) -> dict | None:
        local = instant.astimezone(tz)
        candidates: set[datetime] = set()
        start_date = local.date()
        for boundary_date in (schedule["effective_start"],
                              (date.fromisoformat(schedule["effective_end"]) + timedelta(days=1)).isoformat()
                              if schedule["effective_end"] else None):
            if boundary_date:
                dt = datetime.combine(date.fromisoformat(boundary_date), time.min, tzinfo=tz)
                if dt.astimezone(timezone.utc) > instant:
                    candidates.add(dt)
        for offset in range(0, 9):
            day = start_date + timedelta(days=offset)
            if schedule["effective_start"] and day.isoformat() < schedule["effective_start"]:
                continue
            if schedule["effective_end"] and day.isoformat() > schedule["effective_end"]:
                continue
            for event in schedule["weekly_events"]:
                if event["day_of_week"] == day.weekday():
                    for minute in (event["start_minute"], event["end_minute"]):
                        dt = (datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
                              if minute == 1440 else datetime.combine(day, time(minute // 60, minute % 60), tzinfo=tz))
                        if dt.astimezone(timezone.utc) > instant:
                            candidates.add(dt)
            for event in schedule["special_events"]:
                if event["start_date"] <= day.isoformat() <= event["end_date"]:
                    for minute in (event["start_minute"], event["end_minute"]):
                        dt = (datetime.combine(day + timedelta(days=1), time.min, tzinfo=tz)
                              if minute == 1440 else datetime.combine(day, time(minute // 60, minute % 60), tzinfo=tz))
                        if dt.astimezone(timezone.utc) > instant:
                            candidates.add(dt)
        with closing(self._connect()) as db:
            override = db.execute("SELECT expires_at FROM schedule_overrides WHERE schedule_id=?", (schedule["id"],)).fetchone()
        if override:
            expiry = datetime.fromisoformat(override["expires_at"])
            if expiry.tzinfo is None:
                expiry = expiry.replace(tzinfo=timezone.utc)
            if expiry.astimezone(timezone.utc) > instant:
                candidates.add(expiry.astimezone(tz))
        for boundary in sorted(candidates, key=lambda x: x.astimezone(timezone.utc)):
            # Evaluate just after the boundary to obtain the value that actually wins,
            # including special-event priority and override expiry.
            after = boundary.astimezone(timezone.utc) + timedelta(seconds=1)
            following = self._resolve(schedule, after, tz)
            if following != current:
                return {"at": boundary.isoformat(), "value": following["value"],
                        "source": following["source"], "source_id": following["source_id"]}
        return None

