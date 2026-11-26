from __future__ import annotations

from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from threading import Event, RLock, Thread
from time import monotonic
from typing import Any
from uuid import uuid4

from avic_core.logic_fbd import FBDService


class _FBDStopRequested(RuntimeError):
    """Internal cancellation raised before a cycle publishes its outputs."""


@dataclass
class StrategyExecution:
    document_id: str
    station_id: str
    interval_ms: int
    state: str = "STOPPED"
    generation: int = 0
    tick_count: int = 0
    last_started_at: float | None = None
    last_tick_at: float | None = None
    last_duration_ms: float | None = None
    last_error: str | None = None
    last_result: dict[str, Any] | None = None
    runtime_state: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    stop_event: Event = field(default_factory=Event, repr=False)
    background: bool = False
    in_flight: bool = False
    next_due: float = 0.0
    future: Future | None = field(default=None, repr=False)
    lock: RLock = field(default_factory=RLock, repr=False)


class FBDExecutionService:
    """Cyclic, station-isolated FBD evaluation. Never writes field outputs.

    `tick_once` is deterministic for tests and diagnostics. Background strategies
    share one scheduler thread and a bounded worker pool; missed cycles are skipped.
    """

    MIN_INTERVAL_MS = 100
    MAX_INTERVAL_MS = 60_000
    MAX_EVENTS = 500

    def __init__(self, core, *, max_workers: int = 4, scheduler_resolution_ms: int = 20):
        if isinstance(max_workers, bool) or not isinstance(max_workers, int) or not 1 <= max_workers <= 64:
            raise ValueError("max_workers должен быть целым числом от 1 до 64")
        if isinstance(scheduler_resolution_ms, bool) or not isinstance(scheduler_resolution_ms, int) or not 5 <= scheduler_resolution_ms <= 1000:
            raise ValueError("scheduler_resolution_ms должен быть от 5 до 1000 мс")
        self.core = core
        self.fbd = FBDService(core)
        self._items: dict[str, StrategyExecution] = {}
        self._lock = RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="avic-fbd-eval")
        self._scheduler_resolution = scheduler_resolution_ms / 1000.0
        self._scheduler_wake = Event()
        self._scheduler_stop = Event()
        self._scheduler_thread: Thread | None = None
        self._closed = False

    def _document(self, document_id: str) -> dict[str, Any]:
        graph = self.fbd.get(document_id)
        if not graph.get("station_id"):
            raise ValueError("FBD-стратегия не привязана к станции")
        return graph

    def configure(self, document_id: str, *, interval_ms: int = 1000) -> dict[str, Any]:
        if isinstance(interval_ms, bool) or not isinstance(interval_ms, int):
            raise ValueError("Интервал должен быть целым числом миллисекунд")
        if not self.MIN_INTERVAL_MS <= interval_ms <= self.MAX_INTERVAL_MS:
            raise ValueError(f"Интервал должен быть от {self.MIN_INTERVAL_MS} до {self.MAX_INTERVAL_MS} мс")
        graph = self._document(document_id)
        with self._lock:
            current = self._items.get(document_id)
            if current and current.state == "RUNNING":
                raise RuntimeError("Нельзя менять интервал работающей стратегии; сначала остановите её")
            item = current or StrategyExecution(document_id, graph["station_id"], interval_ms)
            item.station_id = graph["station_id"]
            item.interval_ms = interval_ms
            self._items[document_id] = item
            return self.status(document_id)

    def status(self, document_id: str) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(document_id)
        if not item:
            return {"document_id": document_id, "state": "STOPPED", "configured": False,
                    "tick_count": 0, "runtime_published": False, "field_writes_performed": False}
        with item.lock:
            return {"document_id": item.document_id, "station_id": item.station_id,
                    "state": item.state, "configured": True, "interval_ms": item.interval_ms,
                    "generation": item.generation, "tick_count": item.tick_count,
                    "last_started_at_monotonic": item.last_started_at,
                    "last_tick_at_monotonic": item.last_tick_at,
                    "last_duration_ms": item.last_duration_ms, "last_error": item.last_error,
                    "last_result": item.last_result, "runtime_published": bool((item.last_result or {}).get("runtime_published")),
                    "in_flight": item.in_flight, "field_writes_performed": False}

    def start(self, document_id: str, *, interval_ms: int | None = None,
              background: bool = True) -> dict[str, Any]:
        # Serialize starts against Core shutdown so a just-created scheduler cannot
        # escape the shutdown snapshot.
        core_lock = getattr(self.core, "_lock", None)
        if core_lock is None:
            return self._start_unlocked(document_id, interval_ms=interval_ms, background=background)
        with core_lock:
            ensure_open = getattr(self.core, "_ensure_open", None)
            if callable(ensure_open):
                ensure_open()
            return self._start_unlocked(document_id, interval_ms=interval_ms, background=background)

    def _start_unlocked(self, document_id: str, *, interval_ms: int | None = None,
                        background: bool = True) -> dict[str, Any]:
        if interval_ms is not None:
            self.configure(document_id, interval_ms=interval_ms)
        elif document_id not in self._items:
            self.configure(document_id)
        item = self._items[document_id]
        graph = self._document(document_id)
        if graph["station_id"] != item.station_id:
            raise ValueError("Станция FBD-стратегии изменилась после конфигурации")
        with item.lock:
            if item.state == "RUNNING":
                return self.status(document_id)
            if item.in_flight:
                raise RuntimeError("Предыдущий цикл ещё завершает остановку")
            if self._closed:
                raise RuntimeError("FBDExecutionService уже закрыт")
            item.stop_event = Event()
            item.state = "RUNNING"
            item.background = bool(background)
            item.generation += 1
            item.last_error = None
            item.future = None
            item.in_flight = False
            item.next_due = monotonic()
            # A new execution generation starts from each block's configured initial state.
            item.runtime_state.clear()
            item.last_started_at = monotonic()
            item.events.append({"event": "STARTED", "generation": item.generation,
                                "at_monotonic": item.last_started_at,
                                "background": item.background})
            item.events[:] = item.events[-self.MAX_EVENTS:]
        if background:
            self._ensure_scheduler()
        return self.status(document_id)

    def _ensure_scheduler(self) -> None:
        with self._lock:
            if self._closed:
                raise RuntimeError("FBDExecutionService уже закрыт")
            if self._scheduler_thread and self._scheduler_thread.is_alive():
                self._scheduler_wake.set()
                return
            self._scheduler_stop.clear()
            self._scheduler_thread = Thread(
                target=self._scheduler_loop, name="avic-fbd-scheduler", daemon=True
            )
            self._scheduler_thread.start()

    def _scheduler_loop(self) -> None:
        while not self._scheduler_stop.is_set():
            now = monotonic()
            with self._lock:
                items = tuple(self._items.values())
            for item in items:
                with item.lock:
                    if (item.state != "RUNNING" or not item.background
                            or item.stop_event.is_set() or item.in_flight
                            or now < item.next_due):
                        continue
                    item.in_flight = True
                    # Skip missed periods: never enqueue a backlog of stale cycles.
                    item.next_due = now + item.interval_ms / 1000.0
                    try:
                        item.future = self._executor.submit(self._scheduled_tick, item)
                    except RuntimeError as exc:
                        item.in_flight = False
                        item.state = "ERROR"
                        item.last_error = f"Scheduler submission failed: {exc}"
                        item.stop_event.set()
            self._scheduler_wake.wait(self._scheduler_resolution)
            self._scheduler_wake.clear()

    def _scheduled_tick(self, item: StrategyExecution) -> None:
        try:
            if not item.stop_event.is_set():
                self.tick_once(item.document_id)
        except Exception:
            # tick_once records the fault and transitions only this strategy to ERROR.
            pass
        finally:
            with item.lock:
                item.in_flight = False
                item.future = None

    def tick_once(self, document_id: str, *, inputs: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(document_id)
        if not item:
            raise KeyError(document_id)
        with item.lock:
            if item.state != "RUNNING":
                raise RuntimeError("Цикл можно выполнить только для RUNNING-стратегии")
            started = monotonic()
            try:
                graph = self._document(document_id)
                if graph["station_id"] != item.station_id:
                    raise ValueError("Нарушена изоляция станции: стратегия сменила станцию")
                result = self.fbd.simulate(document_id, inputs=inputs, runtime_state=item.runtime_state,
                                           dt_seconds=item.interval_ms / 1000.0)
                # A stop request may arrive while simulate() is running. Never publish
                # outputs from a cycle that was cancelled before its publication phase.
                if item.stop_event.is_set():
                    raise _FBDStopRequested("FBD-цикл отменён запросом остановки до публикации")
                if result.get("field_writes_performed"):
                    raise RuntimeError("Нарушен запрет записи в оборудование")
                # Publish exposed outputs to Core virtual points. These are read-only
                # software points; this path never calls a field driver or Command Manager.
                graph_nodes = {str(n.get("params", {}).get("_studio_module_id")): n
                               for n in graph.get("nodes", []) if n.get("params", {}).get("_studio_module_id")}
                published = 0
                from avic_core.points.runtime import FBDExposedPoint
                for row in self.core.repository.list_records(entity_type="FBDExposedPoint"):
                    if row.get("payload", {}).get("fbd_document_id") != document_id:
                        continue
                    point, _ = self.core.repository.get(row["entity_id"], FBDExposedPoint)
                    node = graph_nodes.get(point.source_module_id)
                    if node is None:
                        self.core.point_runtime.publish_fbd(point.id, False if point.data_type == "bool" else 0.0, quality="BAD_CONFIGURATION")
                        continue
                    key = f"{node['id']}:{point.source_port}"
                    if key not in result.get("node_values", {}):
                        self.core.point_runtime.publish_fbd(point.id, False if point.data_type == "bool" else 0.0, quality="BAD_CONFIGURATION")
                        continue
                    self.core.point_runtime.publish_fbd(point.id, result["node_values"][key], quality="GOOD")
                    published += 1
                result["published_fbd_points"] = published
                result["runtime_published"] = published > 0
                result["field_writes_performed"] = False
                finished = monotonic()
                item.tick_count += 1
                item.last_tick_at = finished
                item.last_duration_ms = (finished - started) * 1000.0
                item.last_result = result
                item.last_error = None
                item.events.append({"event": "TICK_OK", "tick": item.tick_count,
                                    "duration_ms": item.last_duration_ms,
                                    "at_monotonic": finished})
                item.events[:] = item.events[-self.MAX_EVENTS:]
                return {"tick": item.tick_count, "duration_ms": item.last_duration_ms,
                        "result": result, "runtime_published": bool(result.get("runtime_published")),
                        "field_writes_performed": False}
            except Exception as exc:
                if isinstance(exc, _FBDStopRequested):
                    # Cancellation is not a graph/configuration fault. Let stop()
                    # decide STOPPED vs ERROR from its own deadline and worker state.
                    item.events.append({"event": "TICK_CANCELLED", "tick": item.tick_count,
                                        "at_monotonic": monotonic()})
                else:
                    from avic_core.points.runtime import FBDExposedPoint
                    for row in self.core.repository.list_records(entity_type="FBDExposedPoint"):
                        if row.get("payload", {}).get("fbd_document_id") == document_id:
                            try: self.core.point_runtime.mark_fbd_quality(row["entity_id"], "BAD_CONFIGURATION")
                            except Exception: pass
                    item.state = "ERROR"
                    item.last_error = f"{type(exc).__name__}: {exc}"
                    item.stop_event.set()
                    item.events.append({"event": "TICK_ERROR", "tick": item.tick_count,
                                        "error": item.last_error, "at_monotonic": monotonic()})
                item.events[:] = item.events[-self.MAX_EVENTS:]
                raise

    def stop(self, document_id: str, *, timeout: float = 2.0) -> dict[str, Any]:
        with self._lock:
            item = self._items.get(document_id)
        if not item:
            return self.status(document_id)

        # Signal cancellation BEFORE acquiring item.lock. tick_once currently holds
        # this lock while evaluating the graph, so waiting for it first would make
        # the caller's timeout ineffective.
        item.stop_event.set()
        wait_seconds = max(0.0, float(timeout))
        deadline = monotonic() + wait_seconds
        acquired = item.lock.acquire(timeout=wait_seconds)
        if not acquired:
            item.state = "ERROR"
            item.last_error = "FBD-цикл не завершился за отведённое время; остановка не подтверждена"
            return {
                "document_id": item.document_id,
                "station_id": item.station_id,
                "state": "ERROR",
                "configured": True,
                "interval_ms": item.interval_ms,
                "generation": item.generation,
                "tick_count": item.tick_count,
                "last_error": item.last_error,
                "runtime_published": bool((item.last_result or {}).get("runtime_published")),
                "in_flight": True,
                "field_writes_performed": False,
            }

        try:
            future = item.future
            if item.state != "ERROR":
                item.state = "STOPPING"
            item.generation += 1
        finally:
            item.lock.release()

        if future is not None:
            try:
                future.result(timeout=max(0.0, deadline - monotonic()))
            except FutureTimeout:
                with item.lock:
                    item.last_error = "FBD-цикл не завершился за отведённое время"
                    item.state = "ERROR"
            except Exception:
                # Evaluation errors are already recorded by tick_once.
                pass
        with item.lock:
            if item.in_flight:
                item.last_error = "FBD worker не завершился за отведённое время"
                item.state = "ERROR"
            elif item.state not in ("ERROR",):
                item.state = "STOPPED"
                item.events.append({"event": "STOPPED", "generation": item.generation,
                                    "at_monotonic": monotonic()})
                item.events[:] = item.events[-self.MAX_EVENTS:]
        if self.status(document_id)["state"] == "STOPPED":
            for row in self.core.repository.list_records(entity_type="FBDExposedPoint"):
                if row.get("payload", {}).get("fbd_document_id") == document_id:
                    try:
                        self.core.point_runtime.mark_fbd_quality(row["entity_id"], "STALE")
                    except Exception:
                        pass
        return self.status(document_id)

    def all_status(self) -> list[dict[str, Any]]:
        with self._lock:
            ids = tuple(self._items)
        return [self.status(document_id) for document_id in ids]

    def events(self, document_id: str) -> tuple[dict[str, Any], ...]:
        with self._lock:
            item = self._items.get(document_id)
        if not item:
            return ()
        with item.lock:
            return tuple(dict(event) for event in item.events)

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            ids = tuple(self._items)
        failures = []
        for document_id in ids:
            try:
                status = self.stop(document_id, timeout=2.0)
                # ERROR with no in-flight worker is quiescent: retain the diagnostic,
                # but it is safe to stop the scheduler and its executor.
                if status.get("in_flight") or status.get("state") in {"RUNNING", "STARTING", "STOPPING"}:
                    failures.append(document_id)
            except Exception:
                failures.append(document_id)
        if failures:
            raise RuntimeError("Не удалось подтвердить остановку FBD worker: " + ", ".join(failures))

        self._scheduler_stop.set()
        self._scheduler_wake.set()
        scheduler = self._scheduler_thread
        if scheduler and scheduler.is_alive():
            scheduler.join(timeout=2.0)
        if scheduler and scheduler.is_alive():
            raise RuntimeError("FBD scheduler не завершился за отведённое время")
        self._executor.shutdown(wait=True, cancel_futures=True)
        with self._lock:
            self._closed = True
