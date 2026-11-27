"""Managed polling lifecycle for synchronous read-only driver adapters."""
from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any


class PollingSession:
    """Single-worker, non-overlapping polling loop with explicit start/stop.

    The adapter remains responsible for per-point quality transitions. This
    supervisor only owns scheduling, lifecycle and aggregate diagnostics.
    """

    def __init__(self, adapter: Any, interval_seconds: float, *, name: str = "avic-driver-poller") -> None:
        if not 0.1 <= float(interval_seconds) <= 86400:
            raise ValueError("poll interval must be between 0.1 and 86400 seconds")
        if not callable(getattr(adapter, "poll_once", None)):
            raise TypeError("adapter must expose poll_once()")
        self.adapter = adapter
        self.interval_seconds = float(interval_seconds)
        self.name = name.strip() or "avic-driver-poller"
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._started_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._state = "STOPPED"
        self._poll_count = 0
        self._success_count = 0
        self._failure_count = 0
        self._last_started_at: str | None = None
        self._last_completed_at: str | None = None
        self._last_error: str | None = None
        self._last_result: dict | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                if self._state == "STOPPING":
                    raise RuntimeError("driver polling worker is stopping")
            else:
                self._stop_event.clear()
                self._started_event.clear()
                self._state = "STARTING"
                self._thread = threading.Thread(target=self._run, name=self.name, daemon=True)
                self._thread.start()
        if not self._started_event.wait(timeout=2.0):
            try:
                self.stop(timeout=2.0)
            finally:
                raise TimeoutError("driver polling worker did not enter RUNNING state")

    def _run(self) -> None:
        with self._lock:
            self._state = "RUNNING"
            self._started_event.set()
        next_tick = time.monotonic()
        while not self._stop_event.is_set():
            with self._lock:
                self._last_started_at = datetime.now(timezone.utc).isoformat()
            try:
                result = self.adapter.poll_once()
                results = result.get("results", []) if isinstance(result, dict) else []
                failures = sum(1 for item in results if isinstance(item, dict) and item.get("ok") is False)
                with self._lock:
                    self._poll_count += 1
                    self._success_count += max(0, len(results) - failures)
                    self._failure_count += failures
                    self._last_result = result if isinstance(result, dict) else {"result": result}
                    self._last_error = None
                    self._state = "DEGRADED" if failures else "RUNNING"
            except Exception as exc:
                with self._lock:
                    self._poll_count += 1
                    self._failure_count += 1
                    self._last_error = f"{type(exc).__name__}: {exc}"
                    self._state = "DEGRADED"
            with self._lock:
                self._last_completed_at = datetime.now(timezone.utc).isoformat()

            # Keep a fixed-rate schedule while on time. If a poll overruns its
            # slot, wait a full interval after completion instead of immediately
            # issuing a catch-up request to a slow or overloaded controller.
            next_tick += self.interval_seconds
            now = time.monotonic()
            if next_tick <= now:
                next_tick = now + self.interval_seconds
            delay = max(0.0, next_tick - time.monotonic())
            if self._stop_event.wait(delay):
                break
        with self._lock:
            self._state = "STOPPED"

    def stop(self, timeout: float = 5.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        with self._lock:
            thread = self._thread
            if thread is None or not thread.is_alive():
                self._state = "STOPPED"
                return
            self._state = "STOPPING"
            self._stop_event.set()
        thread.join(timeout)
        if thread.is_alive():
            with self._lock:
                self._state = "STOPPING"
            raise TimeoutError("driver polling worker did not stop before timeout")
        with self._lock:
            self._thread = None
            self._state = "STOPPED"

    def diagnostics(self) -> dict:
        with self._lock:
            alive = self._thread is not None and self._thread.is_alive()
            return {
                "state": self._state,
                "worker_alive": alive,
                "interval_seconds": self.interval_seconds,
                "poll_count": self._poll_count,
                "success_count": self._success_count,
                "failure_count": self._failure_count,
                "last_started_at": self._last_started_at,
                "last_completed_at": self._last_completed_at,
                "last_error": self._last_error,
                "last_result": self._last_result,
            }

    def __enter__(self) -> "PollingSession":
        self.start()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()


class EventDrivenSession:
    """Lifecycle supervisor for callback-driven transports such as MQTT.

    Unlike PollingSession this does not invent a polling loop: the adapter owns
    its network event loop and reports connection health through diagnostics.
    """

    def __init__(self, adapter: Any, *, name: str = "avic-event-driver") -> None:
        if not callable(getattr(adapter, "start", None)) or not callable(getattr(adapter, "stop", None)):
            raise TypeError("event-driven adapter must expose start() and stop()")
        self.adapter = adapter
        self.name = name.strip() or "avic-event-driver"
        self._lock = threading.RLock()
        self._state = "STOPPED"
        self._started_at: str | None = None
        self._last_error: str | None = None

    def start(self) -> None:
        with self._lock:
            if self._state in {"STARTING", "RUNNING", "DEGRADED"}:
                return
            self._state = "STARTING"
        try:
            self.adapter.start()
        except Exception as exc:
            with self._lock:
                self._state = "ERROR"
                self._last_error = f"{type(exc).__name__}: {exc}"
            raise
        with self._lock:
            self._state = "RUNNING"
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._last_error = None

    def stop(self, timeout: float = 5.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        with self._lock:
            if self._state == "STOPPED":
                return
            self._state = "STOPPING"
        try:
            self.adapter.stop()
        except Exception as exc:
            with self._lock:
                self._state = "ERROR"
                self._last_error = f"{type(exc).__name__}: {exc}"
            raise
        with self._lock:
            self._state = "STOPPED"

    def diagnostics(self) -> dict:
        with self._lock:
            adapter_status = self.adapter.diagnostics() if callable(getattr(self.adapter, "diagnostics", None)) else {}
            connected = adapter_status.get("connected")
            state = self._state
            if state in {"RUNNING", "DEGRADED"} and connected is False:
                state = "DEGRADED"
            return {
                "state": state, "worker_alive": state in {"RUNNING", "DEGRADED"},
                "event_driven": True, "started_at": self._started_at,
                "last_error": self._last_error, "adapter": adapter_status,
            }
