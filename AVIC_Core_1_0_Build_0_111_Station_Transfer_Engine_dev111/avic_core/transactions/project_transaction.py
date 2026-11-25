from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing, contextmanager
import uuid
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping


class ProjectTransactionError(RuntimeError):
    pass


@dataclass(frozen=True)
class TransactionResult:
    transaction_id: str
    state: str
    files_written: int


class ProjectTransactionCoordinator:
    """Crash-recoverable coordinator for one SQLite DB and project files.

    SQLite is the commit authority. A durable PREPARED journal is created first;
    the DB mutation and DB_COMMITTED marker are committed in one SQLite transaction.
    File replacements are then replayed idempotently. Startup must call recover()
    before exposing the project to Engineering/Runtime services.
    """

    def __init__(self, database: str | Path, project_root: str | Path, journal_root: str | Path | None = None):
        self.database = Path(database).resolve()
        self.project_root = Path(project_root).resolve()
        self.journal_root = Path(journal_root).resolve() if journal_root else self.project_root / ".avic_transactions"
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.project_root.mkdir(parents=True, exist_ok=True)
        self.journal_root.mkdir(parents=True, exist_ok=True)
        self._coordination_db = self.database.with_name(self.database.name + ".coordination.sqlite3")
        with closing(sqlite3.connect(self._coordination_db, timeout=30, isolation_level=None)) as lock_db:
            lock_db.execute("PRAGMA busy_timeout=30000")
            lock_db.execute("CREATE TABLE IF NOT EXISTS coordinator_lock (id INTEGER PRIMARY KEY CHECK(id=1), touched_at TEXT)")
            lock_db.execute("INSERT OR IGNORE INTO coordinator_lock(id,touched_at) VALUES(1,CURRENT_TIMESTAMP)")
        with closing(self._connect()) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS avic_project_transactions (
                transaction_id TEXT PRIMARY KEY, state TEXT NOT NULL,
                stage_dir TEXT NOT NULL, file_manifest TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def _connect(self):
        db = sqlite3.connect(self.database, timeout=30, isolation_level=None)
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _safe_target(self, relative: str) -> Path:
        rel = PurePosixPath(relative)
        if rel.is_absolute() or not rel.parts or ".." in rel.parts or "\\" in relative or ":" in relative or "\x00" in relative:
            raise ProjectTransactionError(f"Unsafe project-relative path: {relative!r}")
        target = (self.project_root / Path(*rel.parts)).resolve()
        if target != self.project_root and self.project_root not in target.parents:
            raise ProjectTransactionError("Target escapes project root")
        return target

    @contextmanager
    def _coordination_lock(self):
        # Held across DB commit AND file replacement; serializes threads and processes.
        lock_db = sqlite3.connect(self._coordination_db, timeout=30, isolation_level=None)
        try:
            lock_db.execute("PRAGMA busy_timeout=30000")
            lock_db.execute("BEGIN IMMEDIATE")
            yield
            lock_db.commit()
        except Exception:
            lock_db.rollback()
            raise
        finally:
            lock_db.close()

    def commit(self, *, file_updates: Mapping[str, bytes], db_mutation: Callable[[sqlite3.Connection], None]) -> TransactionResult:
        with self._coordination_lock():
            return self._commit_locked(file_updates=file_updates, db_mutation=db_mutation)

    def _commit_locked(self, *, file_updates: Mapping[str, bytes], db_mutation: Callable[[sqlite3.Connection], None]) -> TransactionResult:
        if not callable(db_mutation):
            raise TypeError("db_mutation must be callable")
        txid = str(uuid.uuid4())
        stage = Path(tempfile.mkdtemp(prefix=f"tx-{txid}-", dir=self.journal_root))
        manifest: dict[str, dict[str, object]] = {}
        try:
            for relative, content in file_updates.items():
                if not isinstance(content, bytes):
                    raise TypeError("file_updates values must be bytes")
                self._safe_target(relative)
                staged = stage / "new" / Path(*PurePosixPath(relative).parts)
                staged.parent.mkdir(parents=True, exist_ok=True)
                with staged.open("xb") as stream:
                    stream.write(content)
                    stream.flush()
                    os.fsync(stream.fileno())
                manifest[relative] = {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
            manifest_path = stage / "manifest.json"
            manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
            with manifest_path.open("xb") as stream:
                stream.write(manifest_bytes)
                stream.flush()
                os.fsync(stream.fileno())
            # PREPARED is durable before the database transaction begins.
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO avic_project_transactions(transaction_id,state,stage_dir,file_manifest) VALUES(?,?,?,?)",
                           (txid, "PREPARED", str(stage), json.dumps(manifest, sort_keys=True)))
                db.commit()
            # The application DB mutation and commit decision share one SQLite commit.
            with closing(self._connect()) as db:
                db.execute("BEGIN IMMEDIATE")
                db_mutation(db)
                db.execute("UPDATE avic_project_transactions SET state='DB_COMMITTED', updated_at=CURRENT_TIMESTAMP WHERE transaction_id=?", (txid,))
                db.commit()
            self._apply_files(stage, manifest)
            with closing(self._connect()) as db:
                db.execute("UPDATE avic_project_transactions SET state='COMMITTED', updated_at=CURRENT_TIMESTAMP WHERE transaction_id=?", (txid,))
            shutil.rmtree(stage, ignore_errors=True)
            return TransactionResult(txid, "COMMITTED", len(manifest))
        except Exception:
            # PREPARED without DB_COMMITTED is safe to abandon. DB_COMMITTED must
            # remain journaled for startup recovery; never delete its staged payload.
            try:
                with closing(self._connect()) as db:
                    row = db.execute("SELECT state FROM avic_project_transactions WHERE transaction_id=?", (txid,)).fetchone()
                if row and row[0] == "PREPARED":
                    with closing(self._connect()) as db:
                        db.execute("DELETE FROM avic_project_transactions WHERE transaction_id=?", (txid,))
                    shutil.rmtree(stage, ignore_errors=True)
            except Exception:
                pass
            raise

    def _apply_files(self, stage: Path, manifest: dict[str, dict[str, object]]) -> None:
        for relative, metadata in manifest.items():
            target = self._safe_target(relative)
            source = stage / "new" / Path(*PurePosixPath(relative).parts)
            data = source.read_bytes()
            if len(data) != metadata["size"] or hashlib.sha256(data).hexdigest() != metadata["sha256"]:
                raise ProjectTransactionError(f"Staged file integrity failure: {relative}")
            target.parent.mkdir(parents=True, exist_ok=True)
            temp = target.with_name(target.name + f".{stage.name}.tmp")
            with temp.open("wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp, target)

    def recover(self) -> tuple[TransactionResult, ...]:
        """Finish committed transactions; discard transactions not committed in SQLite."""
        with self._coordination_lock():
            return self._recover_locked()

    def _recover_locked(self) -> tuple[TransactionResult, ...]:
        results: list[TransactionResult] = []
        with closing(self._connect()) as db:
            rows = db.execute("SELECT transaction_id,state,stage_dir,file_manifest FROM avic_project_transactions WHERE state!='COMMITTED' ORDER BY created_at,transaction_id").fetchall()
        for txid, state, stage_dir, raw_manifest in rows:
            stage = Path(stage_dir)
            if state == "PREPARED":
                # DB mutation did not commit; no file is allowed to become visible.
                with closing(self._connect()) as db:
                    db.execute("DELETE FROM avic_project_transactions WHERE transaction_id=? AND state='PREPARED'", (txid,))
                shutil.rmtree(stage, ignore_errors=True)
                results.append(TransactionResult(txid, "ABORTED", 0))
                continue
            if state != "DB_COMMITTED":
                raise ProjectTransactionError(f"Unknown transaction state {state!r}")
            manifest = json.loads(raw_manifest)
            self._apply_files(stage, manifest)
            with closing(self._connect()) as db:
                db.execute("UPDATE avic_project_transactions SET state='COMMITTED',updated_at=CURRENT_TIMESTAMP WHERE transaction_id=?", (txid,))
            shutil.rmtree(stage, ignore_errors=True)
            results.append(TransactionResult(txid, "RECOVERED", len(manifest)))
        return tuple(results)

    def pending_count(self) -> int:
        with closing(self._connect()) as db:
            return int(db.execute("SELECT COUNT(*) FROM avic_project_transactions WHERE state!='COMMITTED'").fetchone()[0])
