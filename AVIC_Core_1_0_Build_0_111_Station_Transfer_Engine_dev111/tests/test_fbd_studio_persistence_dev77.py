from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def test_fbd_studio_document_is_station_scoped_and_revisioned(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    app = client.app
    project = app.state.project_station.create_project("DEV77 Project")
    station = app.state.project_station.create_station(project["id"], "DEV77 Station")
    payload = {"name": "AHU FBD", "data": {"format": "AVIC-FBD-STRATEGY", "version": "1.1.1",
               "project": "AHU FBD", "pages": [{"id": "page-1", "name": "Main", "modules": []}], "links": []}}
    created = client.post(f"/api/stations/{station['id']}/fbd-studio", json=payload)
    assert created.status_code == 201
    doc = created.json()
    assert doc["station_id"] == station["id"]
    assert doc["revision"] == 1
    assert doc["runtime_compiled"] is False
    listing = client.get(f"/api/stations/{station['id']}/fbd-studio").json()
    assert listing["documents"][0]["id"] == doc["id"]
    loaded = client.get(f"/api/fbd-studio/{doc['id']}").json()
    assert loaded["data"]["pages"][0]["name"] == "Main"
    updated = client.put(f"/api/fbd-studio/{doc['id']}", json={"expected_revision": 1,
        "name": "AHU FBD revised", "data": {**payload["data"], "description": "saved in Core"}})
    assert updated.status_code == 200
    assert updated.json()["revision"] == 2
    conflict = client.put(f"/api/fbd-studio/{doc['id']}", json={"expected_revision": 1, "data": payload["data"]})
    assert conflict.status_code == 409


def test_fbd_studio_document_rejects_oversized_or_invalid_graph(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("P")
    station = client.app.state.project_station.create_station(project["id"], "S")
    too_many = {"pages": [{"id": str(i), "modules": []} for i in range(251)], "links": []}
    response = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "Bad", "data": too_many})
    assert response.status_code == 400


def test_logic_route_uses_studio_111_and_core_tree(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/logic")
    assert response.status_code == 200
    assert "FBD Workbench 1.1.1" in response.text
    assert "Инженерное дерево AVIC" in response.text
    assert "/api/engineering/tree" in response.text
    assert "startDrag(e,id)" in response.text
    assert "persistStudioState" in response.text
    assert "core-tree-item" in response.text
    assert "Библиотека FBD-блоков" in response.text
    assert 'id="pageTree"' not in response.text
    assert "data-fbd-point-id" in response.text
    assert "dropFbdPointToPage" in response.text
    assert "dropFbdPointOnPort" in response.text
    assert "data-link" in response.text
    assert "Печать всего FBD-проекта" in response.text


def test_engineering_tree_projects_fbd_documents_pages_and_points(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("FBD Tree Project")
    station = client.app.state.project_station.create_station(project["id"], "FBD Tree Station")
    data = {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "AHU Strategy",
        "pages": [
            {"id": "page-main", "name": "Основная", "modules": [{"id": "m1"}, {"id": "m2"}]},
            {"id": "page-p02", "name": "Нагрев", "modules": []},
        ],
        "fbdPoints": [
            {"id": "fbdp-1", "tag": "FBDP-0001", "name": "Команда вентилятора", "path": "AHU/Fan/Cmd", "dataType": "digital"}
        ],
        "links": [],
    }
    created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "AHU Strategy", "data": data})
    assert created.status_code == 201
    tree = client.get("/api/engineering/tree").json()
    station_node = tree["projects"][0]["stations"][0]
    assert len(station_node["fbd_projects"]) == 1
    fbd = station_node["fbd_projects"][0]
    assert fbd["id"] == created.json()["id"]
    assert fbd["pages"] == [
        {"id": "page-main", "code": "P1", "name": "Основная", "module_count": 2},
        {"id": "page-p02", "code": "P2", "name": "Нагрев", "module_count": 0},
    ]
    assert fbd["points"][0]["id"] == "fbdp-1"
    assert fbd["points"][0]["data_type"] == "digital"


def test_engineering_tree_lists_multiple_fbd_projects_for_one_station(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("Multi FBD Project")
    station = client.app.state.project_station.create_station(project["id"], "Multi FBD Station")
    for name, page_id in (("AHU Supply", "supply"), ("AHU Extract", "extract"), ("Boiler", "boiler")):
        response = client.post(f"/api/stations/{station['id']}/fbd-studio", json={
            "name": name,
            "data": {"project": name, "pages": [{"id": page_id, "name": "Main", "modules": []}], "links": []},
        })
        assert response.status_code == 201
    tree = client.get("/api/engineering/tree").json()
    station_node = tree["projects"][0]["stations"][0]
    assert [doc["name"] for doc in station_node["fbd_projects"]] == ["AHU Extract", "AHU Supply", "Boiler"]


def test_logic_route_contains_global_context_and_multi_project_navigation(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    html = client.get("/logic").text
    assert "Unified right-click handling" in html
    assert "data-fbd-document" in html
    assert "data-create-fbd-project" in html
    assert "grid-template-columns:repeat(auto-fit,minmax(92px,1fr))" in html
    assert "Печать всего FBD-проекта" in html


def test_fbd_studio_project_names_unique_and_project_can_be_deleted(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV81 Project")
    station = client.app.state.project_station.create_station(project["id"], "DEV81 Station")
    payload = {"data": {"pages": [{"id": "p1", "name": "Main", "modules": []}], "links": []}}
    first = client.post(f"/api/stations/{station['id']}/fbd-studio", json={**payload, "name": "AHU"})
    assert first.status_code == 201
    duplicate = client.post(f"/api/stations/{station['id']}/fbd-studio", json={**payload, "name": "ahu"})
    assert duplicate.status_code == 400
    doc_id = first.json()["id"]
    deleted = client.delete(f"/api/fbd-studio/{doc_id}?expected_revision=1")
    assert deleted.status_code == 200
    assert deleted.json()["deleted"] is True
    assert client.get(f"/api/fbd-studio/{doc_id}").status_code == 404
