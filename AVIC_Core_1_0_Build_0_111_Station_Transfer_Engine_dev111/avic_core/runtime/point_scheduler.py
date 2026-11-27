from __future__ import annotations

from threading import Event, RLock, Thread
from time import monotonic


class PointRuntimeScheduler:
    """Explicit lifecycle scheduler for due Point Runtime filtering transitions.

    The debounce state machine itself owns no timer thread. DriverManager owns this
    scheduler and starts it while at least one polling driver is active. One bounded
    worker services all points/stations; it never performs network I/O or field writes.
    """

    def __init__(self, point_runtime, *, interval_seconds: float = 0.025):
        if not 0.01 <= float(interval_seconds) <= 1.0:
            raise ValueError("interval_seconds must be between 0.01 and 1.0")
        self.point_runtime = point_runtime
        self.interval_seconds = float(interval_seconds)
        self._lock = RLock()
        self._stop = Event()
        self._thread: Thread | None = None
        self._tick_count = 0
        self._failure_count = 0
        self._last_error: str | None = None
        self._last_tick_monotonic: float | None = None

    def start(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop.clear()
            self._thread = Thread(
                target=self._run, name="avic-point-runtime-scheduler", daemon=True
            )
            self._thread.start()

    def _run(self) -> None:
        next_tick = monotonic()
        while not self._stop.is_set():
            try:
                self.point_runtime.flush_debounce()
                with self._lock:
                    self._tick_count += 1
                    self._last_error = None
                    self._last_tick_monotonic = monotonic()
            except Exception as exc:
                with self._lock:
                    self._failure_count += 1
                    self._last_error = f"{type(exc).__name__}: {exc}"
                    self._last_tick_monotonic = monotonic()
            next_tick += self.interval_seconds
            current = monotonic()
            if next_tick <= current:
                next_tick = current + self.interval_seconds
            self._stop.wait(max(0.0, next_tick - monotonic()))

    def stop(self, *, timeout: float = 5.0) -> None:
        if timeout <= 0:
            raise ValueError("timeout must be positive")
        with self._lock:
            thread = self._thread
            if thread is None or not thread.is_alive():
                self._thread = None
                return
            self._stop.set()
        thread.join(timeout)
        if thread.is_alive():
            raise TimeoutError("Point Runtime scheduler did not stop before timeout")
        with self._lock:
            self._thread = None

    def diagnostics(self) -> dict:
        with self._lock:
            alive = self._thread is not None and self._thread.is_alive()
            return {
                "state": "RUNNING" if alive else "STOPPED",
                "worker_alive": alive,
                "interval_seconds": self.interval_seconds,
                "tick_count": self._tick_count,
                "failure_count": self._failure_count,
                "last_error": self._last_error,
                "last_tick_monotonic": self._last_tick_monotonic,
            }
