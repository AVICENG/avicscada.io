from __future__ import annotations
import json
import sqlite3
from contextlib import closing, contextmanager
from dataclasses import asdict, fields, is_dataclass
from datetime import datetime
from enum import Enum
from typing import get_args, get_origin, get_type_hints, Union
from pathlib import Path
from threading import RLock
from typing import Any, Iterator
from uuid import UUID


class RepositoryError(RuntimeError):
    pass


class ConcurrencyConflict(RepositoryError):
    pass


class EntityNotFound(RepositoryError):
    pass


def _json_default(value: Any):
    if isinstance(value, datetime):
        return {"__type__": "datetime", "value": value.isoformat()}
    if isinstance(value, Enum):
        return {"__type__": "enum", "class": value.__class__.__name__, "value": value.value}
    raise TypeError(f"Unsupported repository value: {type(value).__name__}")


def _encode(entity: Any) -> str:
    if not is_dataclass(entity):
        raise TypeError("Repository accepts dataclass domain entities only")
    return json.dumps(asdict(entity), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=_json_default, allow_nan=False)


def _convert_typed(value: Any, expected_type: Any):
    if value is None:
        return None
    origin = get_origin(expected_type)
    args = get_args(expected_type)
    if origin is not None and args:
        if origin in (Union, getattr(__import__("types"), "UnionType", object)):
            for candidate in args:
                if candidate is type(None):
                    continue
                try:
                    return _convert_typed(value, candidate)
                except (TypeError, ValueError):
                    pass
            return value
        if origin is list:
            return [_convert_typed(item, args[0]) for item in value]
        if origin is dict:
            return {key: _convert_typed(item, args[1]) for key, item in value.items()}
    if expected_type is datetime:
        if isinstance(value, dict) and value.get("__type__") == "datetime":
            return datetime.fromisoformat(value["value"])
        if isinstance(value, str):
            return datetime.fromisoformat(value)
    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        return expected_type(value)
    return value


def _hydrate(payload: dict[str, Any], model_type: type):
    if not is_dataclass(model_type):
        raise TypeError("Typed hydration requires a dataclass model type")
    hints = get_type_hints(model_type)
    allowed = {item.name for item in fields(model_type) if item.init}
    values = {key: _convert_typed(value, hints.get(key, Any)) for key, value in payload.items() if key in allowed}
    return model_type(**values)


class SQLiteRepository:
    """Transactional entity registry. Domain services own reference validation and policy."""
    def __init__(self, database: str | Path):
        self.database = str(database)
        self._lock = RLock()
        Path(self.database).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("""CREATE TABLE IF NOT EXISTS entities (
                entity_id TEXT PRIMARY KEY,
                entity_type TEXT NOT NULL,
                name TEXT NOT NULL,
                project_id TEXT,
                station_id TEXT,
                version INTEGER NOT NULL,
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )""")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_entities_type ON entities(entity_type)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_entities_project ON entities(project_id)")
            connection.execute("CREATE INDEX IF NOT EXISTS idx_entities_station ON entities(station_id)")
            connection.commit()

    def _connect(self):
        connection = sqlite3.connect(self.database, timeout=15, isolation_level=None)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=15000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Explicit transaction boundary for multi-entity engineering operations."""
        with self._lock:
            connection = self._connect()
            try:
                connection.execute("BEGIN IMMEDIATE")
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise
            finally:
                connection.close()

    @staticmethod
    def _scope(entity: Any) -> tuple[str | None, str | None]:
        project_id = getattr(entity, "project_id", None) or None
        station_id = getattr(entity, "station_id", None) or None
        return project_id, station_id

    def save(self, entity: Any, *, expected_version: int | None = None, connection: sqlite3.Connection | None = None) -> int:
        entity_id = str(getattr(entity, "id", ""))
        UUID(entity_id)
        name = str(getattr(entity, "name", ""))
        if not name.strip():
            raise ValueError("Entity name cannot be empty")
        payload = _encode(entity)
        project_id, station_id = self._scope(entity)
        created = getattr(entity, "created_at").isoformat()
        updated = getattr(entity, "updated_at").isoformat()
        own_connection = connection is None
        cm = self.transaction() if own_connection else None
        if own_connection:
            connection = cm.__enter__()
        try:
            row = connection.execute("SELECT version FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
            if row is None:
                if expected_version not in (None, 0):
                    raise ConcurrencyConflict(f"Entity {entity_id} does not exist at expected version {expected_version}")
                version = 1
                connection.execute("INSERT INTO entities VALUES(?,?,?,?,?,?,?,?,?)", (
                    entity_id, entity.__class__.__name__, name, project_id, station_id,
                    version, payload, created, updated))
            else:
                stored_type = connection.execute("SELECT entity_type FROM entities WHERE entity_id=?", (entity_id,)).fetchone()[0]
                if stored_type != entity.__class__.__name__:
                    raise RepositoryError(
                        f"Entity type is immutable for {entity_id}: stored {stored_type}, received {entity.__class__.__name__}"
                    )
                current = int(row["version"])
                if expected_version is None or expected_version != current:
                    raise ConcurrencyConflict(f"Entity {entity_id} version is {current}; expected {expected_version}")
                version = current + 1
                connection.execute("UPDATE entities SET entity_type=?,name=?,project_id=?,station_id=?,version=?,payload=?,updated_at=? WHERE entity_id=?",
                    (entity.__class__.__name__, name, project_id, station_id, version, payload, updated, entity_id))
            if own_connection:
                cm.__exit__(None, None, None)
            return version
        except Exception as exc:
            if own_connection:
                cm.__exit__(type(exc), exc, exc.__traceback__)
            raise

    def get_record(self, entity_id: str, *, connection: sqlite3.Connection | None = None) -> dict[str, Any]:
        UUID(entity_id)
        if connection is None:
            with closing(self._connect()) as own_connection:
                row = own_connection.execute("SELECT * FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
        else:
            row = connection.execute("SELECT * FROM entities WHERE entity_id=?", (entity_id,)).fetchone()
        if row is None:
            raise EntityNotFound(entity_id)
        result = dict(row)
        result["payload"] = json.loads(result["payload"])
        return result

    def get(self, entity_id: str, model_type: type, *, connection: sqlite3.Connection | None = None):
        record = self.get_record(entity_id, connection=connection)
        if record["entity_type"] != model_type.__name__:
            raise TypeError(f"Stored entity is {record['entity_type']}, not {model_type.__name__}")
        return _hydrate(record["payload"], model_type), int(record["version"])

    def list_records(self, *, entity_type: str | None = None, project_id: str | None = None,
                     station_id: str | None = None, connection: sqlite3.Connection | None = None) -> list[dict[str, Any]]:
        clauses, values = [], []
        for column, value in (("entity_type", entity_type), ("project_id", project_id), ("station_id", station_id)):
            if value is not None:
                clauses.append(f"{column}=?")
                values.append(value)
        sql = "SELECT * FROM entities" + (" WHERE " + " AND ".join(clauses) if clauses else "") + " ORDER BY entity_type,name,entity_id"
        own_connection = connection is None
        if own_connection:
            connection = self._connect()
        try:
            rows = connection.execute(sql, values).fetchall()
        finally:
            if own_connection:
                connection.close()
        result = []
        for row in rows:
            item = dict(row)
            item["payload"] = json.loads(item["payload"])
            result.append(item)
        return result

    def delete(self, entity_id: str, *, expected_version: int, connection: sqlite3.Connection | None = None) -> None:
        UUID(entity_id)
        if connection is None:
            with self.transaction() as transaction:
                self.delete(entity_id, expected_version=expected_version, connection=transaction)
            return
        cursor = connection.execute("DELETE FROM entities WHERE entity_id=? AND version=?", (entity_id, expected_version))
        if cursor.rowcount != 1:
            raise ConcurrencyConflict("Entity missing or version changed; delete refused")
