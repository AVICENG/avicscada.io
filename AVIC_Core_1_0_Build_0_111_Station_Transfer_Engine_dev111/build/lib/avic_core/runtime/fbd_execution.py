from __future__ import annotations

from dataclasses import dataclass, field
from threading import Event, RLock, Thread
from time import monotonic
from typing import Any
from uuid import uuid4

from avic_core.logic_fbd import FBDService


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
    thread: Thread | None = field(default=None, repr=False)
    lock: RLock = field(default_factory=RLock, repr=False)


class FBDExecutionService:
    """Cyclic, station-isolated FBD evaluation. Never writes field outputs.

    `tick_once` is deterministic for tests and diagnostics. `start` can run a
    daemon scheduler; each strategy owns its own worker and stop signal.
    """

    MIN_INTERVAL_MS = 100
    MAX_INTERVAL_MS = 60_000
    MAX_EVENTS = 500

    def __init__(self, core):
        self.core = core
        self.fbd = FBDService(core)
        self._items: dict[str, StrategyExecution] = {}
        self._lock = RLock()

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
                    "field_writes_performed": False}

    def start(self, document_id: str, *, interval_ms: int | None = None,
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
            if item.thread and item.thread.is_alive():
                raise RuntimeError("Предыдущий worker ещё завершает остановку")
            item.stop_event = Event()
            item.state = "RUNNING"
            item.generation += 1
            item.last_error = None
            # A new execution generation starts from each block's configured initial state.
            item.runtime_state.clear()
            item.last_started_at = monotonic()
            item.events.append({"event": "STARTED", "generation": item.generation,
                                "at_monotonic": item.last_started_at})
            item.events[:] = item.events[-self.MAX_EVENTS:]
            if background:
                item.thread = Thread(target=self._worker, args=(item,),
                                     name=f"avic-fbd-{document_id[:8]}", daemon=True)
                item.thread.start()
        return self.status(document_id)

    def _worker(self, item: StrategyExecution) -> None:
        deadline = monotonic()
        while not item.stop_event.is_set():
            deadline += item.interval_ms / 1000.0
            try:
                self.tick_once(item.document_id)
            except Exception:
                # tick_once records the error and changes state to ERROR.
                return
            wait_for = max(0.0, deadline - monotonic())
            if item.stop_event.wait(wait_for):
                return

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
                result = self.fbd.simulate(document_id, inputs=inputs, runtime_state=item.runtime_state)
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
        with item.lock:
            if item.state == "STOPPED":
                return self.status(document_id)
            item.stop_event.set()
            worker = item.thread
            if item.state != "ERROR":
                item.state = "STOPPING"
            item.generation += 1
        if worker and worker is not __import__("threading").current_thread():
            worker.join(timeout=max(0.0, timeout))
        with item.lock:
            if worker and worker.is_alive():
                item.last_error = "Worker не завершился за отведённое время"
                item.state = "ERROR"
            elif item.state != "ERROR":
                item.state = "STOPPED"
                item.events.append({"event": "STOPPED", "generation": item.generation,
                                    "at_monotonic": monotonic()})
                item.events[:] = item.events[-self.MAX_EVENTS:]
        if self.status(document_id)["state"] == "STOPPED":
            for row in self.core.repository.list_records(entity_type="FBDExposedPoint"):
                if row.get("payload", {}).get("fbd_document_id") == document_id:
                    try: self.core.point_runtime.mark_fbd_quality(row["entity_id"], "STALE")
                    except Exception: pass
        return self.status(document_id)

    def events(self, document_id: str) -> tuple[dict[str, Any], ...]:
        with self._lock:
            item = self._items.get(document_id)
        if not item:
            return ()
        with item.lock:
            return tuple(dict(event) for event in item.events)

    def close(self) -> None:
        with self._lock:
            ids = tuple(self._items)
        for document_id in ids:
            self.stop(document_id)
