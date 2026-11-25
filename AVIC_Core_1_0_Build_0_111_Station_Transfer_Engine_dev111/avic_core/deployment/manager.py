from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


class DeploymentError(RuntimeError):
    """Raised when a deployment package is invalid or cannot be safely applied."""


@dataclass(frozen=True)
class DeploymentPreview:
    package_id: str
    project_id: str
    project_name: str
    package_version: int
    source_core_version: str
    required_modules: tuple[str, ...]
    file_count: int
    total_bytes: int
    files: tuple[str, ...]
    compatible: bool
    warnings: tuple[str, ...] = ()


class DeploymentManager:
    """Portable project package export, inspection and staged activation.

    The package carries engineering configuration only. Site-specific endpoints
    and credentials are deliberately excluded and supplied separately at import.
    SHA-256 provides integrity checking, not publisher authenticity; package
    signing is a separate release capability.
    """

    FORMAT_VERSION = 1
    MANIFEST = "avic-package.json"
    PAYLOAD = "payload"
    MAX_FILES = 100_000
    MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
    MAX_FILE_BYTES = 512 * 1024 * 1024
    SECRET_NAMES = {
        ".env", ".env.local", ".env.production", "secrets", "secrets.json",
        "secret_store.json", "credentials.json", "id_rsa", "id_ed25519",
        "private.key", "private.pem", "master.key", "license.key",
    }
    SECRET_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
    SECRET_PARTS = {"secrets", "secret", "credentials", "private_keys"}

    @classmethod
    def _is_secret(cls, relative: str) -> bool:
        path = PurePosixPath(relative)
        lowered = [part.lower() for part in path.parts]
        name = path.name.lower()
        return (
            any(part in cls.SECRET_PARTS for part in lowered)
            or name in cls.SECRET_NAMES
            or name.startswith(".env.")
            or path.suffix.lower() in cls.SECRET_SUFFIXES
        )

    @staticmethod
    def _safe_relative(relative: str) -> str:
        path = PurePosixPath(relative)
        if (not relative or path.is_absolute() or ".." in path.parts
                or "\\" in relative or ":" in relative or "\x00" in relative):
            raise DeploymentError(f"Unsafe package path: {relative!r}")
        return path.as_posix()

    def export_project(
        self,
        source_root: str | Path,
        package_path: str | Path,
        *,
        project_id: str,
        project_name: str,
        source_core_version: str,
        required_modules: tuple[str, ...] | list[str] = (),
    ) -> Path:
        source = Path(source_root).expanduser().resolve()
        output = Path(package_path).expanduser().resolve()
        if not source.is_dir():
            raise DeploymentError("Project source directory does not exist")
        if output == source or source in output.parents:
            raise DeploymentError("Package must be created outside the source project")
        if not project_id.strip() or not project_name.strip() or not source_core_version.strip():
            raise DeploymentError("Project ID, name and source Core version are required")

        entries: dict[str, dict[str, Any]] = {}
        selected: list[tuple[str, Path]] = []
        total = 0
        for item in sorted(source.rglob("*")):
            if item.is_symlink():
                raise DeploymentError(f"Symbolic links are not allowed: {item}")
            if not item.is_file():
                continue
            relative = self._safe_relative(item.relative_to(source).as_posix())
            if self._is_secret(relative):
                continue
            size = item.stat().st_size
            if size > self.MAX_FILE_BYTES:
                raise DeploymentError(f"File exceeds package limit: {relative}")
            total += size
            if total > self.MAX_TOTAL_BYTES:
                raise DeploymentError("Project exceeds maximum package size")
            data = item.read_bytes()
            entries[relative] = {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data)}
            selected.append((relative, item))
            if len(selected) > self.MAX_FILES:
                raise DeploymentError("Project contains too many files")

        manifest = {
            "format": "AVIC_PROJECT_PACKAGE",
            "format_version": self.FORMAT_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "project": {"id": project_id, "name": project_name},
            "source_core_version": source_core_version,
            "required_modules": sorted(set(required_modules)),
            "site_profile": {
                "included": False,
                "instruction": "Create or select a target-site profile during import. No IPs or credentials are embedded.",
            },
            "security": {
                "secrets_included": False,
                "integrity": "SHA-256 per file",
                "authenticity": "unsigned; verify package provenance out-of-band",
            },
            "file_count": len(entries),
            "total_bytes": total,
            "files": entries,
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=output.name + ".", suffix=".tmp", dir=str(output.parent))
        os.close(fd)
        try:
            with zipfile.ZipFile(temp_name, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
                archive.writestr(self.MANIFEST, json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
                for relative, item in selected:
                    archive.write(item, f"{self.PAYLOAD}/{relative}")
            self.inspect_package(temp_name)
            os.replace(temp_name, output)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return output

    def _read_package(self, package_path: str | Path):
        try:
            archive = zipfile.ZipFile(package_path, "r")
        except (OSError, zipfile.BadZipFile) as exc:
            raise DeploymentError("Package cannot be opened") from exc
        with archive:
            infos = archive.infolist()
            names = [item.filename for item in infos]
            if len(names) != len(set(names)):
                raise DeploymentError("Package contains duplicate archive entries")
            if len(infos) > self.MAX_FILES + 1:
                raise DeploymentError("Package contains too many entries")
            if self.MANIFEST not in names:
                raise DeploymentError("AVIC package manifest is missing")
            try:
                manifest = json.loads(archive.read(self.MANIFEST))
            except Exception as exc:
                raise DeploymentError("Package manifest is invalid") from exc
            if manifest.get("format") != "AVIC_PROJECT_PACKAGE" or manifest.get("format_version") != self.FORMAT_VERSION:
                raise DeploymentError("Unsupported AVIC package format")
            expected = manifest.get("files")
            if not isinstance(expected, dict) or manifest.get("file_count") != len(expected):
                raise DeploymentError("Manifest file inventory is inconsistent")
            expected_names = {f"{self.PAYLOAD}/{self._safe_relative(k)}" for k in expected}
            actual_names = set(names) - {self.MANIFEST}
            if actual_names != expected_names:
                raise DeploymentError("Archive contents do not match the manifest")
            contents: dict[str, bytes] = {}
            total = 0
            for info in infos:
                if info.filename == self.MANIFEST:
                    continue
                if info.is_dir():
                    raise DeploymentError("Explicit directory entries are not accepted")
                mode = (info.external_attr >> 16) & 0o170000
                if mode == 0o120000:
                    raise DeploymentError("Symbolic links are not allowed in packages")
                relative = info.filename[len(self.PAYLOAD) + 1:]
                self._safe_relative(relative)
                if self._is_secret(relative):
                    raise DeploymentError(f"Package unexpectedly contains a secret-like file: {relative}")
                if info.file_size > self.MAX_FILE_BYTES:
                    raise DeploymentError(f"Package file exceeds size limit: {relative}")
                total += info.file_size
                if total > self.MAX_TOTAL_BYTES:
                    raise DeploymentError("Package exceeds maximum uncompressed size")
                data = archive.read(info)
                metadata = expected[relative]
                if len(data) != metadata.get("size") or hashlib.sha256(data).hexdigest() != metadata.get("sha256"):
                    raise DeploymentError(f"Integrity check failed: {relative}")
                contents[relative] = data
            if total != manifest.get("total_bytes"):
                raise DeploymentError("Package total size does not match manifest")
            return manifest, contents, total

    def inspect_package(
        self,
        package_path: str | Path,
        *,
        target_core_version: str | None = None,
        installed_modules: tuple[str, ...] | list[str] | None = None,
    ) -> DeploymentPreview:
        manifest, contents, total = self._read_package(package_path)
        required = tuple(manifest.get("required_modules", ()))
        warnings: list[str] = []
        compatible = True
        if target_core_version and target_core_version != manifest.get("source_core_version"):
            # Until explicit migration compatibility ranges are defined, fail closed.
            compatible = False
            warnings.append("Core version differs; an explicit compatibility/migration rule is required")
        if installed_modules is not None:
            missing = sorted(set(required) - set(installed_modules))
            if missing:
                compatible = False
                warnings.append("Missing required modules: " + ", ".join(missing))
        if manifest.get("security", {}).get("secrets_included") is not False:
            compatible = False
            warnings.append("Package security metadata does not confirm secret exclusion")
        package_id = hashlib.sha256(Path(package_path).read_bytes()).hexdigest()[:20]
        project = manifest.get("project", {})
        return DeploymentPreview(
            package_id=package_id,
            project_id=str(project.get("id", "")),
            project_name=str(project.get("name", "")),
            package_version=self.FORMAT_VERSION,
            source_core_version=str(manifest.get("source_core_version", "")),
            required_modules=required,
            file_count=len(contents),
            total_bytes=total,
            files=tuple(sorted(contents)),
            compatible=compatible,
            warnings=tuple(warnings),
        )

    def stage_import(
        self,
        package_path: str | Path,
        target_root: str | Path,
        *,
        expected_package_id: str,
        target_core_version: str,
        installed_modules: tuple[str, ...] | list[str] = (),
        site_profile: dict[str, Any] | None = None,
    ) -> Path:
        preview = self.inspect_package(
            package_path, target_core_version=target_core_version, installed_modules=installed_modules
        )
        if preview.package_id != expected_package_id:
            raise DeploymentError("Package changed after preview; import cancelled")
        if not preview.compatible:
            raise DeploymentError("Package is not compatible with this target: " + "; ".join(preview.warnings))
        if site_profile is not None:
            if not isinstance(site_profile, dict) or any(
                not isinstance(k, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", k)
                for k in site_profile
            ) or any(not (v is None or isinstance(v, (str, int, float, bool))) for v in site_profile.values()):
                raise DeploymentError("Site profile must be a flat object with safe keys and scalar values")
            # Secrets are not persisted in the project package. A separate site-profile
            # store/secret vault will be added before network driver activation is enabled.
            forbidden = {"password", "secret", "token", "private_key", "credential"}
            if any(any(word in key.lower() for word in forbidden) for key in site_profile):
                raise DeploymentError("Credentials must be provisioned through the target SecretStore")

        _, contents, _ = self._read_package(package_path)
        target = Path(target_root).expanduser().resolve()
        if target.exists() and any(target.iterdir()):
            raise DeploymentError("Import target must be new or empty; active projects are never overwritten")
        target.parent.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=target.name + ".stage.", dir=str(target.parent)))
        try:
            for relative, data in contents.items():
                destination = stage / Path(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                with destination.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
            import_record = {
                "package_id": preview.package_id,
                "project_id": preview.project_id,
                "imported_at": datetime.now(timezone.utc).isoformat(),
                "target_core_version": target_core_version,
                "site_profile": site_profile or {},
                "activation": "STAGED_NOT_ACTIVATED",
            }
            (stage / ".avic-deployment.json").write_text(
                json.dumps(import_record, ensure_ascii=False, sort_keys=True, indent=2), encoding="utf-8"
            )
            if target.exists():
                target.rmdir()
            os.replace(stage, target)
            return target
        finally:
            if stage.exists():
                shutil.rmtree(stage, ignore_errors=True)
