from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .manager import MigrationError


@dataclass(frozen=True)
class MigrationPreview:
    from_version: int
    to_version: int
    before: dict
    after: dict
    changed_paths: tuple[str, ...]


@dataclass(frozen=True)
class MigrationSpec:
    migration_id: str
    from_version: int
    to_version: int
    description: str
    apply: Callable[[dict], dict]


class MigrationRegistry:
    """Explicit ordered migrations with a durable execution journal."""
    def __init__(self, journal_path: str | Path):
        self.journal_path = str(journal_path)
        Path(self.journal_path).parent.mkdir(parents=True, exist_ok=True)
        self._migrations: dict[int, MigrationSpec] = {}
        with closing(sqlite3.connect(self.journal_path)) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS migration_journal (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id TEXT NOT NULL,
                migration_id TEXT NOT NULL,
                from_version INTEGER NOT NULL,
                to_version INTEGER NOT NULL,
                executed_at TEXT NOT NULL,
                result_checksum TEXT NOT NULL
            )""")
            db.commit()

    def register(self, spec: MigrationSpec):
        if not spec.migration_id or spec.from_version < 1 or spec.to_version != spec.from_version + 1:
            raise ValueError("Migration must have an id and advance exactly one schema version")
        if spec.from_version in self._migrations:
            raise ValueError(f"Migration from schema {spec.from_version} already registered")
        self._migrations[spec.from_version] = spec

    def plan(self, from_version: int, to_version: int) -> tuple[MigrationSpec, ...]:
        if from_version > to_version:
            raise MigrationError("Downgrade migrations are not supported; use a verified backup")
        result = []
        version = from_version
        while version < to_version:
            spec = self._migrations.get(version)
            if spec is None or spec.to_version > to_version:
                raise MigrationError(f"No migration path from schema {version} to {to_version}")
            result.append(spec)
            version = spec.to_version
        return tuple(result)

    def preview(self, payload: dict, from_version: int, to_version: int) -> MigrationPreview:
        import copy
        before = copy.deepcopy(payload)
        working = copy.deepcopy(payload)
        for spec in self.plan(from_version, to_version):
            try:
                candidate = spec.apply(copy.deepcopy(working))
                if not isinstance(candidate, dict):
                    raise TypeError("Migration result must be an object")
                working = candidate
            except Exception as exc:
                raise MigrationError(f"Migration preview failed at {spec.migration_id}: {exc}") from exc
        changed = []
        def walk(left, right, prefix=""):
            if isinstance(left, dict) and isinstance(right, dict):
                for key in sorted(set(left) | set(right)):
                    path = f"{prefix}.{key}" if prefix else key
                    if key not in left or key not in right:
                        changed.append(path)
                    else:
                        walk(left[key], right[key], path)
            elif left != right:
                changed.append(prefix or "$")
        walk(before, working)
        return MigrationPreview(from_version, to_version, before, working, tuple(changed))

    def migrate_payload(self, entity_id: str, payload: dict, from_version: int, to_version: int) -> dict:
        import hashlib
        import copy
        working = copy.deepcopy(payload)
        completed = []
        for spec in self.plan(from_version, to_version):
            try:
                candidate = spec.apply(copy.deepcopy(working))
                if not isinstance(candidate, dict):
                    raise TypeError("Migration result must be an object")
                encoded = json.dumps(candidate, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
                completed.append((spec, hashlib.sha256(encoded).hexdigest()))
                working = candidate
            except Exception as exc:
                raise MigrationError(f"Migration {spec.migration_id} failed; source payload unchanged: {exc}") from exc
        # Journal only after the complete in-memory chain succeeds. The caller then
        # commits the migrated configuration as a separate atomic operation.
        with closing(sqlite3.connect(self.journal_path)) as db:
            db.execute("BEGIN IMMEDIATE")
            for spec, digest in completed:
                db.execute("INSERT INTO migration_journal(entity_id,migration_id,from_version,to_version,executed_at,result_checksum) VALUES(?,?,?,?,?,?)",
                    (entity_id, spec.migration_id, spec.from_version, spec.to_version, datetime.now(timezone.utc).isoformat(), digest))
            db.commit()
        return working

    def history(self, entity_id: str) -> list[dict]:
        with closing(sqlite3.connect(self.journal_path)) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT * FROM migration_journal WHERE entity_id=? ORDER BY id", (entity_id,)).fetchall()
        return [dict(row) for row in rows]
