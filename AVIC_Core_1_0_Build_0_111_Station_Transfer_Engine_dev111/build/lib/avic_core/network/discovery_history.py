"""Durable audit trail for explicitly requested, read-only network discovery."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class DiscoveryHistory:
    def __init__(self, path: str | Path):
        self.path = str(path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS discovery_sessions (
                session_id TEXT PRIMARY KEY, network_id TEXT NOT NULL, protocol TEXT NOT NULL,
                mode TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL,
                device_count INTEGER NOT NULL, diagnostics_json TEXT NOT NULL, devices_json TEXT NOT NULL
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_discovery_created ON discovery_sessions(created_at DESC)")

    def _db(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def record_completed(self, *, network_id: str, protocol: str, devices: list[dict], diagnostics: dict | None = None) -> dict:
        if not network_id.strip() or not protocol.strip():
            raise ValueError("network_id и protocol обязательны")
        # Store only protocol evidence returned by discovery; never credentials or arbitrary config.
        safe_devices = []
        for device in devices:
            safe_devices.append({k: device.get(k) for k in (
                "device_instance", "ip_address", "udp_port", "vendor_id", "manufacturer",
                "manufacturer_source", "model_name", "model_status", "identity_confidence",
                "max_apdu", "segmentation")})
        safe_diagnostics = {str(k): v for k, v in (diagnostics or {}).items()
                            if str(k).casefold() not in {"password", "secret", "token", "credential"}}
        item = {"session_id": str(uuid4()), "network_id": network_id, "protocol": protocol,
                "mode": "read_only", "state": "COMPLETED", "created_at": datetime.now(timezone.utc).isoformat(),
                "device_count": len(safe_devices), "diagnostics": safe_diagnostics, "devices": safe_devices,
                "write_enabled": False}
        with self._db() as db:
            db.execute("INSERT INTO discovery_sessions VALUES(?,?,?,?,?,?,?,?,?)", (
                item["session_id"], network_id, protocol, "read_only", "COMPLETED", item["created_at"],
                len(safe_devices), json.dumps(safe_diagnostics, ensure_ascii=False),
                json.dumps(safe_devices, ensure_ascii=False)))
        return item

    def list(self, limit: int = 100) -> list[dict]:
        if isinstance(limit, bool) or not 1 <= limit <= 500:
            raise ValueError("limit должен быть в диапазоне 1..500")
        with self._db() as db:
            rows = db.execute("SELECT * FROM discovery_sessions ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [{"session_id": r["session_id"], "network_id": r["network_id"], "protocol": r["protocol"],
                 "mode": r["mode"], "state": r["state"], "created_at": r["created_at"],
                 "device_count": r["device_count"], "write_enabled": False} for r in rows]

    def get(self, session_id: str) -> dict:
        with self._db() as db:
            row = db.execute("SELECT * FROM discovery_sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            raise KeyError(session_id)
        return {"session_id": row["session_id"], "network_id": row["network_id"],
                "protocol": row["protocol"], "mode": row["mode"], "state": row["state"],
                "created_at": row["created_at"], "device_count": row["device_count"],
                "diagnostics": json.loads(row["diagnostics_json"]),
                "devices": json.loads(row["devices_json"]), "write_enabled": False}
