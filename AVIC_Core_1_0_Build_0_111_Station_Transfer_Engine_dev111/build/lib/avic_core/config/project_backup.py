from __future__ import annotations
import hashlib
import json
import os
import shutil
import tempfile
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class BackupError(RuntimeError):
    pass


@dataclass(frozen=True)
class BackupPreview:
    backup_id: str
    file_count: int
    total_bytes: int
    files: tuple[str, ...]
    checksum_valid: bool
    warnings: tuple[str, ...] = ()


class ProjectBackupManager:
    """Verified whole-project backup/restore. Restore stages a complete tree before swap."""
    FORMAT_VERSION = 1
    MANIFEST_NAME = "__avic_backup_manifest__.json"

    def create_backup(self, project_root: str | Path, destination: str | Path) -> Path:
        root = Path(project_root).resolve()
        output = Path(destination).resolve()
        if not root.is_dir():
            raise BackupError("Project root does not exist")
        if output == root or root in output.parents:
            raise BackupError("Backup archive must be outside the project root")
        files: dict[str, dict[str, Any]] = {}
        for item in sorted(root.rglob("*")):
            if item.is_symlink():
                raise BackupError(f"Symbolic links are not allowed in project backup: {item}")
            if not item.is_file():
                continue
            relative = item.relative_to(root).as_posix()
            data = item.read_bytes()
            files[relative] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
        manifest = {
            "format_version": self.FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "file_count": len(files),
            "files": files,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
        os.close(fd)
        try:
            with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr(self.MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
                for relative in files:
                    archive.write(root / Path(relative), arcname=relative)
            # Validate the completed archive before publishing it.
            self.preview(temp_name)
            os.replace(temp_name, output)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return output

    def _read_verified(self, backup_path: str | Path):
        try:
            archive = zipfile.ZipFile(backup_path, "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise BackupError("Backup archive cannot be opened") from exc
        with archive:
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise BackupError("Backup contains duplicate paths")
            if self.MANIFEST_NAME not in names:
                raise BackupError("Backup manifest is missing")
            try:
                manifest = json.loads(archive.read(self.MANIFEST_NAME))
            except Exception as exc:
                raise BackupError("Backup manifest is invalid") from exc
            if manifest.get("format_version") != self.FORMAT_VERSION:
                raise BackupError("Unsupported backup format version")
            expected = manifest.get("files")
            if not isinstance(expected, dict) or manifest.get("file_count") != len(expected):
                raise BackupError("Backup manifest file list is inconsistent")
            actual_names = set(names) - {self.MANIFEST_NAME}
            if actual_names != set(expected):
                raise BackupError("Backup contents do not match manifest")
            contents: dict[str, bytes] = {}
            total = 0
            for info in archive.infolist():
                if info.filename == self.MANIFEST_NAME:
                    continue
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == 0o120000:
                    raise BackupError(f"Symbolic link is not allowed in backup: {info.filename}")
            for relative, metadata in expected.items():
                path = PurePosixPath(relative)
                if path.is_absolute() or ".." in path.parts or not path.parts or "\\" in relative or ":" in relative or "\x00" in relative:
                    raise BackupError(f"Unsafe path in backup: {relative}")
                data = archive.read(relative)
                digest = hashlib.sha256(data).hexdigest()
                if digest != metadata.get("sha256") or len(data) != metadata.get("size"):
                    raise BackupError(f"Integrity check failed: {relative}")
                contents[relative] = data
                total += len(data)
            return manifest, contents, total

    def preview(self, backup_path: str | Path) -> BackupPreview:
        manifest, contents, total = self._read_verified(backup_path)
        return BackupPreview(
            backup_id=hashlib.sha256(Path(backup_path).read_bytes()).hexdigest()[:16],
            file_count=len(contents), total_bytes=total,
            files=tuple(sorted(contents)), checksum_valid=True,
        )

    def restore(self, backup_path: str | Path, target_root: str | Path, *,
                expected_backup_id: str | None = None) -> Path:
        preview = self.preview(backup_path)
        if expected_backup_id is not None and preview.backup_id != expected_backup_id:
            raise BackupError("Backup changed after preview; restore cancelled")
        _, contents, _ = self._read_verified(backup_path)
        target = Path(target_root).resolve()
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=target.name + ".restore.", dir=str(parent)))
        old = parent / (target.name + ".pre_restore")
        try:
            for relative, data in contents.items():
                destination = stage / Path(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            if old.exists():
                raise BackupError(f"Previous restore safety directory already exists: {old}")
            if target.exists():
                os.replace(target, old)
            try:
                os.replace(stage, target)
            except Exception:
                if old.exists() and not target.exists():
                    os.replace(old, target)
                raise
            # Keep pre-restore tree until an explicit retention/cleanup policy is implemented.
            return target
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
