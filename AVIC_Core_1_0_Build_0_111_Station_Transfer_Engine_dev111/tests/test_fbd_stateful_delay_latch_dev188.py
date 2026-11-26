from uuid import uuid4

from fastapi.testclient import TestClient

from avic_core.logic_fbd import FBDService
from avic_core.ui import create_ui_app
from test_graphics_workbench_dev35 import setup


def _uid():
    return str(uuid4())


def test_delay_and_latch_state_is_committed_only_after_successful_pass(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Stateful blocks")
    page_id = doc["pages"][0]["id"]

    start_id, time_id, delay_id, delay_out_id = (_uid() for _ in range(4))
    nodes = [
        {"id": start_id, "type": "BOOL_INPUT", "name": "Start", "params": {"value": True}, "page_id": page_id},
        {"id": time_id, "type": "FLOAT_INPUT", "name": "On delay", "params": {"value": 0.5}, "page_id": page_id},
        {"id": delay_id, "type": "DELAY", "name": "On delay block",
         "params": {"on_delay": 0.5, "off_delay": 0.25, "initial_state": False}, "page_id": page_id},
        {"id": delay_out_id, "type": "BOOL_OUTPUT", "name": "Delayed", "params": {}, "page_id": page_id},
    ]
    links = [
        {"source_node_id": start_id, "source_port": "OUT", "target_node_id": delay_id, "target_port": "IN"},
        {"source_node_id": time_id, "source_port": "OUT", "target_node_id": delay_id, "target_port": "TIME"},
        {"source_node_id": delay_id, "source_port": "OUT", "target_node_id": delay_out_id, "target_port": "IN"},
    ]
    saved = fbd.save(doc["id"], doc["revision"], nodes, links)
    state = {}
    first = fbd.simulate(doc["id"], runtime_state=state, dt_seconds=0.25)
    assert first["outputs"]["Delayed"] is False
    assert state[delay_id]["on"] == 0.25
    second = fbd.simulate(doc["id"], runtime_state=state, dt_seconds=0.25)
    assert second["outputs"]["Delayed"] is True
    third = fbd.simulate(doc["id"], inputs={start_id: False}, runtime_state=state, dt_seconds=0.25)
    assert third["outputs"]["Delayed"] is False

    core.close()


def test_latch_has_configurable_reset_priority_and_retains_state(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Latch state")
    page_id = doc["pages"][0]["id"]
    set_id, reset_id, latch_id, out_id = (_uid() for _ in range(4))
    nodes = [
        {"id": set_id, "type": "BOOL_INPUT", "name": "Set", "params": {"value": False}, "page_id": page_id},
        {"id": reset_id, "type": "BOOL_INPUT", "name": "Reset", "params": {"value": False}, "page_id": page_id},
        {"id": latch_id, "type": "LATCH", "name": "RS latch",
         "params": {"initial_state": False, "reset_priority": True}, "page_id": page_id},
        {"id": out_id, "type": "BOOL_OUTPUT", "name": "Latched", "params": {}, "page_id": page_id},
    ]
    links = [
        {"source_node_id": set_id, "source_port": "OUT", "target_node_id": latch_id, "target_port": "SET"},
        {"source_node_id": reset_id, "source_port": "OUT", "target_node_id": latch_id, "target_port": "RESET"},
        {"source_node_id": latch_id, "source_port": "OUT", "target_node_id": out_id, "target_port": "IN"},
    ]
    fbd.save(doc["id"], doc["revision"], nodes, links)
    state = {}
    assert fbd.simulate(doc["id"], inputs={set_id: True}, runtime_state=state)["outputs"]["Latched"] is True
    assert fbd.simulate(doc["id"], inputs={set_id: False, reset_id: False}, runtime_state=state)["outputs"]["Latched"] is True
    assert fbd.simulate(doc["id"], inputs={set_id: True, reset_id: True}, runtime_state=state)["outputs"]["Latched"] is False
    core.close()


def test_studio_compiles_delay_and_latch_to_core_runtime(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV188 Project")
    station = client.app.state.project_station.create_station(project["id"], "DEV188 Station")
    modules = [
        {"id": "start", "type": "BOOL_INPUT", "name": "Start", "params": {"value": True},
         "ins": [], "outs": [{"id": "start-out", "name": "OUT", "type": "bool"}]},
        {"id": "time", "type": "FLOAT_INPUT", "name": "Delay time", "params": {"value": 0.5},
         "ins": [], "outs": [{"id": "time-out", "name": "OUT", "type": "num"}]},
        {"id": "delay", "type": "DELAY", "name": "Delay", "params": {"delay": {"onDelay": 0.5, "offDelay": 0.25}},
         "ins": [{"id": "delay-in", "name": "IN", "type": "bool"}, {"id": "delay-time", "name": "TIME", "type": "num"}],
         "outs": [{"id": "delay-out", "name": "OUT", "type": "bool"}]},
        {"id": "delayed", "type": "BOOL_OUTPUT", "name": "Delayed", "params": {},
         "ins": [{"id": "delayed-in", "name": "IN", "type": "bool"}], "outs": []},
        {"id": "set", "type": "BOOL_INPUT", "name": "Set", "params": {"value": True},
         "ins": [], "outs": [{"id": "set-out", "name": "OUT", "type": "bool"}]},
        {"id": "reset", "type": "BOOL_INPUT", "name": "Reset", "params": {"value": False},
         "ins": [], "outs": [{"id": "reset-out", "name": "OUT", "type": "bool"}]},
        {"id": "latch", "type": "LATCH", "name": "Latch", "params": {"latch": {"resetPriority": True, "initial": 0}},
         "ins": [{"id": "latch-set", "name": "SET", "type": "bool"}, {"id": "latch-reset", "name": "RESET", "type": "bool"}],
         "outs": [{"id": "latch-out", "name": "OUT", "type": "bool"}]},
        {"id": "latched", "type": "BOOL_OUTPUT", "name": "Latched", "params": {},
         "ins": [{"id": "latched-in", "name": "IN", "type": "bool"}], "outs": []},
    ]
    links = [
        ("start", "delay", 0), ("time", "delay", 1), ("delay", "delayed", 0),
        ("set", "latch", 0), ("reset", "latch", 1), ("latch", "latched", 0),
    ]
    data = {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Stateful parity",
        "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": modules}],
        "links": [
            {"id": f"l{i}", "pageId": "page-main", "from": f"out:{src}:0", "to": f"in:{dst}:{index}",
             "signalType": "num" if src == "time" else "bool"}
            for i, (src, dst, index) in enumerate(links)
        ],
        "references": [], "fbdPoints": [],
    }
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Stateful parity", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    core_doc = compiled.json()["core_document"]
    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["Delayed"] is True
    assert simulation.json()["outputs"]["Latched"] is True
