from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV186 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV186 Station")


def _source_graph(value="valid"):
    constant_value = 1.5 if value == "valid" else "NaN"
    return {
        "format": "AVIC-FBD-STRATEGY",
        "version": "1.1.1",
        "project": "KNOB and CONSTANT",
        "pages": [{
            "id": "page-main",
            "name": "Основная",
            "code": "P1",
            "modules": [
                {"id": "knob", "type": "KNOB", "name": "Уставка оператора",
                 "x": 30, "y": 40, "params": {"value": 50.0},
                 "ins": [], "outs": [{"id": "knob-out", "name": "OUT", "type": "num"}]},
                {"id": "constant", "type": "CONSTANT", "name": "Поправка",
                 "x": 30, "y": 180, "params": {"value": constant_value},
                 "ins": [], "outs": [{"id": "constant-out", "name": "OUT", "type": "num"}]},
                {"id": "sum", "type": "ADD", "name": "Расчётная уставка",
                 "x": 260, "y": 100, "params": {},
                 "ins": [{"id": "sum-a", "name": "A", "type": "num"},
                         {"id": "sum-b", "name": "B", "type": "num"}],
                 "outs": [{"id": "sum-out", "name": "OUT", "type": "num"}]},
                {"id": "result", "type": "FLOAT_OUTPUT", "name": "Результат",
                 "x": 480, "y": 100, "params": {},
                 "ins": [{"id": "result-in", "name": "IN", "type": "num"}], "outs": []},
            ],
        }],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:knob:0", "to": "in:sum:0", "signalType": "num"},
            {"id": "l2", "pageId": "page-main", "from": "out:constant:0", "to": "in:sum:1", "signalType": "num"},
            {"id": "l3", "pageId": "page-main", "from": "out:sum:0", "to": "in:result:0", "signalType": "num"},
        ],
        "references": [],
        "fbdPoints": [],
    }


def test_knob_and_constant_compile_and_execute_in_core(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "KNOB and CONSTANT", "data": _source_graph()},
    )
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert {"KNOB", "CONSTANT"} <= set(preview.json()["supported_block_types"])

    compiled = client.post(
        f"/api/fbd-studio/{source['id']}/compile",
        json={"expected_revision": source["revision"]},
    )
    assert compiled.status_code == 200, compiled.text
    core_document = compiled.json()["core_document"]
    assert {node["type"] for node in core_document["nodes"]} >= {"KNOB", "CONSTANT"}

    simulation = client.post(f"/api/fbd/{core_document['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["Результат"] == 51.5
    assert simulation.json()["field_writes_performed"] is False


def test_compiler_rejects_non_finite_constant_value(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Invalid constant", "data": _source_graph(value="invalid")},
    )
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is False
    assert any("CONSTANT" in issue for issue in preview.json()["issues"])
