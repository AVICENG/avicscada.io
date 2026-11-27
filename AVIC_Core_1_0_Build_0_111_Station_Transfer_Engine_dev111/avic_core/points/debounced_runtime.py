from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock

from avic_core.domain.models import Point, PointDirection, PointQuality
from .debounce import DebounceConfig, DebounceEngine
from .runtime import PointRuntimeService, PointRuntimeValue


_BINARY_TYPES = {
    "bool", "boolean", "binary", "digital", "digital input", "digital output",
}


class DebouncedPointRuntimeService(PointRuntimeService):
    """Point Runtime with persisted, protocol-independent binary input debounce.

    Driver adapters still publish through the normal PointRuntime API. Debounce
    happens here, after ownership/type/timestamp validation and before the shared
    subscriber fan-out. No protocol adapter gets its own filtering implementation.

    The host runtime scheduler must call flush_debounce() regularly so a stable
    transition can commit even when no further sample arrives. This service does
    not create a hidden timer thread.
    """

    def __init__(self, repository):
        super().__init__(repository)
        self._debounce = DebounceEngine()
        # Stripe point locks so one slow subscriber cannot serialize unrelated points.
        self._point_locks = tuple(RLock() for _ in range(64))
        self._debounce_configs: dict[str, tuple[int, int]] = {}
        self._debounce_sources: dict[str, str | None] = {}

    def _point_lock(self, point_id: str) -> RLock:
        return self._point_locks[hash(str(point_id)) % len(self._point_locks)]

    @staticmethod
    def _is_binary(point: Point) -> bool:
        kind = str(point.data_type or "").strip().casefold()
        return kind in _BINARY_TYPES or kind.startswith(("binary-", "digital-"))

    def configure_debounce(self, point_id: str, *, on_ms: int = 0, off_ms: int = 0) -> PointRuntimeValue:
        """Persist ON/OFF debounce delays for a binary input point."""
        config = DebounceConfig(on_ms=on_ms, off_ms=off_ms)
        with self._point_lock(point_id):
            point, version = self.repository.get(str(point_id), Point)
            if not self._is_binary(point):
                raise ValueError("Дребезг можно настраивать только для бинарной точки")
            direction = getattr(point.direction, "value", str(point.direction)).lower()
            if direction == PointDirection.OUTPUT.value:
                raise ValueError("Дребезг нельзя настраивать для OUTPUT-точки")
            point.debounce_on_ms = config.on_ms
            point.debounce_off_ms = config.off_ms
            self.repository.save(point, expected_version=version)
            self._debounce.configure(point.id, config)
            self._debounce_configs[point.id] = (config.on_ms, config.off_ms)
            self._debounce_sources.pop(point.id, None)
        return self.read(point_id)

    def _ensure_debounce_config(self, point: Point) -> tuple[int, int]:
        checked = DebounceConfig(
            on_ms=getattr(point, "debounce_on_ms", 0),
            off_ms=getattr(point, "debounce_off_ms", 0),
        )
        config = (checked.on_ms, checked.off_ms)
        if self._debounce_configs.get(point.id) != config:
            self._debounce.configure(
                point.id, DebounceConfig(on_ms=config[0], off_ms=config[1])
            )
            self._debounce_configs[point.id] = config
            self._debounce_sources.pop(point.id, None)
        return config

    def publish(self, point_id: str, value, *, quality=PointQuality.GOOD,
                timestamp: datetime | None = None, source_driver_id: str | None = None) -> PointRuntimeValue:
        q = self._quality(quality)
        with self._debounce_lock:
            point, _, _ = self._read_entity(point_id)
            if not isinstance(point, Point) or not self._is_binary(point):
                return super().publish(
                    point_id, value, quality=q, timestamp=timestamp,
                    source_driver_id=source_driver_id,
                )

            on_ms, off_ms = self._ensure_debounce_config(point)
            if on_ms == 0 and off_ms == 0:
                return super().publish(
                    point_id, value, quality=q, timestamp=timestamp,
                    source_driver_id=source_driver_id,
                )

            if q != PointQuality.GOOD:
                marked = super().mark_quality(
                    point_id, q, source_driver_id=source_driver_id
                )
                self._debounce.cancel_pending(point.id)
                self._debounce_sources.pop(point.id, None)
                return marked

            if not isinstance(value, bool):
                # Let the authoritative Point Runtime raise its canonical type error.
                return super().publish(
                    point_id, value, quality=q, timestamp=timestamp,
                    source_driver_id=source_driver_id,
                )

            sample_time = timestamp or datetime.now(timezone.utc)
            if self._debounce.stable_value(point.id) is None and isinstance(point.value, bool):
                seed_time = point.timestamp or sample_time
                self._debounce.ingest(point.id, point.value, timestamp=seed_time)

            result = self._debounce.ingest(point.id, value, timestamp=sample_time)
            if result.pending:
                self._debounce_sources[point.id] = source_driver_id
                return super().read(point_id)

            self._debounce_sources.pop(point.id, None)
            if result.accepted or result.reason == "stable_or_bounce_cancelled":
                return super().publish(
                    point_id, value, quality=q, timestamp=sample_time,
                    source_driver_id=source_driver_id,
                )
            return super().read(point_id)

    def mark_quality(self, point_id: str, quality, *, source_driver_id: str | None = None) -> PointRuntimeValue:
        q = self._quality(quality)
        with self._debounce_lock:
            marked = super().mark_quality(
                point_id, q, source_driver_id=source_driver_id
            )
            self._debounce.cancel_pending(str(point_id))
            self._debounce_sources.pop(str(point_id), None)
            return marked

    def flush_debounce(self, *, now: datetime | None = None) -> tuple[PointRuntimeValue, ...]:
        """Commit elapsed binary transitions; call from the common runtime scheduler."""
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None or current.utcoffset() is None:
            raise ValueError("Debounce scheduler timestamp must be timezone-aware")
        published: list[PointRuntimeValue] = []
        due = self._debounce.flush_due(now=current)
        for item in due:
            with self._point_lock(item.point_id):
                source_driver_id = self._debounce_sources.pop(item.point_id, None)
                point, _, _ = self._read_entity(item.point_id)
                # A quality-loss transition may race the scheduler after its due
                # queue was drained. Never let that stale GOOD commit overwrite BAD.
                if self._quality(point.quality) != PointQuality.GOOD:
                    continue
                commit_time = current
                if point.timestamp is not None and commit_time < point.timestamp:
                    commit_time = point.timestamp
                published.append(super().publish(
                    item.point_id, item.value, quality=PointQuality.GOOD,
                    timestamp=commit_time, source_driver_id=source_driver_id,
                ))
        return tuple(published)


__all__ = ["DebouncedPointRuntimeService"]
