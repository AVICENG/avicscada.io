from __future__ import annotations

import hmac
import multiprocessing
from multiprocessing.connection import Connection
from multiprocessing.process import BaseProcess
from secrets import token_urlsafe
from threading import RLock
from time import monotonic
from typing import Any
from uuid import uuid4


class FieldRuntimeProcessError(RuntimeError):
    """Field Runtime process or IPC protocol failure."""


def _agent_main(connection: Connection, maintenance_token: str, heartbeat_interval: float) -> None:
    started = monotonic()
    sequence = 0
    state = "RUNNING"
    last_heartbeat = started
    try:
        connection.send({"ok": True, "event": "READY", "pid": __import__("os").getpid(),
                        "execution_engine_attached": False})
        while state == "RUNNING":
            if connection.poll(heartbeat_interval):
                try:
                    request = connection.recv()
                except EOFError:
                    # Supervisor/Workbench disconnection is NOT a stop request.
                    # The field process remains alive and continues its own service loop.
                    connection = None
                    while state == "RUNNING":
                        import time
                        time.sleep(heartbeat_interval)
                    break
                if not isinstance(request, dict) or request.get("protocol") != 1:
                    continue
                command = request.get("command")
                request_id = request.get("request_id")
                sequence = max(sequence, int(request.get("sequence", sequence)))
                last_heartbeat = monotonic()
                if command in {"ping", "status"}:
                    response = {"ok": True, "request_id": request_id, "protocol": 1,
                                "state": state, "pid": __import__("os").getpid(),
                                "uptime_seconds": max(0.0, monotonic() - started),
                                "last_command_sequence": sequence,
                                "last_heartbeat_monotonic": last_heartbeat,
                                "active_strategies": 0,
                                "execution_engine_attached": False,
                                "capability_state": "PROCESS_HOST_ONLY"}
                    if connection is not None:
                        connection.send(response)
                elif command == "maintenance_stop":
                    supplied = str(request.get("maintenance_token", ""))
                    confirmed = request.get("confirmation") == "STOP FIELD RUNTIME"
                    if not confirmed or not hmac.compare_digest(supplied, maintenance_token):
                        if connection is not None:
                            connection.send({"ok": False, "request_id": request_id,
                                             "error": "maintenance authorization rejected"})
                    else:
                        state = "STOPPED"
                        if connection is not None:
                            connection.send({"ok": True, "request_id": request_id,
                                             "state": state, "event": "MAINTENANCE_STOPPED"})
                else:
                    if connection is not None:
                        connection.send({"ok": False, "request_id": request_id,
                                         "error": "unsupported command"})
            else:
                # A heartbeat tick is deliberately independent of the supervisor link.
                last_heartbeat = monotonic()
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass


class FieldRuntimeProcess:
    """Owns a separate OS process for the Field Runtime service boundary.

    DEV178 intentionally hosts only the process/IPC/watchdog boundary. The FBD
    execution engine is not attached yet; status reports this explicitly.
    """

    def __init__(self, *, heartbeat_interval: float = 0.25, startup_timeout: float = 5.0):
        if not 0.05 <= float(heartbeat_interval) <= 5.0:
            raise ValueError("heartbeat_interval должен быть от 0.05 до 5 секунд")
        if not 0.5 <= float(startup_timeout) <= 30.0:
            raise ValueError("startup_timeout должен быть от 0.5 до 30 секунд")
        self.heartbeat_interval = float(heartbeat_interval)
        self.startup_timeout = float(startup_timeout)
        self._context = multiprocessing.get_context("spawn")
        self._process: BaseProcess | None = None
        self._connection: Connection | None = None
        self._maintenance_token = token_urlsafe(32)
        self._sequence = 0
        self._lock = RLock()

    @property
    def pid(self) -> int | None:
        return self._process.pid if self._process is not None else None

    def start(self) -> dict[str, Any]:
        with self._lock:
            if self._process is not None and self._process.is_alive():
                return self.status()
            parent, child = self._context.Pipe(duplex=True)
            process = self._context.Process(
                target=_agent_main, args=(child, self._maintenance_token, self.heartbeat_interval),
                name="AVIC-FieldRuntime", daemon=False,
            )
            process.start()
            child.close()
            self._process = process
            self._connection = parent
            if not parent.poll(self.startup_timeout):
                process.terminate()
                process.join(timeout=2.0)
                parent.close()
                self._connection = None
                raise FieldRuntimeProcessError("Field Runtime не подтвердил запуск")
            ready = parent.recv()
            if not isinstance(ready, dict) or not ready.get("ok") or ready.get("event") != "READY":
                process.terminate()
                process.join(timeout=2.0)
                parent.close()
                self._connection = None
                raise FieldRuntimeProcessError("Некорректное подтверждение запуска Field Runtime")
            return {**ready, "state": "RUNNING", "capability_state": "PROCESS_HOST_ONLY"}

    def _request(self, command: str, *, timeout: float = 2.0, **payload: Any) -> dict[str, Any]:
        with self._lock:
            process, connection = self._process, self._connection
            if process is None or not process.is_alive() or connection is None:
                raise FieldRuntimeProcessError("Field Runtime process или IPC недоступен")
            self._sequence += 1
            request_id = str(uuid4())
            connection.send({"protocol": 1, "command": command, "request_id": request_id,
                             "sequence": self._sequence, **payload})
            if not connection.poll(timeout):
                raise FieldRuntimeProcessError(f"Тайм-аут ответа Field Runtime: {command}")
            response = connection.recv()
            if not isinstance(response, dict) or response.get("request_id") != request_id:
                raise FieldRuntimeProcessError("Нарушена корреляция IPC-ответа Field Runtime")
            if not response.get("ok"):
                raise FieldRuntimeProcessError(str(response.get("error", "Field Runtime command failed")))
            return response

    def status(self) -> dict[str, Any]:
        return self._request("status")

    def ping(self) -> dict[str, Any]:
        return self._request("ping")

    def disconnect_supervisor(self) -> None:
        """Close only this IPC endpoint; never send a Field Runtime stop command."""
        with self._lock:
            if self._connection is not None:
                self._connection.close()
                self._connection = None

    def stop_for_maintenance(self, *, confirmation: str, maintenance_token: str) -> dict[str, Any]:
        if confirmation != "STOP FIELD RUNTIME":
            raise FieldRuntimeProcessError("Требуется точное подтверждение STOP FIELD RUNTIME")
        response = self._request("maintenance_stop", confirmation=confirmation,
                                 maintenance_token=maintenance_token)
        process = self._process
        if process is not None:
            process.join(timeout=2.0)
            if process.is_alive():
                raise FieldRuntimeProcessError("Field Runtime не завершился после maintenance stop")
        return response

    def close_ipc(self) -> None:
        """Release supervisor IPC resources without stopping the field process."""
        self.disconnect_supervisor()

    def _test_only_process_handle(self) -> BaseProcess | None:
        """Private test seam; production callers must use maintenance lifecycle."""
        return self._process

