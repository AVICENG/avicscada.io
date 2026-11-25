from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import Callable

class RuntimeState(str, Enum):
    STOPPED = "STOPPED"
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    DEGRADED = "DEGRADED"
    STOPPING = "STOPPING"
    RECOVERING = "RECOVERING"
    ERROR = "ERROR"

class InvalidTransition(RuntimeError): pass

_ALLOWED = {
    RuntimeState.STOPPED: {RuntimeState.STARTING},
    RuntimeState.STARTING: {RuntimeState.RUNNING, RuntimeState.DEGRADED, RuntimeState.ERROR, RuntimeState.STOPPING},
    RuntimeState.RUNNING: {RuntimeState.DEGRADED, RuntimeState.STOPPING, RuntimeState.ERROR},
    RuntimeState.DEGRADED: {RuntimeState.RUNNING, RuntimeState.RECOVERING, RuntimeState.STOPPING, RuntimeState.ERROR},
    RuntimeState.RECOVERING: {RuntimeState.RUNNING, RuntimeState.DEGRADED, RuntimeState.ERROR, RuntimeState.STOPPING},
    RuntimeState.STOPPING: {RuntimeState.STOPPED, RuntimeState.ERROR},
    RuntimeState.ERROR: {RuntimeState.RECOVERING, RuntimeState.STOPPING, RuntimeState.STOPPED},
}

@dataclass
class RuntimeStatus:
    station_id: str
    state: RuntimeState = RuntimeState.STOPPED
    generation: int = 0
    last_error: str | None = None
    lock: RLock = field(default_factory=RLock, repr=False)

    def transition(self, target: RuntimeState, *, error: str | None = None):
        with self.lock:
            if target == self.state: return self.state  # Idempotent command.
            if target not in _ALLOWED[self.state]:
                raise InvalidTransition(f"{self.station_id}: {self.state.value} -> {target.value} is not allowed")
            self.state = target
            self.last_error = error if target == RuntimeState.ERROR else None
            self.generation += 1
            return self.state

class RuntimeManager:
    """Owns independent lifecycle state for each station; no global active station."""
    def __init__(self):
        self._items: dict[str, RuntimeStatus] = {}
        self._lock = RLock()

    def register(self, station_id: str) -> RuntimeStatus:
        with self._lock:
            return self._items.setdefault(station_id, RuntimeStatus(station_id))

    def get(self, station_id: str) -> RuntimeStatus:
        with self._lock:
            if station_id not in self._items: raise KeyError(station_id)
            return self._items[station_id]

    def all(self) -> tuple[RuntimeStatus, ...]:
        with self._lock: return tuple(self._items.values())

    def start(self, station_id: str, start_hook: Callable[[], None] | None = None) -> RuntimeStatus:
        status = self.register(station_id)
        with status.lock:
            if status.state in (RuntimeState.RUNNING, RuntimeState.STARTING): return status
            status.transition(RuntimeState.STARTING)
            try:
                if start_hook: start_hook()
                status.transition(RuntimeState.RUNNING)
            except Exception as exc:
                status.transition(RuntimeState.ERROR, error=str(exc))
                raise
        return status

    def stop(self, station_id: str, stop_hook: Callable[[], None] | None = None) -> RuntimeStatus:
        status = self.register(station_id)
        with status.lock:
            if status.state == RuntimeState.STOPPED: return status
            if status.state == RuntimeState.ERROR:
                status.transition(RuntimeState.STOPPING)
            elif status.state != RuntimeState.STOPPING:
                status.transition(RuntimeState.STOPPING)
            try:
                if stop_hook: stop_hook()
                status.transition(RuntimeState.STOPPED)
            except Exception as exc:
                status.transition(RuntimeState.ERROR, error=str(exc))
                raise
        return status
