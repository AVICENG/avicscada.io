"""Protocol-independent, timestamp-driven debounce for binary AVIC points.

The engine is deliberately transport-agnostic: BACnet, Modbus, MQTT and future
adapters feed samples into the same per-point state machine. A caller must invoke
flush_due() from its runtime scheduler; no hidden timer thread is created here.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock


@dataclass(frozen=True, slots=True)
class DebounceConfig:
    on_ms: int = 0
    off_ms: int = 0

    def __post_init__(self) -> None:
        for name, value in (("on_ms", self.on_ms), ("off_ms", self.off_ms)):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class DebounceResult:
    point_id: str
    value: bool
    accepted: bool
    pending: bool
    deadline: datetime | None
    reason: str


@dataclass(slots=True)
class _Pending:
    value: bool
    since: datetime
    deadline: datetime


class DebounceEngine:
    """Per-point ON/OFF debounce state machine with deterministic clock injection.

    First sample initializes state immediately (no artificial startup delay).
    A transition is committed only after its configured direction-specific
    interval. A bounce back to the stable value cancels the pending transition.
    """

    def __init__(self) -> None:
        self._lock = RLock()
        self._configs: dict[str, DebounceConfig] = {}
        self._stable: dict[str, bool] = {}
        self._pending: dict[str, _Pending] = {}
        self._last_timestamp: dict[str, datetime] = {}

    @staticmethod
    def _timestamp(value: datetime | None) -> datetime:
        result = value or datetime.now(timezone.utc)
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("Debounce timestamp must be timezone-aware")
        return result

    def configure(self, point_id: str, config: DebounceConfig) -> None:
        if not point_id:
            raise ValueError("point_id is required")
        if not isinstance(config, DebounceConfig):
            raise TypeError("config must be DebounceConfig")
        with self._lock:
            self._configs[point_id] = config
            self._pending.pop(point_id, None)

    def ingest(self, point_id: str, value: bool, *, timestamp: datetime | None = None) -> DebounceResult:
        if not point_id:
            raise ValueError("point_id is required")
        if not isinstance(value, bool):
            raise TypeError("Debounce accepts bool samples only")
        now = self._timestamp(timestamp)
        with self._lock:
            previous_time = self._last_timestamp.get(point_id)
            if previous_time is not None and now < previous_time:
                raise ValueError("Out-of-order debounce sample rejected")
            self._last_timestamp[point_id] = now

            if point_id not in self._stable:
                self._stable[point_id] = value
                return DebounceResult(point_id, value, True, False, None, "initialized")

            stable = self._stable[point_id]
            if value == stable:
                self._pending.pop(point_id, None)
                return DebounceResult(point_id, stable, False, False, None, "stable_or_bounce_cancelled")

            pending = self._pending.get(point_id)
            if pending is None or pending.value != value:
                cfg = self._configs.get(point_id, DebounceConfig())
                delay = cfg.on_ms if value else cfg.off_ms
                deadline = now + timedelta(milliseconds=delay)
                self._pending[point_id] = _Pending(value, now, deadline)
                if delay == 0:
                    self._stable[point_id] = value
                    self._pending.pop(point_id, None)
                    return DebounceResult(point_id, value, True, False, None, "zero_delay")
                return DebounceResult(point_id, stable, False, True, deadline, "transition_pending")

            if now >= pending.deadline:
                self._stable[point_id] = pending.value
                self._pending.pop(point_id, None)
                return DebounceResult(point_id, value, True, False, None, "debounce_elapsed")
            return DebounceResult(point_id, stable, False, True, pending.deadline, "transition_pending")

    def flush_due(self, *, now: datetime | None = None) -> tuple[DebounceResult, ...]:
        """Commit transitions whose debounce deadline elapsed, even without a new sample."""
        current = self._timestamp(now)
        committed: list[DebounceResult] = []
        with self._lock:
            for point_id, pending in tuple(self._pending.items()):
                if current >= pending.deadline:
                    self._stable[point_id] = pending.value
                    self._pending.pop(point_id, None)
                    committed.append(DebounceResult(
                        point_id, pending.value, True, False, None, "debounce_elapsed"
                    ))
        return tuple(committed)

    def cancel_pending(self, point_id: str) -> bool:
        """Cancel pending transition, e.g. when the source quality becomes non-GOOD."""
        with self._lock:
            return self._pending.pop(point_id, None) is not None

    def stable_value(self, point_id: str) -> bool | None:
        with self._lock:
            return self._stable.get(point_id)

    def remove(self, point_id: str) -> None:
        with self._lock:
            self._configs.pop(point_id, None)
            self._stable.pop(point_id, None)
            self._pending.pop(point_id, None)
            self._last_timestamp.pop(point_id, None)
