from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV189 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV189 Station")


def _graph(invalid=False):
    analog_points = [[0.0, 0.0], [5.0, 100.0]]
    external_points = [[0.0, 0.0], [20.0, 40.0]]
    if invalid:
        analog_points = [[0.0, 0.0], [0.0, 100.0]]
    modules = [
        {"id": "analog", "type": "ANALOG_INPUT", "name": "Analog sensor",
         "params": {"rawValue": 2.5, "sensorType": 4, "scalingPoints": analog_points},
         "ins": [], "outs": [{"id": "analog-out", "name": "OUT", "type": "num"}]},
        {"id": "external", "type": "EXTERNAL_SENSOR", "name": "External sensor",
         "params": {"rawValue": 10.0, "sensorType": 77, "scalingPoints": external_points},
         "ins": [], "outs": [{"id": "external-out", "name": "OUT", "type": "num"}]},
        {"id": "sum", "type": "ADD", "name": "Sensor total", "params": {},
         "ins": [{"id": "sum-a", "name": "A", "type": "num"}, {"id": "sum-b", "name": "B", "type": "num"}],
         "outs": [{"id": "sum-out", "name": "OUT", "type": "num"}]},
        {"id": "result", "type": "FLOAT_OUTPUT", "name": "Scaled result", "params": {},
         "ins": [{"id": "result-in", "name": "IN", "type": "num"}], "outs": []},
    ]
    return {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Sensor sources",
        "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": modules}],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:analog:0", "to": "in:sum:0", "signalType": "num"},
            {"id": "l2", "pageId": "page-main", "from": "out:external:0", "to": "in:sum:1", "signalType": "num"},
            {"id": "l3", "pageId": "page-main", "from": "out:sum:0", "to": "in:result:0", "signalType": "num"},
        ],
        "references": [], "fbdPoints": [],
    }


def test_analog_input_and_external_sensor_compile_and_scale_in_core(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Sensor sources", "data": _graph()},
    )
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert {"ANALOG_INPUT", "EXTERNAL_SENSOR"} <= set(preview.json()["supported_block_types"])

    compiled = client.post(
        f"/api/fbd-studio/{source['id']}/compile",
        json={"expected_revision": source["revision"]},
    )
    assert compiled.status_code == 200, compiled.text
    core_doc = compiled.json()["core_document"]
    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["Scaled result"] == 70.0
    assert simulation.json()["field_writes_performed"] is False


def test_sensor_source_rejects_duplicate_scaling_abscissa(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Invalid sensor curve", "data": _graph(invalid=True)},
    )
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is False
    assert any("ANALOG_INPUT" in issue for issue in preview.json()["issues"])
