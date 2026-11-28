"""Cross-process exclusive leases for AVIC serial field buses."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
from threading import RLock


class SerialPortBusyError(RuntimeError):
    """Raised when another AVIC runtime owns the requested serial port."""


class SerialPortLease:
    """OS-backed advisory lock held for the complete lifetime of a serial driver.

    The lock is process-safe on supported Windows and POSIX hosts. Lock files are
    deliberately persistent: the kernel releases the lock when a process exits,
    so deleting the file is unnecessary and could introduce inode races.
    """

    _registry_lock = RLock()
    _registry: set[str] = set()

    def __init__(self, serial_port: str) -> None:
        if not isinstance(serial_port, str) or not serial_port.strip():
            raise ValueError("serial_port is required")
        raw = serial_port.strip()
        if os.name == "nt":
            normalized = raw.replace("/", "\\").strip()
            # libmodbus and Win32 accept both COM12 and \\.\COM12.
            # They are the same physical port and must share one AVIC lease.
            if normalized.casefold().startswith("\\\\.\\"):
                normalized = normalized[4:]
            if normalized.casefold().startswith("com") and normalized[3:].isdigit():
                normalized = f"COM{int(normalized[3:])}"
            self.identity = normalized.casefold()
        else:
            self.identity = os.path.realpath(os.path.abspath(raw))
        digest = hashlib.sha256(self.identity.encode("utf-8")).hexdigest()
        self.lock_dir = Path(tempfile.gettempdir()) / "avic-core-serial-locks"
        self.lock_path = self.lock_dir / f"{digest}.lock"
        self._stream = None
        self._held = False

    def acquire(self) -> "SerialPortLease":
        with self._registry_lock:
            if self.identity in self._registry:
                raise SerialPortBusyError(f"Serial port is already owned by AVIC: {self.identity}")
            self._registry.add(self.identity)
        try:
            self.lock_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
            self._stream = self.lock_path.open("a+b")
            if self._stream.seek(0, os.SEEK_END) == 0:
                self._stream.write(b"\0")
                self._stream.flush()
            self._stream.seek(0)
            if os.name == "nt":
                import msvcrt
                try:
                    msvcrt.locking(self._stream.fileno(), msvcrt.LK_NBLCK, 1)
                except OSError as exc:
                    raise SerialPortBusyError(
                        f"Serial port is locked by another AVIC process: {self.identity}"
                    ) from exc
            else:
                import fcntl
                try:
                    fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except OSError as exc:
                    raise SerialPortBusyError(
                        f"Serial port is locked by another AVIC process: {self.identity}"
                    ) from exc
            self._held = True
            return self
        except Exception:
            if self._stream is not None:
                self._stream.close()
                self._stream = None
            with self._registry_lock:
                self._registry.discard(self.identity)
            raise

    def release(self) -> None:
        if not self._held:
            return
        stream = self._stream
        if stream is None:
            raise RuntimeError("Serial port lease is marked held without an open lock handle")

        # If the explicit unlock fails, keep the handle open and retain the
        # in-process registry entry. Closing it in a finally block would release
        # the kernel lock and allow another process onto a bus still owned by a
        # Worker whose shutdown/cleanup has not been confirmed.
        stream.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

        self._held = False
        try:
            stream.close()
        finally:
            self._stream = None
            with self._registry_lock:
                self._registry.discard(self.identity)

    def __enter__(self) -> "SerialPortLease":
        return self.acquire()

    def __exit__(self, *_: object) -> None:
        self.release()
