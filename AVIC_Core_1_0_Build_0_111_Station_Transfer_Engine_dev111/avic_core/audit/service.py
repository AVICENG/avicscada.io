from __future__ import annotations

import hashlib
import hmac
import json
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class AuditRecord:
    event_id: str
    occurred_at: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    outcome: str
    details: dict
    previous_hash: str
    record_hash: str


class AuditService:
    """Append-only application API with a tamper-evident SHA-256 hash chain.

    Hash chaining detects modification/deletion/reordering when the latest trusted hash
    is retained externally. It does not replace OS/database ACLs or remote archival.
    """
    GENESIS = "0" * 64

    def __init__(self, database_path: str | Path):
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS audit_events (
                event_id TEXT PRIMARY KEY, occurred_at TEXT NOT NULL, actor_id TEXT NOT NULL,
                action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL,
                outcome TEXT NOT NULL, details_json TEXT NOT NULL,
                previous_hash TEXT NOT NULL DEFAULT '', record_hash TEXT NOT NULL DEFAULT '')""")
            columns = {r[1] for r in db.execute("PRAGMA table_info(audit_events)")}
            if "previous_hash" not in columns:
                db.execute("ALTER TABLE audit_events ADD COLUMN previous_hash TEXT NOT NULL DEFAULT ''")
            if "record_hash" not in columns:
                db.execute("ALTER TABLE audit_events ADD COLUMN record_hash TEXT NOT NULL DEFAULT ''")
            # Upgrade pre-chain audit rows in place, preserving their original order/content.
            rows = db.execute("SELECT event_id,occurred_at,actor_id,action,resource_type,resource_id,outcome,details_json,previous_hash,record_hash FROM audit_events ORDER BY rowid").fetchall()
            if rows and any(not row[9] for row in rows):
                previous = self.GENESIS
                for row in rows:
                    event_id, occurred, actor, action, resource_type, resource_id, outcome, details_json, _, existing_hash = row
                    details = json.loads(details_json)
                    fields = {"event_id": event_id, "occurred_at": occurred, "actor_id": actor,
                              "action": action, "resource_type": resource_type, "resource_id": resource_id,
                              "outcome": outcome, "details": details, "previous_hash": previous}
                    digest = hashlib.sha256(self._canonical(fields)).hexdigest()
                    if existing_hash and existing_hash != digest:
                        raise RuntimeError("Audit chain migration conflict; refusing to rewrite existing integrity data")
                    db.execute("UPDATE audit_events SET previous_hash=?,record_hash=? WHERE event_id=?",
                               (previous, digest, event_id))
                    previous = digest
            db.commit()

    @staticmethod
    def _canonical(fields: dict) -> bytes:
        return json.dumps(fields, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def append(self, *, actor_id: str, action: str, resource_type: str, resource_id: str,
               outcome: str = "success", details: dict | None = None) -> AuditRecord:
        if not all(isinstance(v, str) and v.strip() for v in (actor_id, action, resource_type, resource_id, outcome)):
            raise ValueError("Поля аудита не могут быть пустыми")
        occurred = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid4())
        safe_details = details or {}
        with closing(sqlite3.connect(self.path, timeout=15, isolation_level=None)) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT record_hash FROM audit_events ORDER BY rowid DESC LIMIT 1").fetchone()
            previous = row[0] if row and row[0] else self.GENESIS
            fields = {"event_id": event_id, "occurred_at": occurred, "actor_id": actor_id,
                      "action": action, "resource_type": resource_type, "resource_id": resource_id,
                      "outcome": outcome, "details": safe_details, "previous_hash": previous}
            digest = hashlib.sha256(self._canonical(fields)).hexdigest()
            db.execute("""INSERT INTO audit_events
                (event_id,occurred_at,actor_id,action,resource_type,resource_id,outcome,details_json,previous_hash,record_hash)
                VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (event_id, occurred, actor_id, action, resource_type, resource_id, outcome,
                 json.dumps(safe_details, ensure_ascii=False, sort_keys=True), previous, digest))
            db.commit()
        return AuditRecord(event_id, occurred, actor_id, action, resource_type, resource_id,
                           outcome, safe_details, previous, digest)

    def verify_chain(self) -> tuple[bool, int]:
        previous = self.GENESIS
        count = 0
        with closing(sqlite3.connect(self.path)) as db:
            rows = db.execute("""SELECT event_id,occurred_at,actor_id,action,resource_type,resource_id,
                outcome,details_json,previous_hash,record_hash FROM audit_events ORDER BY rowid""").fetchall()
        for row in rows:
            event_id, occurred, actor, action, resource_type, resource_id, outcome, details_json, prev, digest = row
            try:
                details = json.loads(details_json)
            except Exception:
                return False, count
            fields = {"event_id": event_id, "occurred_at": occurred, "actor_id": actor,
                      "action": action, "resource_type": resource_type, "resource_id": resource_id,
                      "outcome": outcome, "details": details, "previous_hash": previous}
            expected = hashlib.sha256(self._canonical(fields)).hexdigest()
            if prev != previous or not hmac.compare_digest(expected, digest):
                return False, count
            previous = digest
            count += 1
        return True, count
