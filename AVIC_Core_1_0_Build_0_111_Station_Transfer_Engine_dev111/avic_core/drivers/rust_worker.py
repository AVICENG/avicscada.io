"""Supervised subprocess boundary for the AVIC Rust Driver Worker.

This class owns process lifecycle and IPC identity checks. It deliberately does
not publish samples: callers must validate each protocol result against the
configured DriverInstance/binding and publish through Point Runtime.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import queue
import os
import subprocess
import threading
from typing import Any, Sequence
from uuid import uuid4

from avic_core.drivers.ipc import (
    DriverEnvelope, DriverIpcError, SequenceGuard, read_frame, write_frame,
)


class RustWorkerError(RuntimeError):
    pass


class RustDriverWorker:
    """One isolated Rust worker process, one DriverInstance, one generation."""

    def __init__(
        self,
        command: Sequence[str],
        *,
        installation_id: str,
        project_id: str,
        station_id: str,
        driver_instance_id: str,
        generation: int,
        timeout_seconds: float = 5.0,
    ) -> None:
        if not command:
            raise ValueError("worker command is required")
        executable = Path(command[0])
        if not executable.is_absolute() or not executable.is_file():
            raise ValueError("Rust worker executable must be an existing absolute file path")
        if not all(isinstance(v, str) and v.strip() for v in (
            installation_id, project_id, station_id, driver_instance_id,
        )):
            raise ValueError("complete DriverInstance scope is required")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation <= 0:
            raise ValueError("worker generation must be positive")
        if not 0.1 <= float(timeout_seconds) <= 300:
            raise ValueError("worker timeout must be between 0.1 and 300 seconds")

        self.command = tuple(str(v) for v in command)
        self.installation_id = installation_id
        self.project_id = project_id
        self.station_id = station_id
        self.driver_instance_id = driver_instance_id
        self.worker_id = str(uuid4())
        self.generation = generation
        self.timeout_seconds = float(timeout_seconds)
        self._process: subprocess.Popen[bytes] | None = None
        self._responses: queue.Queue[tuple[bool, Any]] = queue.Queue(maxsize=128)
        self._request_sequence = 0
        self._response_guard = SequenceGuard()
        self._response_sequence_gaps = 0
        self._lock = threading.RLock()
        self._exchange_lock = threading.RLock()
        self._reader: threading.Thread | None = None
        self._stderr_reader: threading.Thread | None = None
        self._stderr_tail: deque[str] = deque(maxlen=100)
        self._started = False
        self._worker_version: str | None = None

    def start(self, config: dict[str, Any]) -> None:
        with self._lock:
            if self._process is not None:
                raise RustWorkerError("worker process has already been created")
            if not isinstance(config, dict):
                raise TypeError("worker config must be an object")
            inherited = os.environ
            safe_env = {
                key: inherited[key] for key in (
                    "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", "TMPDIR", "LANG", "LC_ALL",
                ) if key in inherited
            }
            self._process = subprocess.Popen(
                self.command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, bufsize=0, shell=False, env=safe_env,
                close_fds=True,
            )
            self._reader = threading.Thread(target=self._read_stdout, name="avic-rust-worker-stdout", daemon=True)
            self._stderr_reader = threading.Thread(target=self._read_stderr, name="avic-rust-worker-stderr", daemon=True)
            self._reader.start()
            self._stderr_reader.start()
        try:
            initialized = self._request("initialize", {})
            if initialized.kind != "initialized" or initialized.payload.get("protocol") != "avic.driver.ipc" or initialized.payload.get("version") != 1:
                raise RustWorkerError("Rust worker handshake protocol/version mismatch")
            self._worker_version = str(initialized.payload.get("worker_version") or "unknown")
            configured = self._request("configure", config)
            if configured.kind != "configured":
                raise RustWorkerError("Rust worker did not confirm configuration")
            started = self._request("start", {})
            if started.kind != "status" or started.payload.get("state") != "RUNNING":
                raise RustWorkerError("Rust worker did not enter RUNNING state")
            self._started = True
        except Exception:
            self._terminate()
            raise

    def _read_stdout(self) -> None:
        process = self._process
        if process is None or process.stdout is None:
            return
        try:
            while True:
                frame = read_frame(process.stdout)
                if frame is None:
                    # EOF can race the stderr-drain thread and process exit on Windows.
                    # Wait briefly so startup/loader/IPC rejection diagnostics are retained.
                    try:
                        process.wait(timeout=0.5)
                    except subprocess.TimeoutExpired:
                        pass
                    stderr_reader = self._stderr_reader
                    if stderr_reader is not None and stderr_reader is not threading.current_thread():
                        stderr_reader.join(timeout=0.25)
                    detail = list(self._stderr_tail)[-10:]
                    self._responses.put((
                        False,
                        f"worker stdout closed (exit_code={process.poll()}; stderr={detail})",
                    ))
                    return
                self._responses.put((True, frame))
        except Exception as exc:
            try:
                self._responses.put((False, f"{type(exc).__name__}: {exc}"))
            except Exception:
                pass

    def _read_stderr(self) -> None:
        process = self._process
        if process is None or process.stderr is None:
            return
        for raw in iter(process.stderr.readline, b""):
            # The worker must never log credentials; retain only a bounded tail
            # for operational diagnostics if it exits unexpectedly.
            self._stderr_tail.append(raw.decode("utf-8", errors="replace").rstrip())

    def _envelope(self, kind: str, payload: dict[str, Any]) -> DriverEnvelope:
        self._request_sequence += 1
        return DriverEnvelope(
            contract="avic.driver.ipc", version=1, message_id=str(uuid4()), kind=kind,
            installation_id=self.installation_id, project_id=self.project_id,
            station_id=self.station_id, driver_instance_id=self.driver_instance_id,
            worker_id=self.worker_id, generation=self.generation,
            sequence=self._request_sequence,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            correlation_id=None, payload=payload,
        )

    def _request(self, kind: str, payload: dict[str, Any]) -> DriverEnvelope:
        with self._exchange_lock:
            return self._request_serialized(kind, payload)

    def _request_serialized(self, kind: str, payload: dict[str, Any]) -> DriverEnvelope:
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None:
                raise RustWorkerError(f"Rust worker is not alive; stderr={list(self._stderr_tail)[-10:]}")
            if process.stdin is None:
                raise RustWorkerError("Rust worker stdin is unavailable")
            request = self._envelope(kind, payload)
            try:
                write_frame(process.stdin, request)
            except (BrokenPipeError, OSError) as exc:
                raise RustWorkerError(f"failed to send IPC request: {exc}") from exc

        try:
            ok, response = self._responses.get(timeout=self.timeout_seconds)
        except queue.Empty as exc:
            self._terminate()
            raise RustWorkerError(f"Rust worker timed out handling {kind}") from exc
        if not ok:
            self._terminate()
            raise RustWorkerError(f"Rust worker IPC closed: {response}; stderr={list(self._stderr_tail)[-10:]}")
        if not isinstance(response, DriverEnvelope):
            raise RustWorkerError("Rust worker returned an invalid IPC frame")
        if (
            response.installation_id != self.installation_id
            or response.project_id != self.project_id
            or response.station_id != self.station_id
            or response.driver_instance_id != self.driver_instance_id
            or response.worker_id != self.worker_id
            or response.generation != self.generation
            or response.correlation_id != request.message_id
        ):
            self._terminate()
            raise RustWorkerError("Rust worker response identity/correlation mismatch")
        try:
            if self._response_guard.accept(response.generation, response.sequence):
                self._response_sequence_gaps += 1
        except DriverIpcError as exc:
            self._terminate()
            raise RustWorkerError(f"Rust worker response sequence rejected: {exc}") from exc
        if response.kind == "error":
            raise RustWorkerError(str(response.payload.get("message") or response.payload.get("code") or "worker error"))
        return response

    def read(self, request: dict[str, Any]) -> dict[str, Any]:
        if not self._started:
            raise RustWorkerError("Rust worker is not started")
        if not isinstance(request, dict):
            raise TypeError("read request must be an object")
        response = self._request("read", request)
        if response.kind == "read_error":
            raise RustWorkerError(str(response.payload.get("message", "protocol read failed")))
        if response.kind != "read_result":
            raise RustWorkerError(f"unexpected worker response: {response.kind}")
        return response.payload

    def diagnostics(self) -> dict[str, Any]:
        process = self._process
        return {
            "worker_id": self.worker_id,
            "worker_version": self._worker_version,
            "generation": self.generation,
            "response_sequence_gaps": self._response_sequence_gaps,
            "started": self._started,
            "process_alive": process is not None and process.poll() is None,
            "exit_code": process.poll() if process is not None else None,
            "stderr_tail": list(self._stderr_tail)[-10:],
        }

    def _terminate(self) -> None:
        process = self._process
        self._started = False
        if process is None:
            return
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass

    def close(self) -> None:
        process = self._process
        if process is None:
            return
        if process.poll() is None:
            try:
                self._request("stop", {})
                self._request("shutdown", {})
                process.wait(timeout=2)
            except Exception:
                self._terminate()
        self._started = False
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                try:
                    stream.close()
                except OSError:
                    pass

    def __enter__(self) -> "RustDriverWorker":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
