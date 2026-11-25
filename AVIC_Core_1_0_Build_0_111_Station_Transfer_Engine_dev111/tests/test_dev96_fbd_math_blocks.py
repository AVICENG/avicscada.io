from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from avic_core.logic_fbd import FBDService
from avic_core.ui import create_ui_app
from test_graphics_workbench_dev35 import setup


@pytest.mark.parametrize(("block_type", "a", "b", "expected"), [
    ("SUB", 17.0, 5.0, 12.0),
    ("MUL", 3.0, 4.0, 12.0),
    ("DIV", 15.0, 3.0, 5.0),
])
def test_core_fbd_math_blocks_calculate_finite_values(tmp_path, block_type, a, b, expected):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], f"{block_type} test")
    ids = [str(uuid4()) for _ in range(4)]
    nodes = [
        {"id": ids[0], "type": "FLOAT_INPUT", "name": "A", "params": {"value": a}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "B", "params": {"value": b}},
        {"id": ids[2], "type": block_type, "name": "Расчёт"},
        {"id": ids[3], "type": "FLOAT_OUTPUT", "name": "Результат"},
    ]
    links = [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[2], "target_port": "A"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[2], "target_port": "B"},
        {"source_node_id": ids[2], "source_port": "OUT", "target_node_id": ids[3], "target_port": "IN"},
    ]
    saved = fbd.save(doc["id"], doc["revision"], nodes, links)
    result = fbd.simulate(saved["id"])
    assert result["outputs"]["Результат"] == pytest.approx(expected)
    assert result["field_writes_performed"] is False
    assert result["runtime_published"] is False
    core.close()


def test_core_fbd_division_by_zero_is_a_clear_simulation_error(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "DIV zero")
    ids = [str(uuid4()) for _ in range(3)]
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": ids[0], "type": "FLOAT_INPUT", "name": "Числитель", "params": {"value": 10}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "Знаменатель", "params": {"value": 0}},
        {"id": ids[2], "type": "DIV", "name": "Деление"},
    ], [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[2], "target_port": "A"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[2], "target_port": "B"},
    ])
    with pytest.raises(ValueError, match="деление на ноль"):
        fbd.simulate(saved["id"])
    core.close()


@pytest.mark.parametrize(("select", "expected"), [(True, 31.5), (False, 18.0)])
def test_core_fbd_select_chooses_the_correct_numeric_input(tmp_path, select, expected):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "SELECT test")
    ids = [str(uuid4()) for _ in range(5)]
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": ids[0], "type": "BOOL_INPUT", "name": "Выбор", "params": {"value": select}},
        {"id": ids[1], "type": "FLOAT_INPUT", "name": "A", "params": {"value": 31.5}},
        {"id": ids[2], "type": "FLOAT_INPUT", "name": "B", "params": {"value": 18.0}},
        {"id": ids[3], "type": "SELECT", "name": "Выбор уставки"},
        {"id": ids[4], "type": "FLOAT_OUTPUT", "name": "Уставка"},
    ], [
        {"source_node_id": ids[0], "source_port": "OUT", "target_node_id": ids[3], "target_port": "SEL"},
        {"source_node_id": ids[1], "source_port": "OUT", "target_node_id": ids[3], "target_port": "A"},
        {"source_node_id": ids[2], "source_port": "OUT", "target_node_id": ids[3], "target_port": "B"},
        {"source_node_id": ids[3], "source_port": "OUT", "target_node_id": ids[4], "target_port": "IN"},
    ])
    assert fbd.simulate(saved["id"])["outputs"]["Уставка"] == pytest.approx(expected)
    core.close()


def test_fbd_studio_compiler_accepts_and_compiles_sub_mul_div_select(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV96")
    station = client.app.state.project_station.create_station(project["id"], "Station")
    page_id = "math-page"
    modules = []
    links = []
    specs = [
        ("a", "FLOAT_INPUT", [], ["OUT"], {"value": 24.0}),
        ("b", "FLOAT_INPUT", [], ["OUT"], {"value": 6.0}),
        ("sel", "BOOL_INPUT", [], ["OUT"], {"value": True}),
        ("sub", "SUB", ["A", "B"], ["OUT"], {}),
        ("mul", "MUL", ["A", "B"], ["OUT"], {}),
        ("div", "DIV", ["A", "B"], ["OUT"], {}),
        ("choose", "SELECT", ["SEL", "A", "B"], ["OUT"], {}),
        ("out-sub", "FLOAT_OUTPUT", ["IN"], [], {}),
        ("out-mul", "FLOAT_OUTPUT", ["IN"], [], {}),
        ("out-div", "FLOAT_OUTPUT", ["IN"], [], {}),
        ("out-select", "FLOAT_OUTPUT", ["IN"], [], {}),
    ]
    for mid, typ, ins, outs, params in specs:
        modules.append({"id": mid, "type": typ, "name": mid, "x": 40, "y": 40,
                        "params": params,
                        "ins": [{"id": f"{mid}-in-{name}", "name": name, "type": "bool" if name == "SEL" else "num"} for name in ins],
                        "outs": [{"id": f"{mid}-out-{name}", "name": name, "type": "bool" if typ == "BOOL_INPUT" else "num"} for name in outs]})
    def link(source, target, index):
        links.append({"id": f"link-{len(links)}", "pageId": page_id,
                      "from": f"out:{source}:0", "to": f"in:{target}:{index}"})
    for block in ("sub", "mul", "div"):
        link("a", block, 0); link("b", block, 1)
    link("sel", "choose", 0); link("a", "choose", 1); link("b", "choose", 2)
    for block, output in (("sub", "out-sub"), ("mul", "out-mul"), ("div", "out-div"), ("choose", "out-select")):
        link(block, output, 0)
    data = {"format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Math parity",
            "pages": [{"id": page_id, "name": "Расчёты", "code": "P1", "modules": modules}],
            "links": links, "references": [], "fbdPoints": []}
    created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "Math parity", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview", json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True, preview.json()
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile", json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    result = client.post(f"/api/fbd/{compiled.json()['core_document']['id']}/simulate", json={})
    assert result.status_code == 200, result.text
    assert result.json()["outputs"] == {"out-sub": 18.0, "out-mul": 144.0, "out-div": 4.0, "out-select": 24.0}
