"""Audited, lease-gated command workflow with a deliberately simulation-only executor.

No protocol writes are performed here. A physical driver executor must be added as a
separate capability-gated adapter and must pass the same policy checks.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID, uuid4

from avic_core.domain.models import Point, PointDirection
from avic_core.repository.sqlite_repository import EntityNotFound


def _now() -> datetime:
    return datetime.now(timezone.utc)


class CommandRejected(ValueError):
    pass


class CommandManagerService:
    MAX_LEASE_SECONDS = 900
    ALLOWED_COMMANDS = {"START": True, "STOP": False}

    def __init__(self, core, database: str | Path):
        self.core = core
        self.database = str(database)
        self._lock = RLock()
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS access_leases (
                lease_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, actor_id TEXT NOT NULL,
                issued_at TEXT NOT NULL, expires_at TEXT NOT NULL, revoked_at TEXT)""")
            db.execute("""CREATE TABLE IF NOT EXISTS commands (
                command_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, point_id TEXT NOT NULL,
                actor_id TEXT NOT NULL, command TEXT NOT NULL, requested_value TEXT NOT NULL,
                state TEXT NOT NULL, feedback_value TEXT, feedback_quality TEXT,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL, reason TEXT NOT NULL,
                lease_id TEXT NOT NULL, execution_mode TEXT NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_commands_station ON commands(station_id, created_at)")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @contextmanager
    def _db(self):
        db = self._connect()
        try:
            with db:
                yield db
        finally:
            db.close()

    def acquire_lease(self, station_id: str, actor_id: str, duration_seconds: int = 300) -> dict[str, Any]:
        if not actor_id or not actor_id.strip():
            raise CommandRejected("Не указан пользователь")
        if not 1 <= duration_seconds <= self.MAX_LEASE_SECONDS:
            raise CommandRejected(f"Срок Access Lease должен быть от 1 до {self.MAX_LEASE_SECONDS} секунд")
        station = self.core.repository.get_record(station_id)
        if station.get("entity_type") != "Station":
            raise CommandRejected("Access Lease можно получить только для станции")
        now = _now(); lease_id = str(uuid4()); expires = now + timedelta(seconds=duration_seconds)
        with self._db() as db:
            db.execute("UPDATE access_leases SET revoked_at=? WHERE station_id=? AND revoked_at IS NULL AND expires_at>?",
                       (now.isoformat(), station_id, now.isoformat()))
            db.execute("INSERT INTO access_leases VALUES(?,?,?,?,?,NULL)",
                       (lease_id, station_id, actor_id, now.isoformat(), expires.isoformat()))
        self.core.audit.append(actor_id=actor_id, action="control.lease_acquired", resource_type="station",
                               resource_id=station_id, details={"lease_id": lease_id, "expires_at": expires.isoformat()})
        return {"lease_id": lease_id, "station_id": station_id, "actor_id": actor_id,
                "issued_at": now.isoformat(), "expires_at": expires.isoformat(), "active": True,
                "execution_mode": "SIMULATION_ONLY"}

    def revoke_lease(self, lease_id: str, actor_id: str) -> dict[str, Any]:
        now = _now()
        with self._db() as db:
            row = db.execute("SELECT * FROM access_leases WHERE lease_id=?", (lease_id,)).fetchone()
            if row is None:
                raise CommandRejected("Access Lease не найден")
            if row["actor_id"] != actor_id:
                raise CommandRejected("Отозвать Access Lease может только выдавший его пользователь")
            db.execute("UPDATE access_leases SET revoked_at=? WHERE lease_id=?", (now.isoformat(), lease_id))
        self.core.audit.append(actor_id=actor_id, action="control.lease_revoked", resource_type="station",
                               resource_id=row["station_id"], details={"lease_id": lease_id})
        return {"lease_id": lease_id, "active": False, "revoked_at": now.isoformat()}

    def _active_lease(self, lease_id: str, station_id: str, actor_id: str):
        now = _now()
        with self._db() as db:
            row = db.execute("SELECT * FROM access_leases WHERE lease_id=?", (lease_id,)).fetchone()
        if row is None or row["station_id"] != station_id or row["actor_id"] != actor_id:
            raise CommandRejected("Нет действующего Access Lease для этой станции и пользователя")
        if row["revoked_at"] or datetime.fromisoformat(row["expires_at"]) <= now:
            raise CommandRejected("Access Lease истёк или отозван")
        return row

    def request(self, *, station_id: str, point_id: str, actor_id: str, lease_id: str,
                command: str, reason: str, interlock_point_ids: list[str] | None = None) -> dict[str, Any]:
        command = str(command).upper()
        if command not in self.ALLOWED_COMMANDS:
            raise CommandRejected("Поддерживаются только команды START и STOP")
        if not reason or not reason.strip():
            raise CommandRejected("Для команды обязательна причина")
        self._active_lease(lease_id, station_id, actor_id)
        try:
            row = self.core.repository.get_record(point_id)
            if row.get("entity_type") != "Point":
                raise CommandRejected("Команда разрешена только физической OUTPUT-точке; виртуальные FBD-точки не записываются")
            point, _ = self.core.repository.get(point_id, Point)
            device_row = self.core.repository.get_record(point.device_id)
        except EntityNotFound as exc:
            raise CommandRejected("Целевая точка или устройство не найдены") from exc
        if device_row.get("entity_type") != "Device":
            raise CommandRejected("У точки отсутствует устройство")
        device = device_row.get("payload", {})
        if device.get("station_id") != station_id:
            raise CommandRejected("Точка принадлежит другой станции")
        direction = getattr(point.direction, "value", str(point.direction)).lower()
        if direction not in {PointDirection.OUTPUT.value, PointDirection.INOUT.value}:
            raise CommandRejected("Команда разрешена только для OUTPUT/INOUT-точки")
        kind = str(point.data_type).casefold()
        if kind not in {"bool", "boolean", "binary", "digital", "digital output", "digital input"}:
            raise CommandRejected("START/STOP поддерживаются только для булевых точек")
        for interlock_id in interlock_point_ids or []:
            interlock = self.core.point_runtime.read(interlock_id)
            if interlock.quality != "GOOD":
                raise CommandRejected(f"Блокировка {interlock_id}: качество {interlock.quality}, требуется GOOD")
            if interlock.value is not True:
                raise CommandRejected(f"Блокировка {interlock_id}: разрешающее условие не выполнено")
        now = _now(); command_id = str(uuid4()); requested = self.ALLOWED_COMMANDS[command]
        # Simulation is intentionally an explicit safe endpoint: no driver method or
        # PointRuntime mutation is called. Real field writes remain unsupported.
        state = "SIMULATED_ACCEPTED"
        with self._db() as db:
            db.execute("INSERT INTO commands VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (command_id, station_id, point_id, actor_id, command, json.dumps(requested), state,
                        None, None, now.isoformat(), now.isoformat(), reason.strip(), lease_id, "SIMULATION_ONLY"))
        self.core.audit.append(actor_id=actor_id, action="control.command_simulated", resource_type="point",
                               resource_id=point_id, details={"command_id": command_id, "command": command,
                               "station_id": station_id, "execution_mode": "SIMULATION_ONLY"})
        return self.get(command_id)

    def confirm_simulated_feedback(self, command_id: str, *, value: bool, quality: str = "GOOD") -> dict[str, Any]:
        if quality != "GOOD":
            raise CommandRejected("Подтверждение обратной связи допускается только с качеством GOOD")
        now = _now()
        with self._db() as db:
            row = db.execute("SELECT * FROM commands WHERE command_id=?", (command_id,)).fetchone()
            if row is None:
                raise CommandRejected("Команда не найдена")
            if row["execution_mode"] != "SIMULATION_ONLY":
                raise CommandRejected("Неподдерживаемый режим исполнения")
            expected = bool(json.loads(row["requested_value"]))
            state = "SIMULATED_CONFIRMED" if value == expected else "SIMULATED_MISMATCH"
            db.execute("UPDATE commands SET feedback_value=?, feedback_quality=?, state=?, updated_at=? WHERE command_id=?",
                       (json.dumps(value), quality, state, now.isoformat(), command_id))
        self.core.audit.append(actor_id=row["actor_id"], action="control.simulated_feedback", resource_type="point",
                               resource_id=row["point_id"], details={"command_id": command_id, "state": state,
                               "feedback_quality": quality})
        return self.get(command_id)

    def get(self, command_id: str) -> dict[str, Any]:
        with self._db() as db:
            row = db.execute("SELECT * FROM commands WHERE command_id=?", (command_id,)).fetchone()
        if row is None:
            raise CommandRejected("Команда не найдена")
        return {"command_id": row["command_id"], "station_id": row["station_id"], "point_id": row["point_id"],
                "actor_id": row["actor_id"], "command": row["command"], "requested_value": json.loads(row["requested_value"]),
                "state": row["state"], "feedback_value": json.loads(row["feedback_value"]) if row["feedback_value"] is not None else None,
                "feedback_quality": row["feedback_quality"], "created_at": row["created_at"],
                "updated_at": row["updated_at"], "reason": row["reason"], "lease_id": row["lease_id"],
                "execution_mode": row["execution_mode"], "field_write_performed": False}

    def list_station(self, station_id: str, limit: int = 100) -> list[dict[str, Any]]:
        if not 1 <= limit <= 500:
            raise CommandRejected("limit должен быть от 1 до 500")
        with self._db() as db:
            ids = [r[0] for r in db.execute("SELECT command_id FROM commands WHERE station_id=? ORDER BY created_at DESC LIMIT ?", (station_id, limit))]
        return [self.get(command_id) for command_id in ids]
