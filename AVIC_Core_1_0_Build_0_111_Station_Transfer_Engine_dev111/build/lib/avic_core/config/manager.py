from __future__ import annotations
import copy, hashlib, json, os, re, shutil, sqlite3, tempfile
from contextlib import closing, contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CURRENT_SCHEMA_VERSION = 1

class ConfigError(Exception): pass
class NewerSchemaError(ConfigError): pass
class MigrationError(ConfigError): pass
class RevisionConflict(ConfigError): pass

@dataclass(frozen=True)
class ConfigEnvelope:
    schema_version: int
    core_api_version: str
    entity_id: str
    revision: int
    payload: dict
    checksum: str


def _canonical(data: dict) -> bytes:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")

class ConfigurationManager:
    """Versioned JSON configuration store with safe migration and snapshots."""
    def __init__(self, root: str | Path, *, current_schema: int = CURRENT_SCHEMA_VERSION, core_api_version: str = "1.0"):
        self.root = Path(root)
        self.current_schema = current_schema
        self.core_api_version = core_api_version
        self.root.mkdir(parents=True, exist_ok=True)
        self._migrations: dict[int, Callable[[dict], dict]] = {}
        self._validators: dict[int, Callable[[dict], None]] = {}
        self._lock_db = self.root / ".config-locks.sqlite3"
        with closing(sqlite3.connect(self._lock_db)) as db:
            db.execute("CREATE TABLE IF NOT EXISTS lock_state (id INTEGER PRIMARY KEY CHECK(id=1), touched_at TEXT)")
            db.execute("INSERT OR IGNORE INTO lock_state(id,touched_at) VALUES(1,'initialized')")
            db.commit()

    def register_migration(self, from_version: int, migration: Callable[[dict], dict]):
        if from_version >= self.current_schema or from_version in self._migrations:
            raise ValueError("Invalid or duplicate migration version")
        self._migrations[from_version] = migration

    def register_validator(self, schema_version: int, validator: Callable[[dict], None]):
        if schema_version < 1 or schema_version in self._validators:
            raise ValueError("Invalid or duplicate schema validator")
        self._validators[schema_version] = validator

    @contextmanager
    def _write_lock(self):
        # SQLite BEGIN IMMEDIATE provides a cross-process writer lock on Windows and Linux.
        db = sqlite3.connect(self._lock_db, timeout=30, isolation_level=None)
        try:
            db.execute("PRAGMA busy_timeout=30000")
            db.execute("BEGIN IMMEDIATE")
            yield
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _validate(self, version: int, payload: dict):
        validator = self._validators.get(version)
        if validator is not None:
            try:
                validator(copy.deepcopy(payload))
            except Exception as exc:
                raise ConfigError(f"Configuration schema validation failed for version {version}: {exc}") from exc

    def _checksum(self, body: dict) -> str:
        return hashlib.sha256(_canonical(body)).hexdigest()

    def _decode(self, raw: bytes) -> tuple[dict, dict]:
        try:
            envelope = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ConfigError("Configuration is not valid UTF-8 JSON") from exc
        if not isinstance(envelope, dict):
            raise ConfigError("Configuration root must be an object")
        checksum = envelope.pop("checksum", None)
        if not isinstance(checksum, str) or checksum != self._checksum(envelope):
            raise ConfigError("Configuration checksum mismatch")
        required = {"schema_version", "core_api_version", "entity_id", "revision", "payload"}
        if not required.issubset(envelope):
            raise ConfigError("Configuration envelope is incomplete")
        if not isinstance(envelope["payload"], dict):
            raise ConfigError("Configuration payload must be an object")
        if type(envelope["schema_version"]) is not int or envelope["schema_version"] < 1:
            raise ConfigError("Configuration schema_version must be a positive integer")
        if type(envelope["revision"]) is not int or envelope["revision"] < 1:
            raise ConfigError("Configuration revision must be a positive integer")
        if not isinstance(envelope["core_api_version"], str) or not envelope["core_api_version"]:
            raise ConfigError("Configuration core_api_version must be a non-empty string")
        if not isinstance(envelope["entity_id"], str) or not envelope["entity_id"]:
            raise ConfigError("Configuration entity_id must be a non-empty string")
        return envelope, {"checksum": checksum}

    def _resolve_target(self, entity_id: str, path: str | Path | None) -> Path:
        if not isinstance(entity_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", entity_id) or entity_id in {".", ".."}:
            raise ConfigError("Invalid entity_id; path separators and traversal sequences are forbidden")
        target = Path(path).resolve() if path is not None else (self.root / f"{entity_id}.json").resolve()
        root = self.root.resolve()
        if target != root and root not in target.parents:
            raise ConfigError("Configuration target must remain inside the configuration root")
        return target

    def _atomic_write(self, path: Path, data: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False).encode("utf-8")
        fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_name, path)
            # Best-effort directory fsync on platforms that support it.
            try:
                dir_fd = os.open(path.parent, os.O_RDONLY)
                try: os.fsync(dir_fd)
                finally: os.close(dir_fd)
            except OSError:
                pass
        finally:
            if os.path.exists(tmp_name): os.unlink(tmp_name)

    def save(self, entity_id: str, payload: dict, *, revision: int | None = None,
             expected_revision: int | None = None, path: str | Path | None = None) -> Path:
        target = self._resolve_target(entity_id, path)
        if not isinstance(payload, dict):
            raise ConfigError("Configuration payload must be a JSON object")
        try:
            _canonical(payload)
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"Configuration payload is not valid finite JSON data: {exc}") from exc
        self._validate(self.current_schema, payload)
        with self._write_lock():
            if target.exists():
                # Never overwrite a file that cannot be read and verified.
                current = self.load(target, migrate=False)
                if expected_revision is None or expected_revision != current.revision:
                    raise RevisionConflict(f"Configuration revision is {current.revision}; expected {expected_revision}")
                next_revision = current.revision + 1 if revision is None else revision
                if next_revision <= current.revision:
                    raise RevisionConflict("New revision must be greater than current revision")
                self.create_snapshot(target)
            else:
                if expected_revision not in (None, 0):
                    raise RevisionConflict(f"Configuration does not exist at expected revision {expected_revision}")
                next_revision = 1 if revision is None else revision
                if next_revision < 1:
                    raise RevisionConflict("Configuration revision must be positive")
            body = {"schema_version": self.current_schema, "core_api_version": self.core_api_version,
                    "entity_id": entity_id, "revision": next_revision, "payload": copy.deepcopy(payload)}
            document = dict(body, checksum=self._checksum(body))
            self._atomic_write(target, document)
        return target

    def create_snapshot(self, path: str | Path) -> Path:
        source = Path(path)
        if not source.exists(): raise ConfigError("Cannot snapshot a missing configuration")
        # Verify before preserving; corrupted input is not silently blessed as a backup.
        self._decode(source.read_bytes())
        snapshots = self.root / "snapshots"
        snapshots.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        destination = snapshots / f"{source.stem}.{stamp}.json"
        shutil.copy2(source, destination)
        return destination

    def restore_snapshot(self, snapshot_path: str | Path, target_path: str | Path) -> Path:
        """Restore a previously verified snapshot without interpreting or rewriting its schema."""
        with self._write_lock():
            return self._restore_snapshot_impl(snapshot_path, target_path)

    def _restore_snapshot_impl(self, snapshot_path: str | Path, target_path: str | Path) -> Path:
        snapshot = Path(snapshot_path)
        target = Path(target_path)
        try:
            raw = snapshot.read_bytes()
        except OSError as exc:
            raise ConfigError("Cannot read snapshot") from exc
        # Verify checksum and envelope, but preserve the snapshot byte-for-byte.
        self._decode(raw)
        if target.exists():
            # Preserve the current target before rollback; invalid current data is not overwritten.
            self._decode(target.read_bytes())
            self.create_snapshot(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(prefix=target.name + ".restore.", suffix=".tmp", dir=str(target.parent))
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(tmp_name, target)
        finally:
            if os.path.exists(tmp_name): os.unlink(tmp_name)
        return target

    def load(self, path: str | Path, *, migrate: bool = True) -> ConfigEnvelope:
        if migrate:
            with self._write_lock():
                return self._load_impl(path, migrate=True)
        return self._load_impl(path, migrate=False)

    def _load_impl(self, path: str | Path, *, migrate: bool) -> ConfigEnvelope:
        source = Path(path)
        try: raw = source.read_bytes()
        except OSError as exc: raise ConfigError(f"Cannot read configuration: {source}") from exc
        body, meta = self._decode(raw)
        version = int(body["schema_version"])
        if version > self.current_schema:
            raise NewerSchemaError(f"Config schema {version} is newer than supported {self.current_schema}; source left untouched")
        payload = copy.deepcopy(body["payload"])
        self._validate(version, payload)
        if version < self.current_schema and migrate:
            try:
                while version < self.current_schema:
                    migration = self._migrations.get(version)
                    if migration is None: raise MigrationError(f"Missing migration from schema {version}")
                    payload = migration(payload)
                    if not isinstance(payload, dict): raise MigrationError("Migration must return an object")
                    version += 1
                    self._validate(version, payload)
            except Exception as exc:
                raise MigrationError(f"Migration failed; original configuration preserved: {exc}") from exc
            # Migrate to a new verified document only after all steps have succeeded.
            new_body = {"schema_version": self.current_schema, "core_api_version": self.core_api_version,
                        "entity_id": body["entity_id"], "revision": int(body["revision"]) + 1, "payload": payload}
            self.create_snapshot(source)
            self._atomic_write(source, dict(new_body, checksum=self._checksum(new_body)))
            body = new_body
        return ConfigEnvelope(int(body["schema_version"]), str(body["core_api_version"]),
                              str(body["entity_id"]), int(body["revision"]), payload,
                              self._checksum({k:v for k,v in body.items() if k != "checksum"}))
