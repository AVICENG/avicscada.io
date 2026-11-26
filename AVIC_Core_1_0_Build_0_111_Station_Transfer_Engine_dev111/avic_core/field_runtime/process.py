from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from secrets import token_urlsafe
from threading import RLock
from time import monotonic
from typing import Any
from uuid import uuid4


class FieldRuntimeProcessError(RuntimeError):
    """Field Runtime process or IPC protocol failure."""


def _recv_json(connection: socket.socket, reader) -> dict[str, Any]:
    raw = reader.readline(65537)
    if not raw:
        raise FieldRuntimeProcessError("Field Runtime IPC connection closed")
    if len(raw) > 65536:
        raise FieldRuntimeProcessError("Field Runtime IPC message exceeds 64 KiB")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FieldRuntimeProcessError("Invalid Field Runtime IPC JSON") from exc
    if not isinstance(value, dict):
        raise FieldRuntimeProcessError("Field Runtime IPC message must be an object")
    return value


class FieldRuntimeProcess:
    """Supervises a detached OS process; IPC disconnect never means field stop.

    DEV181 still hosts the process/IPC boundary only. FBD execution is not attached.
    """

    def __init__(self, *, heartbeat_interval: float = 0.25, startup_timeout: float = 5.0):
        if not 0.05 <= float(heartbeat_interval) <= 5.0:
            raise ValueError("heartbeat_interval должен быть от 0.05 до 5 секунд")
        if not 0.5 <= float(startup_timeout) <= 30.0:
            raise ValueError("startup_timeout должен быть от 0.5 до 30 секунд")
        self.heartbeat_interval = float(heartbeat_interval)
        self.startup_timeout = float(startup_timeout)
        self._maintenance_token = token_urlsafe(32)
        self._process: subprocess.Popen | None = None
        self._listener: socket.socket | None = None
        self._connection: socket.socket | None = None
        self._reader = None
        self._sequence = 0
        self._lock = RLock()
        self._started_at: float | None = None

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                return self.status()
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(("127.0.0.1", 0))
            listener.listen(2)
            listener.settimeout(self.startup_timeout)
            host, port = listener.getsockname()
            kwargs: dict[str, Any] = {"stdin": subprocess.PIPE, "stdout": subprocess.DEVNULL,
                                      "stderr": subprocess.DEVNULL, "close_fds": True}
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            else:
                kwargs["start_new_session"] = True
            process = subprocess.Popen(
                [sys.executable, "-m", "avic_core.field_runtime.agent",
                 "--host", str(host), "--port", str(port),
                 "--heartbeat", str(self.heartbeat_interval)], **kwargs,
            )
            assert process.stdin is not None
            process.stdin.write((self._maintenance_token + "\n").encode("utf-8"))
            process.stdin.flush()
            process.stdin.close()
            self._listener = listener
            self._process = process
            self._started_at = monotonic()
            try:
                self._accept_agent(timeout=self.startup_timeout)
                ready = self._request("status", timeout=self.startup_timeout)
            except Exception:
                process.terminate()
                process.wait(timeout=2.0)
                self._close_sockets()
                raise
            return ready

    def _accept_agent(self, *, timeout: float) -> None:
        if self._listener is None:
            raise FieldRuntimeProcessError("Field Runtime IPC listener is unavailable")
        self._listener.settimeout(timeout)
        deadline = monotonic() + timeout
        while monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                raise FieldRuntimeProcessError(f"Field Runtime process exited: {self._process.returncode}")
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            connection.settimeout(max(0.1, deadline - monotonic()))
            reader = connection.makefile("rb")
            try:
                hello = _recv_json(connection, reader)
                import hmac
                if hello.get("kind") != "hello" or not hmac.compare_digest(str(hello.get("token", "")), self._maintenance_token):
                    connection.close()
                    continue
                self._connection, self._reader = connection, reader
                return
            except Exception:
                connection.close()
                continue
        raise FieldRuntimeProcessError("Field Runtime agent did not connect before timeout")

    def _ensure_connection(self, timeout: float) -> None:
        if self._connection is not None:
            return
        self._accept_agent(timeout=timeout)

    def _request(self, command: str, *, timeout: float = 2.0, **payload: Any) -> dict[str, Any]:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                raise FieldRuntimeProcessError("Field Runtime process is not running")
            self._ensure_connection(timeout)
            assert self._connection is not None and self._reader is not None
            self._sequence += 1
            request_id = str(uuid4())
            request = {"protocol": 1, "command": command, "request_id": request_id,
                       "sequence": self._sequence, **payload}
            try:
                self._connection.sendall((json.dumps(request, separators=(",", ":")) + "\n").encode("utf-8"))
                self._connection.settimeout(timeout)
                response = _recv_json(self._connection, self._reader)
            except (OSError, TimeoutError, FieldRuntimeProcessError) as exc:
                self._drop_connection()
                raise FieldRuntimeProcessError(f"Field Runtime IPC failed for {command}: {exc}") from exc
            if response.get("request_id") != request_id:
                raise FieldRuntimeProcessError("Field Runtime IPC response correlation failed")
            if not response.get("ok"):
                raise FieldRuntimeProcessError(str(response.get("error", "Field Runtime command rejected")))
            return response

    def status(self) -> dict[str, Any]:
        return self._request("status")

    def ping(self) -> dict[str, Any]:
        return self._request("ping")

    def _drop_connection(self) -> None:
        if self._reader is not None:
            try: self._reader.close()
            except Exception: pass
        if self._connection is not None:
            try: self._connection.close()
            except Exception: pass
        self._reader = self._connection = None

    def disconnect_supervisor(self) -> None:
        """Drop only the control connection; the detached agent keeps running."""
        with self._lock:
            self._drop_connection()

    def stop_for_maintenance(self, *, confirmation: str, maintenance_token: str) -> dict[str, Any]:
        if confirmation != "STOP FIELD RUNTIME":
            raise FieldRuntimeProcessError("Требуется точное подтверждение STOP FIELD RUNTIME")
        response = self._request("maintenance_stop", confirmation=confirmation,
                                 maintenance_token=maintenance_token)
        process = self._process
        if process is not None:
            try:
                process.wait(timeout=2.0)
            except subprocess.TimeoutExpired as exc:
                raise FieldRuntimeProcessError("Field Runtime не завершился после maintenance stop") from exc
        self._close_sockets()
        return response

    def _close_sockets(self) -> None:
        self._drop_connection()
        if self._listener is not None:
            try: self._listener.close()
            except Exception: pass
            self._listener = None

    def _test_only_process_handle(self) -> subprocess.Popen | None:
        return self._process

