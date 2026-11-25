from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from avic_core.logic_fbd import FBDService
from avic_core.runtime.fbd_execution import FBDExecutionService
from avic_core.ui import create_ui_app
from test_graphics_workbench_dev35 import setup


def test_hysteresis_has_memory_between_simulation_passes(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Hysteresis")
    ids = [str(uuid4()) for _ in range(5)]
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": ids[0], "type": "FLOAT_INPUT", "name": "PV", "params": {"value": 19}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "LOW", "params": {"value": 18}},
        {"id": ids[2], "type": "FLOAT_INPUT", "name": "HIGH", "params": {"value": 22}},
        {"id": ids[3], "type": "HYSTERESIS", "name": "Термостат", "params": {"initial_state": False}},
        {"id": ids[4], "type": "BOOL_OUTPUT", "name": "HEAT"},
    ], [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[3], "target_port": "IN"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[3], "target_port": "LOW"},
        {"source_node_id": ids[2], "source_port": "OUT", "target_node_id": ids[3], "target_port": "HIGH"},
        {"source_node_id": ids[3], "source_port": "OUT", "target_node_id": ids[4], "target_port": "IN"},
    ])
    state = {}
    assert fbd.simulate(saved["id"], inputs={ids[0]: 23}, runtime_state=state)["outputs"]["HEAT"] is True
    assert fbd.simulate(saved["id"], inputs={ids[0]: 20}, runtime_state=state)["outputs"]["HEAT"] is True
    assert fbd.simulate(saved["id"], inputs={ids[0]: 17}, runtime_state=state)["outputs"]["HEAT"] is False
    core.close()


def test_hysteresis_rejects_invalid_thresholds_without_advancing_state(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Bad hysteresis")
    ids = [str(uuid4()) for _ in range(4)]
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": ids[0], "type": "FLOAT_INPUT", "name": "PV", "params": {"value": 20}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "LOW", "params": {"value": 22}},
        {"id": ids[2], "type": "FLOAT_INPUT", "name": "HIGH", "params": {"value": 22}},
        {"id": ids[3], "type": "HYSTERESIS", "name": "HYS"},
    ], [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[3], "target_port": "IN"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[3], "target_port": "LOW"},
        {"source_node_id": ids[2], "source_port": "OUT", "target_node_id": ids[3], "target_port": "HIGH"},
    ])
    state = {ids[3]: True}
    with pytest.raises(ValueError, match="LOW должен быть строго меньше HIGH"):
        fbd.simulate(saved["id"], runtime_state=state)
    assert state == {ids[3]: True}
    core.close()


def test_cyclic_runtime_retains_hysteresis_state_across_ticks(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "HYS runtime")
    ids = [str(uuid4()) for _ in range(5)]
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": ids[0], "type": "FLOAT_INPUT", "name": "PV", "params": {"value": 19}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "LOW", "params": {"value": 18}},
        {"id": ids[2], "type": "FLOAT_INPUT", "name": "HIGH", "params": {"value": 22}},
        {"id": ids[3], "type": "HYSTERESIS", "name": "Термостат"},
        {"id": ids[4], "type": "BOOL_OUTPUT", "name": "HEAT"},
    ], [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[3], "target_port": "IN"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[3], "target_port": "LOW"},
        {"source_node_id": ids[2], "source_port": "OUT", "target_node_id": ids[3], "target_port": "HIGH"},
        {"source_node_id": ids[3], "source_port": "OUT", "target_node_id": ids[4], "target_port": "IN"},
    ])
    runtime = FBDExecutionService(core)
    runtime.start(saved["id"], background=False)
    assert runtime.tick_once(saved["id"], inputs={ids[0]: 23})["result"]["outputs"]["HEAT"] is True
    assert runtime.tick_once(saved["id"], inputs={ids[0]: 20})["result"]["outputs"]["HEAT"] is True
    assert runtime.tick_once(saved["id"], inputs={ids[0]: 17})["result"]["outputs"]["HEAT"] is False
    runtime.stop(saved["id"])
    runtime.start(saved["id"], background=False)
    assert runtime.tick_once(saved["id"], inputs={ids[0]: 20})["result"]["outputs"]["HEAT"] is False
    runtime.close(); core.close()


def _studio_module(mid, typ, ins, outs, params=None):
    return {"id": mid, "type": typ, "name": mid, "x": 100, "y": 100,
            "params": params or {},
            "ins": [{"id": f"{mid}-in-{name}", "name": name, "type": "bool" if name == "SEL" else "num"} for name in ins],
            "outs": [{"id": f"{mid}-out-{name}", "name": name, "type": "bool" if typ == "HYSTERESIS" else "num"} for name in outs]}


def test_studio_compiler_compiles_scale_parameters_and_hysteresis(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV97")
    station = client.app.state.project_station.create_station(project["id"], "Station")
    page = "page-1"
    modules = [
        _studio_module("pv", "FLOAT_INPUT", [], ["OUT"], {"value": 150}),
        _studio_module("scale", "SCALE", ["IN"], ["OUT"], {"scale": {"inputLow": 0, "inputHigh": 100, "outputLow": 10, "outputHigh": 20}}),
        _studio_module("scale-out", "FLOAT_OUTPUT", ["IN"], []),
        _studio_module("hys", "HYSTERESIS", ["IN", "LOW", "HIGH"], ["OUT"], {"hysteresis": {"low": 18, "high": 22, "initial": 0}}),
        _studio_module("hys-out", "BOOL_OUTPUT", ["IN"], []),
    ]
    data = {"format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Scale Hysteresis",
            "pages": [{"id": page, "name": "P1", "code": "P1", "modules": modules}],
            "links": [
                {"id": "l1", "pageId": page, "from": "out:pv:0", "to": "in:scale:0"},
                {"id": "l2", "pageId": page, "from": "out:scale:0", "to": "in:scale-out:0"},
                {"id": "l3", "pageId": page, "from": "out:pv:0", "to": "in:hys:0"},
                {"id": "l4", "pageId": page, "from": "out:hys:0", "to": "in:hys-out:0"},
            ], "references": [], "fbdPoints": []}
    created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "DEV97", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview", json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True, preview.json()
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile", json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    core_id = compiled.json()["core_document"]["id"]
    simulated = client.post(f"/api/fbd/{core_id}/simulate", json={})
    assert simulated.status_code == 200, simulated.text
    assert simulated.json()["outputs"]["scale-out"] == pytest.approx(20.0)
    assert simulated.json()["outputs"]["hys-out"] is True


def test_studio_compiler_rejects_zero_width_scale_range(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV97 invalid")
    station = client.app.state.project_station.create_station(project["id"], "Station")
    data = {"format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "bad",
            "pages": [{"id": "p", "name": "P1", "modules": [
                _studio_module("in", "FLOAT_INPUT", [], ["OUT"], {"value": 50}),
                _studio_module("scale", "SCALE", ["IN"], ["OUT"], {"scale": {"inputLow": 2, "inputHigh": 2}}),
            ]}], "links": [{"id": "l", "pageId": "p", "from": "out:in:0", "to": "in:scale:0"}],
            "references": [], "fbdPoints": []}
    created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "bad", "data": data})
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview", json={"expected_revision": source["revision"]})
    assert preview.json()["compilable"] is False
    assert any("SCALE" in issue for issue in preview.json()["issues"])
