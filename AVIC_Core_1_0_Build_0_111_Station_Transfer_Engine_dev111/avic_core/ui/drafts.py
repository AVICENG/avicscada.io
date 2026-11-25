from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DraftError(ValueError):
    """Base error for engineering draft operations."""


class DraftNotFound(DraftError):
    pass


class DraftConflict(DraftError):
    pass


class EngineeringDraftStore:
    """Durable, versioned working drafts kept separate from published configuration."""

    EDITORS = frozenset({"fbd", "graphics", "web-page"})
    MAX_CONTENT_BYTES = 5 * 1024 * 1024

    def __init__(self, database_path: str | Path):
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS engineering_drafts (
                    editor TEXT NOT NULL,
                    station_id TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    base_revision INTEGER NOT NULL,
                    draft_revision INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(editor, station_id, resource_id)
                )
            """)
            db.execute("""
                CREATE INDEX IF NOT EXISTS ix_engineering_drafts_station_updated
                ON engineering_drafts(station_id, updated_at DESC)
            """)

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA busy_timeout=15000")
        return db

    @classmethod
    def _validate_key(cls, editor: str, station_id: str, resource_id: str) -> None:
        if editor not in cls.EDITORS:
            raise DraftError("Unsupported engineering editor")
        if not isinstance(station_id, str) or not station_id.strip() or len(station_id) > 128:
            raise DraftError("station_id is required")
        if not isinstance(resource_id, str) or not resource_id.strip() or len(resource_id) > 128:
            raise DraftError("resource_id is required")

    @classmethod
    def _encode_content(cls, content: dict[str, Any]) -> str:
        if not isinstance(content, dict):
            raise DraftError("Draft content must be a JSON object")
        try:
            encoded = json.dumps(content, ensure_ascii=False, sort_keys=True,
                                 separators=(",", ":"), allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise DraftError("Draft content must contain finite JSON values only") from exc
        if len(encoded.encode("utf-8")) > cls.MAX_CONTENT_BYTES:
            raise DraftError("Draft exceeds the 5 MiB limit")
        return encoded

    @staticmethod
    def _serialize(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "editor": row["editor"],
            "station_id": row["station_id"],
            "resource_id": row["resource_id"],
            "content": json.loads(row["content_json"]),
            "base_revision": row["base_revision"],
            "draft_revision": row["draft_revision"],
            "updated_at": row["updated_at"],
        }

    def save(self, editor: str, station_id: str, resource_id: str, *,
             content: dict[str, Any], base_revision: int,
             expected_draft_revision: int) -> dict[str, Any]:
        self._validate_key(editor, station_id, resource_id)
        if isinstance(base_revision, bool) or not isinstance(base_revision, int) or base_revision < 0:
            raise DraftError("base_revision must be a non-negative integer")
        if (isinstance(expected_draft_revision, bool)
                or not isinstance(expected_draft_revision, int)
                or expected_draft_revision < 0):
            raise DraftError("expected_draft_revision must be a non-negative integer")
        encoded = self._encode_content(content)
        now = datetime.now(timezone.utc).isoformat()
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            current = db.execute(
                "SELECT * FROM engineering_drafts WHERE editor=? AND station_id=? AND resource_id=?",
                (editor, station_id, resource_id),
            ).fetchone()
            actual = int(current["draft_revision"]) if current else 0
            if actual != expected_draft_revision:
                raise DraftConflict(
                    f"Draft revision conflict: expected {expected_draft_revision}, current {actual}"
                )
            revision = actual + 1
            if current:
                db.execute(
                    """UPDATE engineering_drafts
                       SET content_json=?, base_revision=?, draft_revision=?, updated_at=?
                       WHERE editor=? AND station_id=? AND resource_id=?""",
                    (encoded, base_revision, revision, now, editor, station_id, resource_id),
                )
            else:
                db.execute(
                    """INSERT INTO engineering_drafts
                       (editor,station_id,resource_id,content_json,base_revision,draft_revision,updated_at)
                       VALUES(?,?,?,?,?,?,?)""",
                    (editor, station_id, resource_id, encoded, base_revision, revision, now),
                )
            row = db.execute(
                "SELECT * FROM engineering_drafts WHERE editor=? AND station_id=? AND resource_id=?",
                (editor, station_id, resource_id),
            ).fetchone()
            db.commit()
            return self._serialize(row)

    def get(self, editor: str, station_id: str, resource_id: str) -> dict[str, Any]:
        self._validate_key(editor, station_id, resource_id)
        with closing(self._connect()) as db:
            row = db.execute(
                "SELECT * FROM engineering_drafts WHERE editor=? AND station_id=? AND resource_id=?",
                (editor, station_id, resource_id),
            ).fetchone()
        if row is None:
            raise DraftNotFound("Engineering draft not found")
        return self._serialize(row)

    def list_station(self, station_id: str) -> list[dict[str, Any]]:
        if not isinstance(station_id, str) or not station_id.strip() or len(station_id) > 128:
            raise DraftError("station_id is required")
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT * FROM engineering_drafts WHERE station_id=? ORDER BY updated_at DESC",
                (station_id,),
            ).fetchall()
        return [self._serialize(row) for row in rows]

    def delete(self, editor: str, station_id: str, resource_id: str, *,
               expected_draft_revision: int) -> bool:
        self._validate_key(editor, station_id, resource_id)
        if (isinstance(expected_draft_revision, bool)
                or not isinstance(expected_draft_revision, int)
                or expected_draft_revision < 1):
            raise DraftError("expected_draft_revision must be a positive integer")
        with closing(self._connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT draft_revision FROM engineering_drafts WHERE editor=? AND station_id=? AND resource_id=?",
                (editor, station_id, resource_id),
            ).fetchone()
            if row is None:
                db.commit()
                return False
            if int(row["draft_revision"]) != expected_draft_revision:
                raise DraftConflict(
                    f"Draft revision conflict: expected {expected_draft_revision}, current {row['draft_revision']}"
                )
            db.execute(
                "DELETE FROM engineering_drafts WHERE editor=? AND station_id=? AND resource_id=?",
                (editor, station_id, resource_id),
            )
            db.commit()
        return True
