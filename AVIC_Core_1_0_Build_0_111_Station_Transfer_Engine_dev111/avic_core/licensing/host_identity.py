
"""Stable, privacy-preserving AVIC installation Host ID for Windows/Linux/macOS."""
from __future__ import annotations

import hashlib
import csv
import json
import os
import platform
import re
import subprocess
import uuid

from pathlib import Path
from typing import Callable


def _set_windows_identity_acl(path: Path, user_sid: str, *, is_directory: bool) -> None:
    """Apply a protected DACL using explicit numeric SIDs; never grant Local Account."""
    if not re.fullmatch(r"S-1-5-21-(?:\\d+-){2,}\\d+", user_sid):
        raise HostIdentityError("Некорректный Windows user SID для ACL installation identity")

    inheritance = "(OI)(CI)" if is_directory else ""
    permission = f"{inheritance}F"
    # Remove the broad Local Account group if an older installation created it.
    # The next command disables inheritance and replaces grants for the exact
    # current user, Local System and Builtin Administrators.
    subprocess.run(
        ["icacls", str(path), "/remove:g", "*S-1-5-113"],
        capture_output=True, text=True, timeout=10,
    )
    grants = [
        f"*{user_sid}:{permission}",
        f"*S-1-5-18:{permission}",
        f"*S-1-5-32-544:{permission}",
    ]
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", *grants],
            check=True, capture_output=True, text=True, timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise HostIdentityError(
            f"Не удалось установить защищённый ACL installation identity: {exc}"
        ) from exc

class HostIdentityError(RuntimeError):
    """Raised when a stable machine identity cannot safely be obtained."""


def _machine_fingerprint() -> str:
    system = platform.system().lower()
    value = ""

    if system == "windows":
        try:
            import winreg  # type: ignore

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as key:
                value, _ = winreg.QueryValueEx(key, "MachineGuid")

        except Exception as exc:
            raise HostIdentityError(
                "Не удалось прочитать Windows MachineGuid"
            ) from exc

    elif system == "linux":
        for candidate in (
            Path("/etc/machine-id"),
            Path("/var/lib/dbus/machine-id"),
        ):
            try:
                value = candidate.read_text(encoding="ascii").strip()
                if value:
                    break
            except OSError:
                continue

        if not value:
            raise HostIdentityError(
                "Не удалось прочитать Linux machine-id"
            )

    elif system == "darwin":
        try:
            result = subprocess.run(
                [
                    "ioreg",
                    "-rd1",
                    "-c",
                    "IOPlatformExpertDevice",
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=5,
            )

            match = re.search(
                r'"IOPlatformUUID"\s*=\s*"([^"]+)"',
                result.stdout,
            )
            value = match.group(1) if match else ""

        except Exception as exc:
            raise HostIdentityError(
                "Не удалось прочитать macOS platform UUID"
            ) from exc

        if not value:
            raise HostIdentityError(
                "macOS platform UUID отсутствует"
            )

    else:
        raise HostIdentityError(
            f"ОС не поддерживается для Host ID: {platform.system()}"
        )

    normalized = re.sub(
        r"[^a-zA-Z0-9-]",
        "",
        str(value),
    ).lower()

    if len(normalized) < 8:
        raise HostIdentityError(
            "Системный идентификатор компьютера некорректен"
        )

    return normalized


class HostIdentity:
    """Binds a persisted installation nonce to the OS machine identifier.

    Raw OS identifiers and installation nonce are never returned or logged.
    Copying the AVIC data directory to another computer produces another Host ID.
    """

    def __init__(
        self,
        data_dir: str | Path,
        machine_id_provider: Callable[[], str] | None = None,
    ):
        self.data_dir = Path(data_dir)
        self._provider = machine_id_provider or _machine_fingerprint

    def _installation_id(self) -> str:
        identity_dir = self.data_dir / "identity"
        identity_file = identity_dir / "installation_id"

        try:
            identity_dir.mkdir(parents=True, exist_ok=True)

            current_sid = None
            if os.name == "nt":
                who = subprocess.run(
                    ["whoami", "/user", "/fo", "csv", "/nh"],
                    check=True, capture_output=True, text=True, timeout=10,
                )
                rows = list(csv.reader(line for line in who.stdout.splitlines() if line.strip()))
                current_sid = rows[0][-1].strip() if rows and rows[0] else ""
                if not re.fullmatch(r"S-1-5-21-(?:\d+-){2,}\d+", current_sid):
                    raise HostIdentityError(
                        "Не удалось определить точный Windows user SID для ACL installation identity"
                    )

                # Set a protected DACL through Windows Security APIs. This removes
                # every previous ACE and grants FullControl only to the current
                # user, Local System and Builtin Administrators. OI/CI ACE flags
                # protect newly created child files and directories as well.
                _set_windows_identity_acl(identity_dir, current_sid, is_directory=True)
                if identity_file.exists():
                    _set_windows_identity_acl(identity_file, current_sid, is_directory=False)

            if identity_file.exists():
                return str(
                    uuid.UUID(
                        identity_file.read_text(
                            encoding="ascii"
                        ).strip()
                    )
                )

            value = str(uuid.uuid4())

            fd = os.open(
                str(identity_file),
                os.O_WRONLY | os.O_CREAT | os.O_EXCL,
                0o600,
            )

            with os.fdopen(
                fd,
                "w",
                encoding="ascii",
            ) as stream:
                stream.write(value)
                stream.flush()
                os.fsync(stream.fileno())

            if current_sid:
                _set_windows_identity_acl(identity_file, current_sid, is_directory=False)

            return value

        except FileExistsError:
            return str(
                uuid.UUID(
                    identity_file.read_text(
                        encoding="ascii"
                    ).strip()
                )
            )

        except HostIdentityError:
            raise

        except (
            OSError,
            ValueError,
            subprocess.SubprocessError,
        ) as exc:
            raise HostIdentityError(
                "Не удалось создать/прочитать AVIC installation identity"
            ) from exc

    def get_host_id(self) -> str:
        machine_id = self._provider()

        if (
            not isinstance(machine_id, str)
            or len(machine_id.strip()) < 8
        ):
            raise HostIdentityError(
                "Machine identity provider вернул некорректное значение"
            )

        material = {
            "product": "AVIC-SCADA",
            "identity_version": 1,
            "machine": machine_id.strip().lower(),
            "installation": self._installation_id(),
        }

        digest = hashlib.sha256(
            json.dumps(
                material,
                sort_keys=True,
                separators=(",", ":"),
            ).encode()
        ).hexdigest()[:32].upper()

        return "AVIC-" + "-".join(
            digest[i:i + 8]
            for i in range(0, 32, 8)
        )
