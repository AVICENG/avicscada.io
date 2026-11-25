import time
import threading
import pytest

from avic_core.logic_fbd import FBDService
from avic_core.runtime.fbd_execution import FBDExecutionService
from test_graphics_workbench_dev35 import setup


def _wait_until(predicate, timeout=3.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return bool(predicate())


def test_many_strategies_share_one_scheduler_and_bounded_workers(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    runtime = FBDExecutionService(core, max_workers=2)
    documents = [fbd.create_fan_demo(station["id"]) for _ in range(12)]
    for doc in documents:
        runtime.start(doc["id"], interval_ms=100, background=True)

    assert _wait_until(lambda: all(runtime.status(d["id"])["tick_count"] >= 1 for d in documents))
    names = [thread.name for thread in threading.enumerate()]
    assert names.count("avic-fbd-scheduler") == 1
    assert sum(name.startswith("avic-fbd-eval") for name in names) <= 2
    assert not any(name.startswith("avic-fbd-") and name not in {"avic-fbd-scheduler"}
                   and not name.startswith("avic-fbd-eval") for name in names)

    for doc in documents:
        assert runtime.stop(doc["id"])["state"] == "STOPPED"
    runtime.close()
    core.close()


def test_slow_strategy_skips_missed_cycles_without_overlap_or_backlog(tmp_path):
    core, station, _ = setup(tmp_path)
    doc = FBDService(core).create_fan_demo(station["id"])
    runtime = FBDExecutionService(core, max_workers=1)
    original = runtime.fbd.simulate
    active = 0
    maximum_active = 0
    guard = threading.Lock()

    def slow(document_id, **kwargs):
        nonlocal active, maximum_active
        with guard:
            active += 1
            maximum_active = max(maximum_active, active)
        try:
            time.sleep(0.22)
            return original(document_id, **kwargs)
        finally:
            with guard:
                active -= 1

    runtime.fbd.simulate = slow
    runtime.start(doc["id"], interval_ms=100, background=True)
    assert _wait_until(lambda: runtime.status(doc["id"])["tick_count"] >= 2, timeout=2.0)
    time.sleep(0.25)
    status = runtime.stop(doc["id"], timeout=2.0)
    assert status["state"] == "STOPPED"
    assert maximum_active == 1
    assert status["tick_count"] <= 4
    runtime.close()
    core.close()


def test_one_strategy_fault_does_not_stop_other_strategy(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    bad = fbd.create_fan_demo(station["id"])
    good = fbd.create_fan_demo(station["id"])
    runtime = FBDExecutionService(core, max_workers=2)
    original = runtime.fbd.simulate

    def selective(document_id, **kwargs):
        if document_id == bad["id"]:
            raise ValueError("isolated strategy fault")
        return original(document_id, **kwargs)

    runtime.fbd.simulate = selective
    runtime.start(bad["id"], interval_ms=100, background=True)
    runtime.start(good["id"], interval_ms=100, background=True)
    assert _wait_until(lambda: runtime.status(bad["id"])["state"] == "ERROR")
    assert _wait_until(lambda: runtime.status(good["id"])["tick_count"] >= 2)
    assert runtime.status(good["id"])["state"] == "RUNNING"
    runtime.close()
    core.close()


def test_fbd_topological_evaluation_handles_maximum_chain(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Длинная цепь", "Проверка линейной топологической сортировки")
    nodes = []
    first_id = __import__("uuid").uuid4().__str__()
    nodes.append({"id": first_id, "type": "FLOAT_INPUT", "name": "Источник",
                  "x": 20, "y": 20, "params": {"value": 5.0}})
    previous = first_id
    links = []
    for index in range(998):
        node_id = __import__("uuid").uuid4().__str__()
        nodes.append({"id": node_id, "type": "ADD", "name": f"Сумматор {index}",
                      "x": 100 + (index % 800), "y": 40 + (index % 900), "params": {}})
        links.append({"source_node_id": previous, "source_port": "OUT",
                      "target_node_id": node_id, "target_port": "A"})
        previous = node_id
    output_id = __import__("uuid").uuid4().__str__()
    nodes.append({"id": output_id, "type": "FLOAT_OUTPUT", "name": "Результат",
                  "x": 900, "y": 900, "params": {}})
    links.append({"source_node_id": previous, "source_port": "OUT",
                  "target_node_id": output_id, "target_port": "IN"})
    saved = fbd.save(doc["id"], doc["revision"], nodes, links)
    result = fbd.simulate(doc["id"])
    assert result["outputs"]["Результат"] == 5.0
    assert len(result["node_diagnostics"]) == 1000
    core.close()
