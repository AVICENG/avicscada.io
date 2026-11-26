from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app
from avic_core.logic_fbd import FBDService


def _station(client):
    project = client.app.state.project_station.create_project("DEV187 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV187 Station")


def _graph(invalid=False):
    rows = [
        {"enabled": True, "cells": ["E", "F", "", ""]},
        {"enabled": True, "cells": ["", "g", "H", ""]},
        {"enabled": False, "cells": ["", "", "", ""]},
        {"enabled": False, "cells": ["", "", "", ""]},
    ]
    if invalid:
        rows[0]["cells"][0] = "Q"
    modules = []
    for key, value, y in (("e", True, 30), ("f", False, 120), ("g", False, 210), ("h", True, 300)):
        modules.append({
            "id": key, "type": "BOOL_INPUT", "name": key.upper(),
            "x": 20, "y": y, "params": {"value": value}, "ins": [],
            "outs": [{"id": f"{key}-out", "name": "OUT", "type": "bool"}],
        })
    modules.extend([
        {"id": "combo", "type": "COMBINATION", "name": "Combination", "x": 260, "y": 120,
         "params": {"comboRows": rows},
         "ins": [{"id": f"combo-{p.lower()}", "name": p, "type": "bool"} for p in "EFGH"],
         "outs": [{"id": "combo-out", "name": "OUT", "type": "bool"}]},
        {"id": "result", "type": "BOOL_OUTPUT", "name": "Разрешение", "x": 500, "y": 120,
         "params": {}, "ins": [{"id": "result-in", "name": "IN", "type": "bool"}], "outs": []},
    ])
    links = [
        {"id": f"l-{key}", "pageId": "page-main", "from": f"out:{key}:0",
         "to": f"in:combo:{index}", "signalType": "bool"}
        for index, key in enumerate(("e", "f", "g", "h"))
    ]
    links.append({"id": "l-result", "pageId": "page-main", "from": "out:combo:0",
                  "to": "in:result:0", "signalType": "bool"})
    return {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Combination parity",
        "pages": [{"id": "page-main", "name": "Основная", "code": "P1", "modules": modules}],
        "links": links, "references": [], "fbdPoints": [],
    }


def test_combination_compiles_and_executes_truth_table_in_core(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Combination parity", "data": _graph()},
    )
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert "COMBINATION" in preview.json()["supported_block_types"]

    compiled = client.post(
        f"/api/fbd-studio/{source['id']}/compile",
        json={"expected_revision": source["revision"]},
    )
    assert compiled.status_code == 200, compiled.text
    core_document = compiled.json()["core_document"]
    simulation = client.post(f"/api/fbd/{core_document['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["Разрешение"] is True
    assert simulation.json()["field_writes_performed"] is False


def test_combination_rejects_unknown_condition_cell(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Invalid Combination", "data": _graph(invalid=True)},
    )
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is False
    assert any("COMBINATION" in issue for issue in preview.json()["issues"])


def test_combination_catalog_defaults_use_python_boolean_values():
    rows = FBDService.BLOCKS["COMBINATION"]["defaults"]["comboRows"]
    assert [row["enabled"] for row in rows] == [True, False, False, False]
    assert all(type(row["enabled"]) is bool for row in rows)
