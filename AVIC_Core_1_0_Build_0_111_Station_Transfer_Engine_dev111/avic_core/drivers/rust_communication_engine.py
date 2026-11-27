"""Optional Rust-backed Modbus TCP transport over a supervised JSONL process."""
from __future__ import annotations

import ipaddress
import json
import queue
import subprocess
import threading
from pathlib import Path
from typing import Any


class RustCommunicationEngineError(RuntimeError):
    """The Rust communication engine returned an invalid or failed response."""


class RustModbusTcpClient:
    """Drop-in read-only client implementing the ModbusTcpClient read interface.

    The engine is a separately built executable. No silent Python fallback occurs:
    startup, protocol, or process failures are surfaced to Driver Manager.
    """

    engine_backend = "rust"

    def __init__(self, host: str, port: int = 502, *, unit_id: int = 1,
                 timeout: float = 2.0, engine_binary: str | Path):
        ipaddress.ip_address(host)
        if not 1 <= int(port) <= 65535 or not 0 <= int(unit_id) <= 247:
            raise ValueError("invalid Modbus TCP port or unit_id")
        if not 0.1 <= float(timeout) <= 10.0:
            raise ValueError("timeout must be in range 0.1..10 seconds")
        binary = Path(engine_binary).expanduser()
        if not binary.is_file():
            raise FileNotFoundError(f"Rust Communication Engine executable not found: {binary}")
        self.host, self.port, self.unit_id = host, int(port), int(unit_id)
        self.timeout, self.engine_binary = float(timeout), binary.resolve()
        self._lock = threading.RLock()
        self._process: subprocess.Popen[str] | None = None
        self._responses: queue.Queue[Any] = queue.Queue()
        self._reader: threading.Thread | None = None
        self._request_id = 0
        self._healthy = False

    def _start_locked(self) -> None:
        if self._process is not None and self._process.poll() is None:
            return
        self._responses = queue.Queue()
        process = subprocess.Popen(
            [str(self.engine_binary)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, encoding="utf-8", bufsize=1,
            shell=False,
        )
        self._process = process
        self._healthy = False

        def read_responses() -> None:
            try:
                assert process.stdout is not None
                for line in process.stdout:
                    try:
                        self._responses.put(json.loads(line))
                    except Exception as exc:
                        self._responses.put({"_reader_error": f"invalid JSON from Rust engine: {exc}"})
                        return
            finally:
                self._responses.put(None)

        self._reader = threading.Thread(
            target=read_responses, name="avic-rust-engine-reader", daemon=True
        )
        self._reader.start()

    def _terminate_locked(self) -> None:
        process, self._process = self._process, None
        self._healthy = False
        if process is not None:
            if process.poll() is None:
                process.kill()
                try:
                    process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    pass
            for pipe in (process.stdin, process.stdout):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass

    def _exchange_locked(self, payload: dict[str, Any]) -> dict[str, Any]:
        process = self._process
        if process is None or process.poll() is not None or process.stdin is None:
            raise RustCommunicationEngineError("Rust Communication Engine process is not running")
        self._request_id += 1
        request_id = self._request_id
        request = dict(payload, request_id=request_id)
        try:
            process.stdin.write(json.dumps(request, separators=(",", ":")) + "\n")
            process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            self._terminate_locked()
            raise RustCommunicationEngineError("cannot write to Rust Communication Engine") from exc
        try:
            response = self._responses.get(timeout=self.timeout + 1.0)
        except queue.Empty as exc:
            self._terminate_locked()
            raise TimeoutError("Rust Communication Engine response timed out") from exc
        if response is None:
            self._terminate_locked()
            raise RustCommunicationEngineError("Rust Communication Engine exited unexpectedly")
        if not isinstance(response, dict) or "_reader_error" in response:
            message = response.get("_reader_error", "invalid response") if isinstance(response, dict) else "invalid response"
            self._terminate_locked()
            raise RustCommunicationEngineError(str(message))
        if response.get("request_id") != request_id:
            self._terminate_locked()
            raise RustCommunicationEngineError("Rust engine response request_id mismatch")
        if response.get("ok") is not True:
            raise RustCommunicationEngineError(str(response.get("error") or "Rust engine request failed"))
        return response

    def _ensure_started_locked(self) -> None:
        if self._process is None or self._process.poll() is not None:
            self._start_locked()
        if not self._healthy:
            response = self._exchange_locked({"operation": "health"})
            if response.get("engine") != "avic-communication-engine":
                self._terminate_locked()
                raise RustCommunicationEngineError("unexpected Rust engine identity")
            capabilities = response.get("capabilities")
            if not isinstance(capabilities, list) or "modbus-tcp-read-1-4" not in capabilities:
                self._terminate_locked()
                raise RustCommunicationEngineError("Rust engine does not advertise Modbus read capability")
            self._healthy = True

    def _read(self, function: int, address: int, count: int) -> list[int]:
        if function not in (1, 2, 3, 4):
            raise ValueError("only Modbus read functions 1..4 are supported")
        maximum = 2000 if function in (1, 2) else 125
        if not 0 <= address <= 65535 or not 1 <= count <= maximum or address + count > 65536:
            raise ValueError("invalid Modbus address/count")
        with self._lock:
            self._ensure_started_locked()
            response = self._exchange_locked({
                "operation": "modbus_read", "host": self.host, "port": self.port,
                "unit_id": self.unit_id, "timeout_ms": int(self.timeout * 1000),
                "function": function, "address": address, "count": count,
            })
            values = response.get("values")
            if (not isinstance(values, list) or len(values) != count
                    or any(type(value) is not int or not 0 <= value <= 65535 for value in values)):
                self._terminate_locked()
                raise RustCommunicationEngineError("Rust engine returned invalid Modbus values")
            return values

    def read_coils(self, address: int, count: int = 1) -> list[int]:
        return self._read(1, address, count)

    def read_discrete_inputs(self, address: int, count: int = 1) -> list[int]:
        return self._read(2, address, count)

    def read_holding_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read(3, address, count)

    def read_input_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read(4, address, count)

    def close(self) -> None:
        with self._lock:
            if self._process is None:
                return
            try:
                if self._process.poll() is None:
                    self._exchange_locked({"operation": "shutdown"})
                    self._process.wait(timeout=1.0)
            except Exception:
                self._terminate_locked()
            finally:
                if self._process is not None and self._process.poll() is not None:
                    self._process = None
                    self._healthy = False

    def diagnostics(self) -> dict[str, Any]:
        with self._lock:
            running = self._process is not None and self._process.poll() is None
            return {
                "engine_backend": "rust",
                "engine_binary": str(self.engine_binary),
                "engine_process_running": running,
                "engine_healthy": self._healthy and running,
            }
