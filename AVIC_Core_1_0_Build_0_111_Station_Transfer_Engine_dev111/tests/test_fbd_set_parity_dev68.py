"""DEV68 SET-style strategy pages and cross-page connective regression tests."""
import pytest
from uuid import uuid4
from avic_core.logic_fbd import FBDService
from test_graphics_workbench_dev35 import setup


def _two_page_graph(tmp_path):
    core, station, _ = setup(tmp_path)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Многостраничная стратегия")
    first = doc["pages"][0]
    doc = svc.add_page(doc["id"], "Управление")
    second = next(p for p in doc["pages"] if p["name"] == "Управление")
    a, b = str(uuid4()), str(uuid4())
    nodes = [
        {"id": a, "type": "BOOL_INPUT", "name": "Разрешение", "x": 50, "y": 80,
         "params": {"value": True}, "page_id": first["id"]},
        {"id": b, "type": "BOOL_OUTPUT", "name": "Команда вентилятора", "x": 50, "y": 80,
         "page_id": second["id"]},
    ]
    saved = svc.save(doc["id"], doc["revision"], nodes, [])
    return svc, saved, first, second, a, b


def test_strategy_document_starts_with_persisted_first_page(tmp_path):
    core, station, _ = setup(tmp_path)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Стратегия")
    reopened = svc.get(doc["id"])
    assert len(reopened["pages"]) == 1
    assert reopened["pages"][0]["name"] == "Страница 1"


def test_strategy_page_create_rename_and_delete_guards(tmp_path):
    core, station, _ = setup(tmp_path)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Стратегия")
    doc = svc.add_page(doc["id"], "Пуск")
    page = next(p for p in doc["pages"] if p["name"] == "Пуск")
    doc = svc.rename_page(doc["id"], page["id"], "Пуск/Стоп")
    assert any(p["name"] == "Пуск/Стоп" for p in doc["pages"])
    doc = svc.delete_page(doc["id"], page["id"])
    assert len(doc["pages"]) == 1
    with pytest.raises(ValueError, match="последнюю страницу"):
        svc.delete_page(doc["id"], doc["pages"][0]["id"])


def test_node_page_assignment_persists_and_is_returned(tmp_path):
    svc, doc, first, second, a, b = _two_page_graph(tmp_path)
    reopened = svc.get(doc["id"])
    assert {n["id"]: n["page_id"] for n in reopened["nodes"]} == {
        a: first["id"], b: second["id"]
    }


def test_cross_page_connective_validates_types_and_persists(tmp_path):
    svc, doc, first, second, a, b = _two_page_graph(tmp_path)
    linked = svc.create_connective(doc["id"], {
        "name": "Разрешение ПВ-1",
        "source_page_id": first["id"], "source_node_id": a, "source_port": "OUT",
        "target_page_id": second["id"], "target_node_id": b, "target_port": "IN",
    })
    assert len(linked["connectives"]) == 1
    c = linked["connectives"][0]
    assert c["source_page_id"] == first["id"] and c["target_page_id"] == second["id"]
    reopened = svc.get(doc["id"])
    assert reopened["connectives"][0]["id"] == c["id"]


def test_connective_rejects_wrong_signal_type(tmp_path):
    svc, doc, first, second, a, b = _two_page_graph(tmp_path)
    with pytest.raises(ValueError, match="Несовместимые типы"):
        svc.create_connective(doc["id"], {
            "name": "Ошибка типа",
            "source_page_id": first["id"], "source_node_id": a, "source_port": "OUT",
            "target_page_id": second["id"], "target_node_id": b, "target_port": "NOT_A_PORT",
        })


def test_page_with_assigned_nodes_cannot_be_deleted(tmp_path):
    svc, doc, first, second, a, b = _two_page_graph(tmp_path)
    with pytest.raises(ValueError, match="размещены блоки"):
        svc.delete_page(doc["id"], second["id"])


def test_cross_page_connective_participates_in_offline_simulation(tmp_path):
    svc, doc, first, second, a, b = _two_page_graph(tmp_path)
    svc.create_connective(doc["id"], {
        "name": "Пуск между страницами",
        "source_page_id": first["id"], "source_node_id": a, "source_port": "OUT",
        "target_page_id": second["id"], "target_node_id": b, "target_port": "IN",
    })
    result = svc.simulate(doc["id"])
    assert result["outputs"]["Команда вентилятора"] is True
    assert result["field_writes_performed"] is False


def test_strategy_pages_and_connectives_http_api(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    client = TestClient(create_ui_app(data_dir=str(tmp_path / "api")))
    project = client.post("/api/projects", json={"name": "FBD API"}).json()
    station = client.post("/api/stations", json={"name": "Plant", "project_id": project["id"]}).json()
    created = client.post(f"/api/stations/{station['id']}/fbd", json={"name": "Strategy", "description": ""})
    assert created.status_code == 201, created.text
    doc = created.json()
    first = doc["pages"][0]
    added = client.post(f"/api/fbd/{doc['id']}/pages", json={"name": "Page 2"})
    assert added.status_code == 201, added.text
    doc = added.json()
    second = next(p for p in doc["pages"] if p["name"] == "Page 2")
    a, b = str(uuid4()), str(uuid4())
    saved = client.put(f"/api/fbd/{doc['id']}", json={
        "expected_revision": doc["revision"],
        "nodes": [
            {"id": a, "type": "BOOL_INPUT", "name": "Start", "page_id": first["id"], "params": {"value": True}},
            {"id": b, "type": "BOOL_OUTPUT", "name": "Run", "page_id": second["id"]},
        ],
        "links": [],
    })
    assert saved.status_code == 200, saved.text
    linked = client.post(f"/api/fbd/{doc['id']}/connectives", json={
        "name": "Start to Run", "source_page_id": first["id"], "source_node_id": a,
        "source_port": "OUT", "target_page_id": second["id"], "target_node_id": b, "target_port": "IN",
    })
    assert linked.status_code == 201, linked.text
    assert len(linked.json()["connectives"]) == 1
    assert client.post(f"/api/fbd/{doc['id']}/simulate", json={}).json()["outputs"]["Run"] is True
