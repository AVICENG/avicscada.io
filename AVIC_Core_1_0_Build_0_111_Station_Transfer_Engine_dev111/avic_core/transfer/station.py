from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from uuid import uuid4, uuid5, NAMESPACE_URL

from avic_core.repository.sqlite_repository import RepositoryError


class StationTransferError(RuntimeError):
    """Raised when a Station package cannot be safely exported or imported."""


@dataclass(frozen=True)
class StationTransferPreview:
    package_id: str
    station_id: str
    station_name: str
    source_project_id: str
    source_core_version: str
    entity_count: int
    auxiliary_record_count: int
    compatible: bool
    warnings: tuple[str, ...] = ()


class StationTransferManager:
    """Station-scoped engineering transfer. Runtime history and secrets are excluded.

    The package preserves engineering object IDs. A target Project is selected at
    import time; the Station's parent project reference is rebound to that target.
    Only explicitly allow-listed auxiliary tables are transferred.
    """

    FORMAT = "AVIC_STATION_PACKAGE"
    FORMAT_VERSION = 1
    MANIFEST = "avic-station.json"
    PAYLOAD = "payload/station.json"
    MAX_PACKAGE_BYTES = 512 * 1024 * 1024
    MAX_ENTITIES = 100_000
    MAX_AUX_ROWS = 500_000

    # Engineering configuration only. Operational journals and runtime state are
    # deliberately not included in a Station Copier package.
    AUX_TABLES = {
        "custom_svg": {"custom_svg_assets": ("station_id",)},
        "dependencies": {"dependencies": ("station_id",)},
        "time_management": {
            "station_time_policy": ("station_id",),
            "device_time_permission": ("station_id",),
        },
        "schedules": {"schedules": ("station_id",)},
        "analytics": {
            "point_tags": ("point_id",),
            "point_hierarchy": ("point_id",),
        },
    }
    SCHEDULE_CHILDREN = ("weekly_events", "special_events", "schedule_bindings")
    EXCLUDED_DATABASES = (
        "history.sqlite3", "events.sqlite3", "alarms.sqlite3", "audit.sqlite3",
        "notifications.sqlite3", "point_views.sqlite3", "engineering_lifecycle.sqlite3",
    )
    EXCLUDED_ENTITY_TYPES = {"Event", "HistoryRecord"}
    REFERENCE_PARENT_FIELDS = {
        "GraphicElement": ("document_id",),
        "PointBinding": ("element_id",),
        "LogicGraphicsBinding": ("graphic_element_id", "logic_node_id"),
        "LogicNode": ("document_id",),
        "LogicLink": ("document_id",),
        "StrategyPage": ("document_id",),
        "StrategyConnective": ("document_id",),
        "PropertyDefinition": ("owner_object_id",),
    }

    @staticmethod
    def _json_value(value: Any) -> Any:
        if isinstance(value, bytes):
            return {"__avic_binary__": base64.b64encode(value).decode("ascii")}
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        raise StationTransferError(f"Unsupported SQLite value type: {type(value).__name__}")

    @staticmethod
    def _from_json_value(value: Any) -> Any:
        if isinstance(value, dict) and set(value) == {"__avic_binary__"}:
            try:
                return base64.b64decode(value["__avic_binary__"], validate=True)
            except Exception as exc:
                raise StationTransferError("Invalid binary field encoding") from exc
        if isinstance(value, dict) or isinstance(value, list):
            raise StationTransferError("Unexpected nested SQLite field value")
        return value

    @staticmethod
    def _connect(path: Path) -> sqlite3.Connection:
        if not path.is_file():
            raise StationTransferError(f"Required Core database is missing: {path.name}")
        db = sqlite3.connect(str(path), timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA busy_timeout=20000")
        return db

    @staticmethod
    def _table_exists(db: sqlite3.Connection, table: str) -> bool:
        return db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

    @classmethod
    def _table_columns(cls, db: sqlite3.Connection, table: str) -> set[str]:
        return {row[1] for row in db.execute(f'PRAGMA table_info("{table}")')}

    @classmethod
    def _read_auxiliary(cls, core, station_id: str, point_ids: set[str]) -> dict[str, dict[str, list[dict[str, Any]]]]:
        result: dict[str, dict[str, list[dict[str, Any]]]] = {}
        total = 0
        for db_key, tables in cls.AUX_TABLES.items():
            db_path = core.paths.databases / f"{db_key if db_key != 'custom_svg' else 'custom_svg_library'}.sqlite3"
            if not db_path.exists():
                continue
            with cls._connect(db_path) as db:
                selected: dict[str, list[dict[str, Any]]] = {}
                db.execute("BEGIN")  # one consistent read snapshot per auxiliary database
                for table, scope_columns in tables.items():
                    if not cls._table_exists(db, table):
                        continue
                    columns = cls._table_columns(db, table)
                    scope_column = scope_columns[0]
                    if scope_column not in columns:
                        continue
                    if scope_column == "station_id":
                        rows = db.execute(f'SELECT * FROM "{table}" WHERE "{scope_column}"=?', (station_id,)).fetchall()
                    else:
                        if not point_ids:
                            rows = []
                        else:
                            placeholders = ",".join("?" for _ in point_ids)
                            rows = db.execute(f'SELECT * FROM "{table}" WHERE "{scope_column}" IN ({placeholders})', tuple(sorted(point_ids))).fetchall()
                    selected[table] = [{k: cls._json_value(row[k]) for k in row.keys()} for row in rows]
                    total += len(rows)
                if db_key == "schedules" and "schedules" in selected and cls._table_exists(db, "schedules"):
                    schedule_ids = [r["schedule_id"] for r in selected["schedules"]]
                    for child in cls.SCHEDULE_CHILDREN:
                        if not cls._table_exists(db, child):
                            continue
                        if schedule_ids:
                            placeholders = ",".join("?" for _ in schedule_ids)
                            rows = db.execute(f'SELECT * FROM "{child}" WHERE schedule_id IN ({placeholders})', tuple(schedule_ids)).fetchall()
                        else:
                            rows = []
                        selected[child] = [{k: cls._json_value(row[k]) for k in row.keys()} for row in rows]
                        total += len(rows)
                if selected:
                    result[db_key] = selected
        if total > cls.MAX_AUX_ROWS:
            raise StationTransferError("Station contains too many auxiliary configuration records")
        return result

    @staticmethod
    def _resolve_entities(core, station_id: str) -> tuple[dict[str, Any], list[dict[str, Any]], set[str]]:
        try:
            station = core.repository.get_record(station_id)
        except Exception as exc:
            raise StationTransferError("Station does not exist in this Core") from exc
        if station["entity_type"] != "Station":
            raise StationTransferError("Selected object is not a Station")
        records = core.repository.list_records()
        selected: dict[str, dict[str, Any]] = {station_id: station}
        # Repository station_id covers most engineering objects. Points are linked
        # through Device and therefore need explicit reference resolution.
        for row in records:
            if row["entity_id"] == station_id:
                continue
            if row["entity_type"] in StationTransferManager.EXCLUDED_ENTITY_TYPES:
                continue
            if row.get("station_id") == station_id or row["payload"].get("station_id") == station_id:
                selected[row["entity_id"]] = row
        changed = True
        while changed:
            changed = False
            device_ids = {rid for rid, row in selected.items() if row["entity_type"] == "Device"}
            for row in records:
                if row["entity_id"] in selected:
                    continue
                payload = row["payload"]
                parent_fields = StationTransferManager.REFERENCE_PARENT_FIELDS.get(row["entity_type"], ())
                reference_child = bool(parent_fields) and all(payload.get(field) in selected for field in parent_fields)
                if ((row["entity_type"] == "Point" and payload.get("device_id") in device_ids)
                        or reference_child):
                    selected[row["entity_id"]] = row
                    changed = True
        if len(selected) > StationTransferManager.MAX_ENTITIES:
            raise StationTransferError("Station contains too many engineering entities")
        entity_ids = set(selected)
        # Refuse dangling references inside the selected station graph. External
        # references are recorded as blockers rather than silently copied.
        warnings: list[str] = []
        for row in selected.values():
            payload = row["payload"]
            if row["entity_type"] == "Station":
                continue
            if row["entity_type"] == "Point" and payload.get("device_id") not in entity_ids:
                raise StationTransferError(f"Point {row['entity_id']} references a Device outside the transfer scope")
            if row["entity_type"] in {"Device", "ProtocolChannel"} and payload.get("network_id") and payload["network_id"] not in entity_ids:
                raise StationTransferError(f"{row['entity_type']} {row['entity_id']} references a network outside the transfer scope")
            for key in ("source_object_id", "target_object_id", "owner_object_id"):
                ref = payload.get(key)
                if ref and ref not in entity_ids:
                    warnings.append(f"External reference {key}={ref} on {row['entity_type']} {row['entity_id']}")
        # Project is intentionally not embedded: import selects a target Project.
        return station, sorted(selected.values(), key=lambda r: (r["entity_type"], r["entity_id"])), entity_ids

    @classmethod
    def _sanitize_configuration(cls, value: Any, key: str = "") -> Any:
        """Remove target-site endpoints and credentials without guessing field semantics."""
        lowered = key.casefold()
        if lowered == "addressing_mode":
            return value
        sensitive_exact = {"password", "passwd", "secret", "token", "credential", "private_key", "keyring",
                           "hostname", "host", "ip", "ip_address", "ipv4", "subnet", "gateway", "dns",
                           "mac_address", "interface_id", "interface_name", "port", "tcp_port", "udp_port",
                           "bacnet_port", "modbus_port", "username", "address", "endpoint", "url",
                           "community", "auth", "authorization", "device_instance"}
        sensitive_suffixes = ("_password", "_passwd", "_secret", "_token", "_credential", "_private_key",
                              "_hostname", "_host", "_ip", "_ip_address", "_ipv4", "_subnet", "_gateway",
                              "_dns", "_mac_address", "_interface_id", "_interface_name", "_address",
                              "_endpoint", "_url", "_username", "_community")
        if lowered in sensitive_exact or lowered.endswith(sensitive_suffixes):
            if isinstance(value, bool): return False
            if isinstance(value, (int, float)): return None
            if isinstance(value, list): return []
            if isinstance(value, dict): return {}
            return ""
        if isinstance(value, dict):
            return {str(k): cls._sanitize_configuration(v, str(k)) for k, v in value.items()}
        if isinstance(value, list):
            return [cls._sanitize_configuration(v, key) for v in value]
        return value

    @classmethod
    def _assert_no_inline_secrets(cls, value: Any, path: str = "payload") -> None:
        credential_patterns = (
            re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.I),
            re.compile(r"(?:password|passwd|api[_-]?key|client[_-]?secret|access[_-]?token)\s*[:=]\s*['\"]?[^'\"\s]{6,}", re.I),
            re.compile(r"authorization\s*:\s*bearer\s+[A-Za-z0-9._~+/-]{12,}", re.I),
            re.compile(r"https?://[^/\s:@]+:[^/\s@]+@", re.I),
        )
        private_ip = re.compile(r"(?<![0-9])(?:10\.(?:[0-9]{1,3}\.){2}[0-9]{1,3}|192\.168\.(?:[0-9]{1,3}\.)[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.(?:[0-9]{1,3}\.)[0-9]{1,3}|169\.254\.(?:[0-9]{1,3}\.)[0-9]{1,3})(?![0-9])")
        if isinstance(value, str):
            if any(pattern.search(value) for pattern in credential_patterns) or private_ip.search(value):
                raise StationTransferError(f"Potential credential or site endpoint remains in free-text field: {path}")
        elif isinstance(value, dict):
            for key, child in value.items():
                cls._assert_no_inline_secrets(child, f"{path}.{key}")
        elif isinstance(value, list):
            for index, child in enumerate(value):
                cls._assert_no_inline_secrets(child, f"{path}[{index}]")

    @classmethod
    def _sanitize_auxiliary(cls, auxiliary: dict[str, dict[str, list[dict[str, Any]]]]) -> None:
        """Re-provision site-specific time/network permissions at the target."""
        for row in auxiliary.get("time_management", {}).get("station_time_policy", []):
            row["ntp_enabled"] = 0
            row["ntp_servers_json"] = "[]"
        for row in auxiliary.get("time_management", {}).get("device_time_permission", []):
            row["allowed"] = 0
            row["approved_by"] = ""
            row["reason"] = "Requires explicit re-approval on the target installation"
        for row in auxiliary.get("dependencies", {}).get("dependencies", []):
            raw = row.get("metadata_json")
            if isinstance(raw, str):
                try:
                    row["metadata_json"] = json.dumps(cls._sanitize_configuration(json.loads(raw)), ensure_ascii=False, sort_keys=True)
                except json.JSONDecodeError as exc:
                    raise StationTransferError("Dependency metadata contains invalid JSON") from exc
        for row in auxiliary.get("analytics", {}).get("point_hierarchy", []):
            raw = row.get("metadata_json")
            if isinstance(raw, str):
                try:
                    row["metadata_json"] = json.dumps(cls._sanitize_configuration(json.loads(raw)), ensure_ascii=False, sort_keys=True)
                except json.JSONDecodeError as exc:
                    raise StationTransferError("Point hierarchy metadata contains invalid JSON") from exc

    @classmethod
    def _sanitize_records(cls, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for original in records:
            row = json.loads(json.dumps(original, ensure_ascii=False))
            payload = row["payload"]
            kind = row["entity_type"]
            if kind == "Device":
                payload["address"] = ""
                payload["native_identity"] = ""
            elif kind == "PhysicalNetwork":
                for field in ("interface_id", "interface_name", "ipv4", "subnet_cidr", "station_ipv4", "gateway_ipv4"):
                    if field in payload: payload[field] = ""
                if "dns_servers" in payload: payload["dns_servers"] = []
                if "addressing_mode" in payload: payload["addressing_mode"] = "auto"
            elif kind == "ProtocolChannel":
                payload["enabled"] = False
                payload["mode"] = "read_only"
            elif kind == "DriverInstance":
                payload["configuration"] = cls._sanitize_configuration(payload.get("configuration", {}))
                payload["state"] = "STOPPED"
            elif kind == "RuntimeInstance":
                payload["state"] = "STOPPED"
                payload["generation"] = 0
                payload["worker_id"] = None
            elif kind == "Point":
                payload["value"] = None
                payload["quality"] = "UNCERTAIN"
                payload["timestamp"] = None
                payload["source_ref"] = ""
            elif kind == "Alarm":
                payload["state"] = "NORMAL"
                payload["acknowledged_by"] = None
                payload["acknowledged_at"] = None
            row["payload"] = cls._sanitize_configuration(payload)
            result.append(row)
        return result

    @staticmethod
    def _validate_engineering_references(records: list[dict[str, Any]], auxiliary: dict[str, Any]) -> None:
        by_id = {row["entity_id"]: row for row in records}

        def require(ref: Any, expected: set[str], context: str) -> None:
            found = by_id.get(str(ref)) if ref else None
            if found is None or found.get("entity_type") not in expected:
                raise StationTransferError(f"Broken engineering reference {context}: expected {', '.join(sorted(expected))}")

        schedule_ids = {row.get("schedule_id") for row in auxiliary.get("schedules", {}).get("schedules", [])}
        custom_svg_ids = {row.get("symbol_id") for row in auxiliary.get("custom_svg", {}).get("custom_svg_assets", [])}
        for row in records:
            p = row["payload"]
            kind = row["entity_type"]
            if kind == "GraphicElement":
                require(p.get("document_id"), {"GraphicDocument"}, f"GraphicElement {row['entity_id']}.document_id")
                symbol = p.get("symbol_key", "")
                if isinstance(symbol, str) and symbol.startswith("custom_") and symbol not in custom_svg_ids:
                    raise StationTransferError(f"GraphicElement {row['entity_id']} references missing custom SVG {symbol}")
            elif kind == "PointBinding":
                require(p.get("element_id"), {"GraphicElement"}, f"PointBinding {row['entity_id']}.element_id")
                require(p.get("point_id"), {"Point", "FBDExposedPoint"}, f"PointBinding {row['entity_id']}.point_id")
            elif kind == "LogicGraphicsBinding":
                require(p.get("graphic_element_id"), {"GraphicElement"}, f"LogicGraphicsBinding {row['entity_id']}.graphic_element_id")
                require(p.get("logic_node_id"), {"LogicNode"}, f"LogicGraphicsBinding {row['entity_id']}.logic_node_id")
            elif kind == "LogicNode":
                require(p.get("document_id"), {"LogicDocument"}, f"LogicNode {row['entity_id']}.document_id")
                if p.get("page_id"):
                    require(p["page_id"], {"StrategyPage"}, f"LogicNode {row['entity_id']}.page_id")
                schedule_id = (p.get("params") or {}).get("schedule_id")
                if schedule_id and schedule_id not in schedule_ids:
                    raise StationTransferError(f"LogicNode {row['entity_id']} references a schedule outside the transfer")
            elif kind == "LogicLink":
                require(p.get("document_id"), {"LogicDocument"}, f"LogicLink {row['entity_id']}.document_id")
                require(p.get("source_node_id"), {"LogicNode"}, f"LogicLink {row['entity_id']}.source_node_id")
                require(p.get("target_node_id"), {"LogicNode"}, f"LogicLink {row['entity_id']}.target_node_id")
            elif kind == "StrategyPage":
                require(p.get("document_id"), {"LogicDocument"}, f"StrategyPage {row['entity_id']}.document_id")
            elif kind == "StrategyConnective":
                require(p.get("document_id"), {"LogicDocument"}, f"StrategyConnective {row['entity_id']}.document_id")
                for field in ("source_page_id", "target_page_id"):
                    require(p.get(field), {"StrategyPage"}, f"StrategyConnective {row['entity_id']}.{field}")
                for field in ("source_node_id", "target_node_id"):
                    require(p.get(field), {"LogicNode"}, f"StrategyConnective {row['entity_id']}.{field}")
            elif kind == "WebPageNode":
                if p.get("parent_id"):
                    require(p["parent_id"], {"WebPageNode"}, f"WebPageNode {row['entity_id']}.parent_id")
                for graphic_id in p.get("graphic_ids", []):
                    require(graphic_id, {"GraphicDocument"}, f"WebPageNode {row['entity_id']}.graphic_ids")
            elif kind == "FBDExposedPoint":
                if p.get("fbd_document_id"):
                    require(p["fbd_document_id"], {"LogicDocument"}, f"FBDExposedPoint {row['entity_id']}.fbd_document_id")
                if p.get("studio_document_id"):
                    require(p["studio_document_id"], {"FBDStudioDocument"}, f"FBDExposedPoint {row['entity_id']}.studio_document_id")

    def export_station(self, core, station_id: str, package_path: str | Path, *, source_core_version: str) -> Path:
        with core._lock:
            core._ensure_open()
            station, records, entity_ids = self._resolve_entities(core, station_id)
            point_ids = {r["entity_id"] for r in records if r["entity_type"] == "Point"}
            auxiliary = self._read_auxiliary(core, station_id, point_ids)
            self._sanitize_auxiliary(auxiliary)
            for edge in auxiliary.get("dependencies", {}).get("dependencies", []):
                if edge.get("dependent_id") not in entity_ids or edge.get("dependency_id") not in entity_ids:
                    raise StationTransferError("Station dependency graph contains an external object reference")
            for permission in auxiliary.get("time_management", {}).get("device_time_permission", []):
                if permission.get("device_id") not in entity_ids:
                    raise StationTransferError("Device time permission references a device outside the Station")
            for binding in auxiliary.get("schedules", {}).get("schedule_bindings", []):
                if binding.get("point_id") not in point_ids:
                    raise StationTransferError("Schedule binding references a point outside the Station")
            self._validate_engineering_references(records, auxiliary)
            project_id = station["payload"].get("project_id")
            safe_records = self._sanitize_records(records)
            payload = {
                "station": next(r for r in safe_records if r["entity_type"] == "Station"),
                "entities": safe_records,
                "auxiliary": auxiliary,
                "transfer_policy": {
                    "preserve_object_ids": True,
                    "target_site_binding_required": True,
                    "runtime_history_included": False,
                    "secrets_included": False,
                },
            }
            self._assert_no_inline_secrets(payload)
            payload_bytes = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
            if len(payload_bytes) > self.MAX_PACKAGE_BYTES:
                raise StationTransferError("Station package exceeds maximum uncompressed size")
            manifest = {
                "format": self.FORMAT,
                "format_version": self.FORMAT_VERSION,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "station": {"id": station_id, "name": station["name"], "source_project_id": project_id},
                "source_core_version": source_core_version,
                "entity_count": len(records),
                "auxiliary_record_count": sum(len(rows) for db in auxiliary.values() for rows in db.values()),
                "payload": {"path": self.PAYLOAD, "size": len(payload_bytes), "sha256": hashlib.sha256(payload_bytes).hexdigest()},
                "excluded": {
                    "structured_secrets": "known structured fields scrubbed; free-text scan enforced",
                    "site_credentials": True,
                    "runtime_history": True, "event_journal": True,
                    "audit_log": True, "notification_outbox": True,
                    "point_favorites": True,
                },
                "security": {"integrity": "SHA-256", "authenticity": "unsigned; publisher signature not implemented"},
            }
            output = Path(package_path).expanduser().resolve()
            if output == core.paths.root or core.paths.root in output.parents:
                raise StationTransferError("Station package must be outside the Core data directory")
            output.parent.mkdir(parents=True, exist_ok=True)
            fd, tmp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
            os.close(fd)
            try:
                with zipfile.ZipFile(tmp_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
                    zf.writestr(self.MANIFEST, json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
                    zf.writestr(self.PAYLOAD, payload_bytes)
                self.inspect_package(tmp_name)
                os.replace(tmp_name, output)
            finally:
                if os.path.exists(tmp_name):
                    os.unlink(tmp_name)
            core.events.record("station.exported", f"Station package created: {station['name']}", station_id=station_id, severity="NOTICE", details={"package": output.name, "entity_count": len(records)})
            core.audit.append(actor_id="system", action="station.exported", resource_type="station", resource_id=station_id, details={"package": output.name, "entity_count": len(records)})
            return output

    def _read_package(self, package_path: str | Path) -> tuple[dict[str, Any], dict[str, Any], str]:
        path = Path(package_path)
        if not path.is_file() or path.stat().st_size > self.MAX_PACKAGE_BYTES:
            raise StationTransferError("Station package is missing or exceeds size limit")
        try:
            with zipfile.ZipFile(path, "r") as zf:
                infos = zf.infolist()
                names = [i.filename for i in infos]
                if len(names) != 2 or len(set(names)) != 2 or set(names) != {self.MANIFEST, self.PAYLOAD}:
                    raise StationTransferError("Station package must contain exactly one manifest and one payload")
                for info in infos:
                    if info.file_size > self.MAX_PACKAGE_BYTES or info.compress_size > self.MAX_PACKAGE_BYTES:
                        raise StationTransferError("Station package entry exceeds size limit")
                    if info.filename.startswith("/") or ".." in PurePosixPath(info.filename).parts or "\\" in info.filename:
                        raise StationTransferError("Unsafe path in Station package")
                    mode = (info.external_attr >> 16) & 0o170000
                    if mode == 0o120000:
                        raise StationTransferError("Symbolic links are forbidden in Station packages")
                if zf.getinfo(self.MANIFEST).file_size > 8 * 1024 * 1024:
                    raise StationTransferError("Station manifest exceeds size limit")
                if sum(info.file_size for info in infos) > self.MAX_PACKAGE_BYTES:
                    raise StationTransferError("Station package uncompressed size exceeds limit")
                manifest = json.loads(zf.read(self.MANIFEST))
                if not isinstance(manifest, dict):
                    raise StationTransferError("Station manifest must be a JSON object")
                if manifest.get("format") != self.FORMAT or manifest.get("format_version") != self.FORMAT_VERSION:
                    raise StationTransferError("Unsupported Station package format")
                payload_meta = manifest.get("payload", {})
                if not isinstance(payload_meta, dict) or payload_meta.get("path") != self.PAYLOAD:
                    raise StationTransferError("Station payload path metadata is inconsistent")
                raw = zf.read(self.PAYLOAD)
                if len(raw) != payload_meta.get("size") or hashlib.sha256(raw).hexdigest() != payload_meta.get("sha256"):
                    raise StationTransferError("Station package integrity check failed")
                payload = json.loads(raw)
                if not isinstance(payload, dict):
                    raise StationTransferError("Station payload must be a JSON object")
                package_id = hashlib.sha256(path.read_bytes()).hexdigest()[:24]
                return manifest, payload, package_id
        except (OSError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            raise StationTransferError("Station package is invalid or unreadable") from exc

    def inspect_package(self, package_path: str | Path, *, target_core_version: str | None = None) -> StationTransferPreview:
        manifest, payload, package_id = self._read_package(package_path)
        station_meta = manifest.get("station", {})
        if not isinstance(station_meta, dict):
            raise StationTransferError("Station metadata must be an object")
        if not isinstance(payload.get("entities"), list) or not payload["entities"]:
            raise StationTransferError("Station package has no engineering entities")
        if any(not isinstance(row, dict) for row in payload["entities"]):
            raise StationTransferError("Station entity records must be objects")
        entity_ids = [str(row.get("entity_id", "")) for row in payload["entities"]]
        if any(not item for item in entity_ids) or len(entity_ids) != len(set(entity_ids)):
            raise StationTransferError("Station package contains missing or duplicate entity IDs")
        if len(payload["entities"]) != manifest.get("entity_count"):
            raise StationTransferError("Station entity count does not match manifest")
        auxiliary = payload.get("auxiliary", {})
        if not isinstance(auxiliary, dict):
            raise StationTransferError("Station auxiliary data must be an object")
        auxiliary_count = sum(len(rows) for db in auxiliary.values() if isinstance(db, dict)
                              for rows in db.values() if isinstance(rows, list))
        if auxiliary_count != manifest.get("auxiliary_record_count"):
            raise StationTransferError("Station auxiliary record count does not match manifest")
        station_rows = [r for r in payload["entities"] if r.get("entity_type") == "Station"]
        if len(station_rows) != 1 or station_rows[0].get("entity_id") != station_meta.get("id"):
            raise StationTransferError("Station root identity is inconsistent")
        warnings: list[str] = []
        compatible = True
        if target_core_version and target_core_version != manifest.get("source_core_version"):
            compatible = False
            warnings.append("Core version differs; explicit migration rules are required")
        if manifest.get("security", {}).get("authenticity") != "unsigned; publisher signature not implemented":
            warnings.append("Package authenticity metadata is not recognized")
        if not payload.get("transfer_policy", {}).get("target_site_binding_required"):
            raise StationTransferError("Station package does not require target-site binding")
        return StationTransferPreview(
            package_id=package_id, station_id=str(station_meta.get("id", "")),
            station_name=str(station_meta.get("name", "")),
            source_project_id=str(station_meta.get("source_project_id", "")),
            source_core_version=str(manifest.get("source_core_version", "")),
            entity_count=len(payload["entities"]),
            auxiliary_record_count=int(manifest.get("auxiliary_record_count", 0)),
            compatible=compatible, warnings=tuple(warnings),
        )

    def stage_import(self, package_path: str | Path, staging_root: str | Path, *, expected_package_id: str,
                     target_core_version: str) -> Path:
        preview = self.inspect_package(package_path, target_core_version=target_core_version)
        if preview.package_id != expected_package_id:
            raise StationTransferError("Station package changed after preview; staging cancelled")
        if not preview.compatible:
            raise StationTransferError("Station package is incompatible: " + "; ".join(preview.warnings))
        manifest, payload, package_id = self._read_package(package_path)
        root = Path(staging_root).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        stage = root / f"{preview.station_id}.{package_id}.staged"
        if stage.exists():
            raise StationTransferError("This Station package is already staged")
        temp = Path(tempfile.mkdtemp(prefix=stage.name + ".", dir=str(root)))
        try:
            (temp / "station.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8")
            payload_digest = hashlib.sha256((temp / "station.json").read_bytes()).hexdigest()
            (temp / "stage.json").write_text(json.dumps({"package_id": package_id, "payload_sha256": payload_digest,
                "station_id": preview.station_id, "staged_at": datetime.now(timezone.utc).isoformat(),
                "state": "STAGED_NOT_ACTIVATED"}, indent=2), encoding="utf-8")
            os.replace(temp, stage)
            return stage
        finally:
            if temp.exists():
                shutil.rmtree(temp, ignore_errors=True)

    @staticmethod
    def _ensure_outbox(core) -> None:
        """Create the durable journal-delivery outbox in the entity database."""
        with sqlite3.connect(str(core.repository.database), timeout=20) as db:
            db.execute("PRAGMA busy_timeout=20000")
            db.execute("""CREATE TABLE IF NOT EXISTS station_transfer_outbox (
                operation_id TEXT PRIMARY KEY,
                station_id TEXT NOT NULL,
                station_name TEXT NOT NULL,
                target_project_id TEXT NOT NULL,
                actor_id TEXT NOT NULL,
                entity_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                status TEXT NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                audit_event_id TEXT NOT NULL UNIQUE,
                last_error TEXT
            )""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_station_transfer_outbox_status ON station_transfer_outbox(status, created_at)")

    def _deliver_outbox(self, core, operation_id: str, *, allow_prepared: bool = False) -> bool:
        """Deliver event and audit records idempotently; retain the row until both succeed."""
        with sqlite3.connect(str(core.repository.database), timeout=20) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM station_transfer_outbox WHERE operation_id=?", (operation_id,)).fetchone()
        if row is None:
            return False
        if row["status"] == "COMPLETE":
            return True
        if row["status"] == "PREPARED" and not allow_prepared:
            return False
        details = {"operation_id": operation_id, "target_project_id": row["target_project_id"],
                   "entity_count": row["entity_count"], "activation": "NOT_ACTIVATED"}
        try:
            core.events.record(
                "station.imported", f"Station imported: {row['station_name']}",
                station_id=row["station_id"], severity="NOTICE", actor_id=row["actor_id"],
                details=details, event_id=row["event_id"],
            )
            core.audit.append(
                actor_id=row["actor_id"], action="station.imported", resource_type="station",
                resource_id=row["station_id"], details=details,
                event_id=row["audit_event_id"], occurred_at=row["created_at"],
            )
            with core.repository.transaction() as conn:
                conn.execute("UPDATE station_transfer_outbox SET status='COMPLETE', last_error=NULL WHERE operation_id=?",
                             (operation_id,))
            return True
        except Exception as exc:
            try:
                with core.repository.transaction() as conn:
                    conn.execute("UPDATE station_transfer_outbox SET status='JOURNAL_PENDING', last_error=? WHERE operation_id=?",
                                 (f"{type(exc).__name__}: {exc}"[:2000], operation_id))
            except Exception:
                # The durable PREPARED/JOURNAL_PENDING row remains available for startup recovery.
                pass
            return False

    def recover_pending(self, core) -> dict[str, int]:
        """Retry committed journal deliveries; flag crash-interrupted imports for reconciliation."""
        self._ensure_outbox(core)
        with sqlite3.connect(str(core.repository.database), timeout=20) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT operation_id,status FROM station_transfer_outbox WHERE status!='COMPLETE' ORDER BY created_at").fetchall()
        recovered = 0
        pending = 0
        reconciliation = 0
        for row in rows:
            if row["status"] == "PREPARED":
                # PREPARED means the process stopped before it could certify that every
                # auxiliary database committed. Never publish a success event for this state.
                with core.repository.transaction() as conn:
                    conn.execute("UPDATE station_transfer_outbox SET status='NEEDS_RECONCILIATION', last_error=? WHERE operation_id=?",
                                 ("Process stopped before auxiliary-store commit was confirmed; inspect imported rows.", row["operation_id"]))
                reconciliation += 1
            elif row["status"] == "JOURNAL_PENDING":
                if self._deliver_outbox(core, row["operation_id"]):
                    recovered += 1
                else:
                    pending += 1
        return {"recovered": recovered, "pending": pending, "needs_reconciliation": reconciliation}

    def list_recovery_operations(self, core) -> list[dict[str, Any]]:
        """Expose non-complete operations for an administrator/recovery UI."""
        self._ensure_outbox(core)
        with sqlite3.connect(str(core.repository.database), timeout=20) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """SELECT operation_id,station_id,station_name,target_project_id,actor_id,
                          entity_count,created_at,status,last_error
                   FROM station_transfer_outbox
                   WHERE status!='COMPLETE'
                   ORDER BY created_at"""
            ).fetchall()
        return [dict(row) for row in rows]

    def commit_import(self, core, staged_path: str | Path, *, expected_package_id: str, target_project_id: str,
                      actor: str = "local-engineer") -> dict[str, Any]:
        stage_input = Path(staged_path).expanduser()
        if stage_input.is_symlink():
            raise StationTransferError("Staged Station directory cannot be a symbolic link")
        stage = stage_input.resolve()
        if not stage.is_dir() or (stage / "stage.json").is_symlink() or (stage / "station.json").is_symlink():
            raise StationTransferError("Staged Station files are missing or symbolic links")
        try:
            stage_meta = json.loads((stage / "stage.json").read_text(encoding="utf-8"))
            payload = json.loads((stage / "station.json").read_text(encoding="utf-8"))
        except Exception as exc:
            raise StationTransferError("Staged Station data is missing or invalid") from exc
        if not isinstance(stage_meta, dict) or not isinstance(payload, dict):
            raise StationTransferError("Staged Station metadata and payload must be objects")
        if stage_meta.get("package_id") != expected_package_id or stage_meta.get("state") != "STAGED_NOT_ACTIVATED":
            raise StationTransferError("Staged package identity/state mismatch")
        if hashlib.sha256((stage / "station.json").read_bytes()).hexdigest() != stage_meta.get("payload_sha256"):
            raise StationTransferError("staged Station payload integrity check failed")
        if not isinstance(payload.get("entities"), list) or not isinstance(payload.get("auxiliary", {}), dict):
            raise StationTransferError("Staged Station entity/auxiliary structure is invalid")
        self._ensure_outbox(core)
        operation_id = str(uuid4())
        created_at = datetime.now(timezone.utc).isoformat()
        event_id = str(uuid5(NAMESPACE_URL, "avic.station-transfer:" + operation_id + ":event"))
        audit_event_id = str(uuid5(NAMESPACE_URL, "avic.station-transfer:" + operation_id + ":audit"))
        with core._lock:
            core._ensure_open()
            try:
                target_project = core.repository.get_record(target_project_id)
            except Exception as exc:
                raise StationTransferError("Target Project does not exist") from exc
            if target_project["entity_type"] != "Project":
                raise StationTransferError("Target parent is not a Project")
            if target_project["payload"].get("archived", False):
                raise StationTransferError("Cannot import a Station into an archived Project")
            records = payload.get("entities", [])
            station_id = stage_meta.get("station_id")
            if not records or records[0] is None:
                raise StationTransferError("Staged package has no entities")
            incoming_ids = {str(r.get("entity_id")) for r in records}
            if len(incoming_ids) != len(records):
                raise StationTransferError("Duplicate entity IDs in staged Station")
            existing = core.repository.list_records()
            existing_by_id = {r["entity_id"]: r for r in existing}
            conflicts = sorted(incoming_ids.intersection(existing_by_id))
            if conflicts:
                raise StationTransferError("Object ID collision on target: " + ", ".join(conflicts[:10]))
            station_record = next((r for r in records if r.get("entity_type") == "Station"), None)
            if station_record is None or station_record.get("entity_id") != station_id:
                raise StationTransferError("Staged Station root is invalid")
            # Bind the imported Station to the target Project without changing its ID.
            station_record["payload"]["project_id"] = target_project_id
            station_record["project_id"] = target_project_id
            by_id = {r["entity_id"]: (r["entity_type"], r["payload"]) for r in existing}
            by_id.update({r["entity_id"]: (r["entity_type"], r["payload"]) for r in records})
            core.objects._validate_graph(by_id)
            self._validate_engineering_references(records, payload.get("auxiliary", {}))
            # Check all auxiliary conflicts before changing any target database.
            auxiliary = payload.get("auxiliary", {})
            db_specs: list[tuple[Path, str, list[dict[str, Any]]]] = []
            db_names = {"custom_svg": "custom_svg_library.sqlite3", "dependencies": "dependencies.sqlite3",
                        "time_management": "time_management.sqlite3", "schedules": "schedules.sqlite3",
                        "analytics": "analytics.sqlite3"}
            for db_key, tables in auxiliary.items():
                if db_key not in db_names or not isinstance(tables, dict):
                    raise StationTransferError("Unknown auxiliary database in Station package")
                db_path = core.paths.databases / db_names[db_key]
                for table, rows in tables.items():
                    if not isinstance(rows, list):
                        raise StationTransferError("Invalid auxiliary table payload")
                    if not rows:
                        continue
                    if not db_path.is_file():
                        raise StationTransferError(f"Target database is missing: {db_names[db_key]}")
                    with self._connect(db_path) as db:
                        if not self._table_exists(db, table):
                            raise StationTransferError(f"Target schema does not support table: {table}")
                        columns = self._table_columns(db, table)
                        for row in rows:
                            if not isinstance(row, dict) or not set(row).issubset(columns):
                                raise StationTransferError(f"Unsupported columns in auxiliary table: {table}")
                            pk_cols = [r[1] for r in db.execute(f'PRAGMA table_info("{table}")') if r[5]]
                            if pk_cols and all(k in row for k in pk_cols):
                                where = " AND ".join(f'"{k}"=?' for k in pk_cols)
                                values = tuple(self._from_json_value(row[k]) for k in pk_cols)
                                if db.execute(f'SELECT 1 FROM "{table}" WHERE {where}', values).fetchone():
                                    raise StationTransferError(f"Auxiliary ID collision in {table}")
                    db_specs.append((db_path, table, rows))
            # Repository insertion is a single SQLite transaction. Auxiliary DBs
            # are separately transactional; snapshots compensate if a later DB fails.
            snapshots: dict[Path, Path] = {}
            try:
                for db_path, _, _ in db_specs:
                    if db_path not in snapshots:
                        fd, snap_name = tempfile.mkstemp(prefix=db_path.name + ".pre-transfer.", suffix=".sqlite", dir=str(core.paths.backups))
                        os.close(fd)
                        snap = Path(snap_name)
                        src = sqlite3.connect(str(db_path)); dst = sqlite3.connect(str(snap))
                        try: src.backup(dst)
                        finally: dst.close(); src.close()
                        snapshots[db_path] = snap
                with core.repository.transaction() as conn:
                    for row in records:
                        # Repository.save requires dataclass objects. The stored
                        # payload is already canonical JSON, so insert validated rows.
                        conn.execute("INSERT INTO entities(entity_id,entity_type,name,project_id,station_id,version,payload,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?)",
                            (row["entity_id"], row["entity_type"], row["name"], row.get("project_id"), row.get("station_id"),
                             int(row["version"]), json.dumps(row["payload"], ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                             row["created_at"], row["updated_at"]))
                    conn.execute("""INSERT INTO station_transfer_outbox
                        (operation_id,station_id,station_name,target_project_id,actor_id,entity_count,created_at,
                         status,event_id,audit_event_id,last_error)
                        VALUES(?,?,?,?,?,?,?,'PREPARED',?,?,NULL)""",
                        (operation_id, station_id, station_record["name"], target_project_id, actor,
                         len(records), created_at, event_id, audit_event_id))
                grouped: dict[Path, list[tuple[str, list[dict[str, Any]]]]] = {}
                for db_path, table, rows in db_specs:
                    grouped.setdefault(db_path, []).append((table, rows))
                for db_path, table_rows in grouped.items():
                    with self._connect(db_path) as db:
                        db.execute("BEGIN IMMEDIATE")
                        try:
                            for table, rows in table_rows:
                                for row in rows:
                                    decoded = {k: self._from_json_value(v) for k, v in row.items()}
                                    cols = list(decoded)
                                    sql = f'INSERT INTO "{table}" ({",".join(chr(34)+c+chr(34) for c in cols)}) VALUES ({",".join("?" for _ in cols)})'
                                    db.execute(sql, tuple(decoded[c] for c in cols))
                            db.commit()
                        except Exception:
                            db.rollback()
                            raise
            except Exception as exc:
                # Compensate all SQLite auxiliary stores and remove inserted entities.
                compensation_failures: list[str] = []
                for db_path, snap in snapshots.items():
                    try:
                        src = sqlite3.connect(str(snap)); dst = sqlite3.connect(str(db_path))
                        try: src.backup(dst)
                        finally: dst.close(); src.close()
                    except Exception as rollback_exc:
                        compensation_failures.append(f"{db_path.name}: {rollback_exc}")
                try:
                    with core.repository.transaction() as conn:
                        conn.executemany("DELETE FROM entities WHERE entity_id=?", [(x,) for x in incoming_ids])
                        conn.execute("DELETE FROM station_transfer_outbox WHERE operation_id=?", (operation_id,))
                except Exception as rollback_exc:
                    compensation_failures.append(f"objects.sqlite3: {rollback_exc}")
                if compensation_failures:
                    raise StationTransferError("Station import failed and compensation is incomplete: " + "; ".join(compensation_failures)) from exc
                if isinstance(exc, StationTransferError):
                    raise
                raise StationTransferError(f"Station import failed; database compensation completed: {exc}") from exc
            finally:
                for snap in snapshots.values():
                    try: snap.unlink(missing_ok=True)
                    except OSError: pass
            # Auxiliary stores have committed. Move the durable outbox row to a
            # retryable delivery state before attempting either external journal.
            try:
                with core.repository.transaction() as conn:
                    conn.execute("UPDATE station_transfer_outbox SET status='JOURNAL_PENDING' WHERE operation_id=?",
                                 (operation_id,))
            except Exception:
                # The PREPARED row is still durable. We know this live process completed
                # the auxiliary writes, so it is safe to attempt idempotent delivery now.
                pass
            delivered = self._deliver_outbox(core, operation_id, allow_prepared=True)
            return {"station_id": station_id, "station_name": station_record["name"], "entity_count": len(records),
                    "activation": "NOT_ACTIVATED", "site_binding_required": True,
                    "operation_id": operation_id,
                    "journal_status": "DELIVERED" if delivered else "PENDING_RETRY"}
