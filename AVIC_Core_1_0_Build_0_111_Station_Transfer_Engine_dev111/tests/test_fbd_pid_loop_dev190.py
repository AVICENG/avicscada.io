from uuid import uuid4

from fastapi.testclient import TestClient

from avic_core.logic_fbd import FBDService
from avic_core.ui import create_ui_app
from test_graphics_workbench_dev35 import setup


def _uid():
    return str(uuid4())


def _pid_config():
    return {
        "kp": 2.0, "ti": 0.0, "td": 0.0, "action": "reverse", "mode": "auto",
        "outputMin": 0.0, "outputMax": 100.0, "disabledOutput": 0.0, "manualOutput": 35.0,
        "bias": 0.0, "deadband": 0.0, "derivativeFilter": 0.0, "outputRateLimit": 0.0,
        "sampleTime": 1.0, "integralMin": -100.0, "integralMax": 100.0,
    }


def test_pid_loop_executes_auto_manual_bumpless_transfer_and_reset(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "PID strategy")
    page_id = doc["pages"][0]["id"]
    pv, sp, enable, manual, manual_out, reset, pid, output = (_uid() for _ in range(8))
    nodes = [
        {"id": pv, "type": "FLOAT_INPUT", "name": "PV", "params": {"value": 10.0}, "page_id": page_id},
        {"id": sp, "type": "FLOAT_INPUT", "name": "SP", "params": {"value": 20.0}, "page_id": page_id},
        {"id": enable, "type": "BOOL_INPUT", "name": "Enable", "params": {"value": True}, "page_id": page_id},
        {"id": manual, "type": "BOOL_INPUT", "name": "Manual", "params": {"value": False}, "page_id": page_id},
        {"id": manual_out, "type": "FLOAT_INPUT", "name": "Manual output", "params": {"value": 35.0}, "page_id": page_id},
        {"id": reset, "type": "BOOL_INPUT", "name": "Reset", "params": {"value": False}, "page_id": page_id},
        {"id": pid, "type": "PID_LOOP", "name": "PID", "params": {"pid": _pid_config()}, "page_id": page_id},
        {"id": output, "type": "FLOAT_OUTPUT", "name": "PID output", "params": {}, "page_id": page_id},
    ]
    links = [
        {"source_node_id": pv, "source_port": "OUT", "target_node_id": pid, "target_port": "PV"},
        {"source_node_id": sp, "source_port": "OUT", "target_node_id": pid, "target_port": "SP"},
        {"source_node_id": enable, "source_port": "OUT", "target_node_id": pid, "target_port": "ENABLE"},
        {"source_node_id": manual, "source_port": "OUT", "target_node_id": pid, "target_port": "MANUAL"},
        {"source_node_id": manual_out, "source_port": "OUT", "target_node_id": pid, "target_port": "MANUAL_OUT"},
        {"source_node_id": reset, "source_port": "OUT", "target_node_id": pid, "target_port": "RESET"},
        {"source_node_id": pid, "source_port": "OUT", "target_node_id": output, "target_port": "IN"},
    ]
    fbd.save(doc["id"], doc["revision"], nodes, links)
    state = {}
    auto = fbd.simulate(doc["id"], runtime_state=state)
    assert auto["outputs"]["PID output"] == 20.0
    manual_result = fbd.simulate(doc["id"], inputs={manual: True}, runtime_state=state)
    assert manual_result["outputs"]["PID output"] == 35.0
    returned_auto = fbd.simulate(doc["id"], inputs={manual: False}, runtime_state=state)
    assert returned_auto["outputs"]["PID output"] == 35.0
    reset_result = fbd.simulate(doc["id"], inputs={manual: False, reset: True}, runtime_state=state)
    assert reset_result["outputs"]["PID output"] == 20.0
    core.close()


def test_studio_compiles_pid_loop_and_all_four_outputs(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV190 Project")
    station = client.app.state.project_station.create_station(project["id"], "DEV190 Station")
    modules = [
        {"id": "pv", "type": "FLOAT_INPUT", "name": "PV", "params": {"value": 10.0}, "ins": [],
         "outs": [{"id": "pv-out", "name": "OUT", "type": "num"}]},
        {"id": "sp", "type": "FLOAT_INPUT", "name": "SP", "params": {"value": 20.0}, "ins": [],
         "outs": [{"id": "sp-out", "name": "OUT", "type": "num"}]},
        {"id": "enable", "type": "BOOL_INPUT", "name": "Enable", "params": {"value": True}, "ins": [],
         "outs": [{"id": "enable-out", "name": "OUT", "type": "bool"}]},
        {"id": "manual", "type": "BOOL_INPUT", "name": "Manual", "params": {"value": False}, "ins": [],
         "outs": [{"id": "manual-out", "name": "OUT", "type": "bool"}]},
        {"id": "manualout", "type": "FLOAT_INPUT", "name": "Manual output", "params": {"value": 35.0}, "ins": [],
         "outs": [{"id": "manualout-out", "name": "OUT", "type": "num"}]},
        {"id": "reset", "type": "BOOL_INPUT", "name": "Reset", "params": {"value": False}, "ins": [],
         "outs": [{"id": "reset-out", "name": "OUT", "type": "bool"}]},
        {"id": "pid", "type": "PID_LOOP", "name": "PID", "params": {"pid": _pid_config()},
         "ins": [{"id": "pid-pv", "name": "PV", "type": "num"},
                 {"id": "pid-sp", "name": "SP", "type": "num"},
                 {"id": "pid-enable", "name": "ENABLE", "type": "bool"},
                 {"id": "pid-manual", "name": "MANUAL", "type": "bool"},
                 {"id": "pid-manualout", "name": "MANUAL_OUT", "type": "num"},
                 {"id": "pid-reset", "name": "RESET", "type": "bool"}],
         "outs": [{"id": "pid-out", "name": "OUT", "type": "num"},
                  {"id": "pid-p", "name": "P", "type": "num"},
                  {"id": "pid-i", "name": "I", "type": "num"},
                  {"id": "pid-d", "name": "D", "type": "num"}]},
        {"id": "result", "type": "FLOAT_OUTPUT", "name": "PID result", "params": {},
         "ins": [{"id": "result-in", "name": "IN", "type": "num"}], "outs": []},
    ]
    pairs = [("pv", "PV"), ("sp", "SP"), ("enable", "ENABLE"), ("manual", "MANUAL"),
             ("manualout", "MANUAL_OUT"), ("reset", "RESET")]
    links = [
        {"id": f"l{i}", "pageId": "page-main", "from": f"out:{src}:0",
         "to": f"in:pid:{list(name for _, name in pairs).index(target)}",
         "signalType": "num" if src in {"pv", "sp", "manualout"} else "bool"}
        for i, (src, target) in enumerate(pairs)
    ]
    links.append({"id": "l-result", "pageId": "page-main", "from": "out:pid:0",
                  "to": "in:result:0", "signalType": "num"})
    data = {"format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "PID compile",
            "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": modules}],
            "links": links, "references": [], "fbdPoints": []}
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "PID compile", "data": data})
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
    pid_node = next(node for node in core_doc["nodes"] if node["type"] == "PID_LOOP")
    assert set(pid_node["ports"]["outputs"]) == {"OUT", "P", "I", "D"}
    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["PID result"] == 20.0
