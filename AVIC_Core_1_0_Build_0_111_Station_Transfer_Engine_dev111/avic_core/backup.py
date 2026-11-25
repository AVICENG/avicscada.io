from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.exceptions import InvalidTag


class SystemBackupError(RuntimeError):
    """Raised when a full Core backup cannot be safely created or restored."""


@dataclass(frozen=True)
class SystemBackupPreview:
    backup_id: str
    created_at: str
    core_version: str
    file_count: int
    total_bytes: int
    databases: tuple[str, ...]
    checksum_valid: bool
    warnings: tuple[str, ...] = ()


class SystemBackupManager:
    """Encrypted, verified full-installation backup using SQLite online snapshots.

    Each SQLite database is captured through SQLite's backup API (including WAL
    committed pages). Station runtimes and driver sessions must be stopped.
    Separate SQLite files are individually consistent; this is not a cross-file
    atomic transaction.
    """

    FORMAT = "AVIC_SYSTEM_BACKUP"
    FORMAT_VERSION = 1
    MANIFEST = "__avic_system_backup__.json"
    MAGIC = b"AVICSB01"
    SALT_BYTES = 16
    NONCE_BYTES = 12
    TAG_BYTES = 16
    CHUNK_BYTES = 1024 * 1024
    MAX_FILES = 200_000
    MAX_UNCOMPRESSED_BYTES = 16 * 1024 * 1024 * 1024

    def _derive_key(self, passphrase: str, salt: bytes) -> bytes:
        if not isinstance(passphrase, str) or len(passphrase) < 12:
            raise SystemBackupError("Пароль резервной копии должен содержать не менее 12 символов")
        return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(passphrase.encode("utf-8"))

    @staticmethod
    def _sha256_file(path: Path) -> tuple[str, int]:
        digest = hashlib.sha256()
        size = 0
        with path.open("rb") as stream:
            while True:
                chunk = stream.read(SystemBackupManager.CHUNK_BYTES)
                if not chunk:
                    break
                digest.update(chunk)
                size += len(chunk)
        return digest.hexdigest(), size

    @staticmethod
    def _assert_core_quiescent(core) -> None:
        if getattr(core, "closed", False):
            raise SystemBackupError("Нельзя создавать резервную копию закрытого AVIC Core")
        active = []
        try:
            for status in core.runtime.all():
                state = getattr(status.state, "value", status.state)
                if state != "STOPPED":
                    active.append(f"{status.station_id}:{state}")
        except Exception as exc:
            raise SystemBackupError(f"Не удалось проверить состояние станций: {exc}") from exc
        if active:
            raise SystemBackupError(
                "Для полной системной копии остановите все станции: " + ", ".join(active)
            )
        sessions = getattr(getattr(core, "driver_manager", None), "_sessions", None)
        if sessions:
            raise SystemBackupError("Нельзя создавать системную копию: остались активные сессии драйверов")

    @staticmethod
    def _sqlite_snapshot(source: Path, destination: Path) -> None:
        source_db = None
        target_db = None
        try:
            source_db = sqlite3.connect(str(source), timeout=30)
            source_db.execute("PRAGMA busy_timeout=30000")
            target_db = sqlite3.connect(str(destination), timeout=30)
            source_db.backup(target_db, pages=256, sleep=0.01)
            result = target_db.execute("PRAGMA integrity_check").fetchone()
            if not result or result[0] != "ok":
                raise SystemBackupError(f"SQLite snapshot integrity check failed: {source.name}")
            target_db.commit()
        except sqlite3.Error as exc:
            raise SystemBackupError(f"Не удалось создать согласованный снимок {source.name}: {exc}") from exc
        finally:
            if target_db is not None:
                target_db.close()
            if source_db is not None:
                source_db.close()

    def _snapshot_tree(self, core, destination: Path, core_version: str) -> dict[str, Any]:
        root = Path(core.paths.root).resolve()
        destination.mkdir(parents=True, exist_ok=True)
        database_names: list[str] = []
        for item in sorted(root.rglob("*")):
            relative = item.relative_to(root)
            if relative.parts and relative.parts[0].casefold() in {"backups", ".git", "__pycache__"}:
                continue
            if item.is_symlink():
                raise SystemBackupError(f"Символические ссылки запрещены в системной копии: {relative}")
            if not item.is_file():
                continue
            if item.name.endswith(("-wal", "-shm")):
                continue
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if item.suffix.casefold() in {".sqlite", ".sqlite3", ".db"}:
                self._sqlite_snapshot(item, target)
                database_names.append(relative.as_posix())
            else:
                shutil.copy2(item, target)

        files: dict[str, dict[str, Any]] = {}
        total = 0
        for item in sorted(destination.rglob("*")):
            if not item.is_file():
                continue
            relative = item.relative_to(destination).as_posix()
            digest, size = self._sha256_file(item)
            files[relative] = {"sha256": digest, "size": size}
            total += size
            if len(files) > self.MAX_FILES or total > self.MAX_UNCOMPRESSED_BYTES:
                raise SystemBackupError("Системная копия превышает допустимые ограничения размера")
        return {
            "format": self.FORMAT,
            "format_version": self.FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "core_version": core_version,
            "consistency": "sqlite-online-snapshot-per-database; all stations and driver sessions stopped",
            "file_count": len(files),
            "total_bytes": total,
            "databases": database_names,
            "files": files,
        }

    def _encrypt(self, source: Path, destination: Path, passphrase: str) -> None:
        salt = os.urandom(self.SALT_BYTES)
        nonce = os.urandom(self.NONCE_BYTES)
        key = self._derive_key(passphrase, salt)
        encryptor = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        destination.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=destination.name + ".", suffix=".tmp", dir=str(destination.parent))
        try:
            with os.fdopen(fd, "wb") as output, source.open("rb") as input_stream:
                output.write(self.MAGIC + salt + nonce)
                while True:
                    chunk = input_stream.read(self.CHUNK_BYTES)
                    if not chunk:
                        break
                    encrypted = encryptor.update(chunk)
                    if encrypted:
                        output.write(encrypted)
                final = encryptor.finalize()
                if final:
                    output.write(final)
                output.write(encryptor.tag)
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _decrypt(self, source: Path, destination: Path, passphrase: str) -> None:
        try:
            size = source.stat().st_size
            minimum = len(self.MAGIC) + self.SALT_BYTES + self.NONCE_BYTES + self.TAG_BYTES + 1
            if size < minimum:
                raise SystemBackupError("Файл резервной копии повреждён или имеет неверный формат")
            with source.open("rb") as input_stream:
                header = input_stream.read(len(self.MAGIC) + self.SALT_BYTES + self.NONCE_BYTES)
                if len(header) != len(self.MAGIC) + self.SALT_BYTES + self.NONCE_BYTES or not header.startswith(self.MAGIC):
                    raise SystemBackupError("Неизвестный формат системной резервной копии")
                offset = len(self.MAGIC)
                salt = header[offset:offset + self.SALT_BYTES]
                nonce = header[offset + self.SALT_BYTES:]
                input_stream.seek(-self.TAG_BYTES, os.SEEK_END)
                tag = input_stream.read(self.TAG_BYTES)
                ciphertext_length = size - len(header) - self.TAG_BYTES
                input_stream.seek(len(header))
                key = self._derive_key(passphrase, salt)
                decryptor = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("wb") as output:
                    remaining = ciphertext_length
                    while remaining:
                        chunk = input_stream.read(min(self.CHUNK_BYTES, remaining))
                        if not chunk:
                            raise SystemBackupError("Неполный файл резервной копии")
                        remaining -= len(chunk)
                        plain = decryptor.update(chunk)
                        if plain:
                            output.write(plain)
                    final = decryptor.finalize()
                    if final:
                        output.write(final)
        except InvalidTag as exc:
            raise SystemBackupError("Неверный пароль или нарушена целостность резервной копии") from exc
        except OSError as exc:
            raise SystemBackupError(f"Не удалось прочитать резервную копию: {exc}") from exc

    @staticmethod
    def _safe_relative_path(value: str) -> PurePosixPath:
        if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or ":" in value:
            raise SystemBackupError("Недопустимый путь в резервной копии")
        path = PurePosixPath(value)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise SystemBackupError(f"Небезопасный путь в резервной копии: {value}")
        return path

    def _verify_archive(self, archive_path: Path) -> tuple[dict[str, Any], int]:
        try:
            archive = zipfile.ZipFile(archive_path, "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise SystemBackupError("Внутренний архив системной копии повреждён") from exc
        with archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)) or len(names) > self.MAX_FILES + 1:
                raise SystemBackupError("В архиве обнаружены повторяющиеся пути или слишком много файлов")
            if self.MANIFEST not in names:
                raise SystemBackupError("Манифест системной резервной копии отсутствует")
            try:
                manifest = json.loads(archive.read(self.MANIFEST))
            except Exception as exc:
                raise SystemBackupError("Манифест системной резервной копии повреждён") from exc
            if manifest.get("format") != self.FORMAT or manifest.get("format_version") != self.FORMAT_VERSION:
                raise SystemBackupError("Неподдерживаемая версия формата системной резервной копии")
            expected = manifest.get("files")
            if not isinstance(expected, dict) or manifest.get("file_count") != len(expected):
                raise SystemBackupError("Список файлов в манифесте некорректен")
            if set(names) - {self.MANIFEST} != set(expected):
                raise SystemBackupError("Состав архива не совпадает с манифестом")
            total = 0
            for info in infos:
                if info.filename == self.MANIFEST:
                    continue
                relative = self._safe_relative_path(info.filename)
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000 or info.is_dir():
                    raise SystemBackupError(f"Недопустимый тип элемента архива: {info.filename}")
                metadata = expected[info.filename]
                if not isinstance(metadata, dict) or not isinstance(metadata.get("size"), int):
                    raise SystemBackupError(f"Некорректные метаданные файла: {info.filename}")
                if metadata["size"] != info.file_size:
                    raise SystemBackupError(f"Размер файла не совпадает с манифестом: {info.filename}")
                total += info.file_size
                if total > self.MAX_UNCOMPRESSED_BYTES:
                    raise SystemBackupError("Распакованный архив превышает допустимый размер")
                digest = hashlib.sha256()
                actual_size = 0
                with archive.open(info, "r") as stream:
                    while True:
                        chunk = stream.read(self.CHUNK_BYTES)
                        if not chunk:
                            break
                        digest.update(chunk)
                        actual_size += len(chunk)
                if actual_size != metadata["size"] or digest.hexdigest() != metadata.get("sha256"):
                    raise SystemBackupError(f"Контрольная сумма не совпадает: {info.filename}")
            return manifest, total

    def create_backup(self, core, destination: str | Path, *, passphrase: str,
                      core_version: str = "unknown") -> Path:
        self._assert_core_quiescent(core)
        output = Path(destination).expanduser().resolve()
        root = Path(core.paths.root).resolve()
        if output == root or root in output.parents:
            if not (output.parent == Path(core.paths.backups).resolve() or Path(core.paths.backups).resolve() in output.parents):
                raise SystemBackupError("Системная копия должна храниться вне каталога данных, в том числе в Core/backups")
        with tempfile.TemporaryDirectory(prefix="avic-system-backup-") as temporary:
            temporary_root = Path(temporary)
            snapshot = temporary_root / "snapshot"
            manifest = self._snapshot_tree(core, snapshot, core_version)
            archive_path = temporary_root / "payload.zip"
            with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                archive.writestr(self.MANIFEST, json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
                for item in sorted(snapshot.rglob("*")):
                    if item.is_file():
                        archive.write(item, arcname=item.relative_to(snapshot).as_posix())
            self._verify_archive(archive_path)
            self._encrypt(archive_path, output, passphrase)
        return output

    def inspect_backup(self, backup_path: str | Path, *, passphrase: str) -> SystemBackupPreview:
        source = Path(backup_path).expanduser().resolve()
        with tempfile.TemporaryDirectory(prefix="avic-system-inspect-") as temporary:
            archive_path = Path(temporary) / "payload.zip"
            self._decrypt(source, archive_path, passphrase)
            manifest, total = self._verify_archive(archive_path)
        return SystemBackupPreview(
            backup_id=self._sha256_file(source)[0][:20],
            created_at=manifest["created_at"],
            core_version=manifest.get("core_version", "unknown"),
            file_count=manifest["file_count"],
            total_bytes=total,
            databases=tuple(manifest.get("databases", [])),
            checksum_valid=True,
            warnings=("Снимки SQLite согласованы по отдельности; общей атомарной транзакции между разными БД нет.",),
        )

    def restore_backup(self, backup_path: str | Path, target_root: str | Path, *, passphrase: str,
                       expected_backup_id: str) -> Path:
        source = Path(backup_path).expanduser().resolve()
        target = Path(target_root).expanduser().resolve()
        if not expected_backup_id:
            raise SystemBackupError("Для восстановления требуется ID из предварительной проверки")
        backup_id = self._sha256_file(source)[0][:20]
        if backup_id != expected_backup_id:
            raise SystemBackupError("Файл резервной копии изменился после предварительной проверки")
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.is_symlink() or any(target.rglob("*")):
                raise SystemBackupError("Восстановление разрешено только в новый или пустой каталог")
        with tempfile.TemporaryDirectory(prefix="avic-system-restore-", dir=str(parent)) as temporary:
            temporary_root = Path(temporary)
            archive_path = temporary_root / "payload.zip"
            self._decrypt(source, archive_path, passphrase)
            manifest, _ = self._verify_archive(archive_path)
            stage = temporary_root / "restored"
            stage.mkdir()
            with zipfile.ZipFile(archive_path, "r") as archive:
                for info in archive.infolist():
                    if info.filename == self.MANIFEST:
                        continue
                    relative = self._safe_relative_path(info.filename)
                    destination = stage.joinpath(*relative.parts)
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with archive.open(info, "r") as input_stream, destination.open("xb") as output:
                        shutil.copyfileobj(input_stream, output, length=self.CHUNK_BYTES)
            for database in manifest.get("databases", []):
                relative = self._safe_relative_path(database)
                db_path = stage.joinpath(*relative.parts)
                if not db_path.is_file():
                    raise SystemBackupError(f"Восстановленная база данных отсутствует: {database}")
                try:
                    with sqlite3.connect(str(db_path)) as db:
                        check = db.execute("PRAGMA integrity_check").fetchone()
                        if not check or check[0] != "ok":
                            raise SystemBackupError(f"SQLite integrity_check failed after restore: {database}")
                except sqlite3.Error as exc:
                    raise SystemBackupError(f"Не удалось проверить восстановленную БД {database}: {exc}") from exc
            if target.exists():
                target.rmdir()
            os.replace(stage, target)
        return target
