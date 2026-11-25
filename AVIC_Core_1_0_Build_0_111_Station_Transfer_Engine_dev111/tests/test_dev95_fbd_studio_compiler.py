from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV95 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV95 Station")


def _studio_graph():
    return {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Fan Permit",
        "pages": [{"id": "page-main", "name": "Основная", "code": "P1", "modules": [
            {"id": "start", "type": "BOOL_INPUT", "name": "Команда Пуск", "x": 30, "y": 40,
             "params": {"value": True}, "ins": [], "outs": [{"id": "start-out", "name": "OUT", "type": "bool"}]},
            {"id": "safe", "type": "BOOL_INPUT", "name": "Защита исправна", "x": 30, "y": 180,
             "params": {"value": True}, "ins": [], "outs": [{"id": "safe-out", "name": "OUT", "type": "bool"}]},
            {"id": "and", "type": "AND", "name": "Разрешение", "x": 260, "y": 100,
             "params": {}, "ins": [{"id": "and-a", "name": "A", "type": "bool"}, {"id": "and-b", "name": "B", "type": "bool"}],
             "outs": [{"id": "and-out", "name": "OUT", "type": "bool"}]},
            {"id": "out", "type": "BOOL_OUTPUT", "name": "RUN", "x": 480, "y": 100,
             "params": {}, "ins": [{"id": "out-in", "name": "IN", "type": "bool"}], "outs": []},
        ]}],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:start:0", "to": "in:and:0", "signalType": "bool"},
            {"id": "l2", "pageId": "page-main", "from": "out:safe:0", "to": "in:and:1", "signalType": "bool"},
            {"id": "l3", "pageId": "page-main", "from": "out:and:0", "to": "in:out:0", "signalType": "bool"},
        ],
        "references": [], "fbdPoints": [],
    }


def test_fbd_studio_compile_preview_and_compile_to_executable_core_graph(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "AHU Permit", "data": _studio_graph()})
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert preview.json()["source_blocks"] == 4
    assert preview.json()["source_links"] == 3

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    result = compiled.json()
    core_doc = result["core_document"]
    assert result["compiled_blocks"] == 4
    assert result["compiled_links"] == 3
    assert result["field_writes_enabled"] is False
    assert result["runtime_published"] is False

    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["RUN"] is True

    # Compilation creates a separate executable document; it never rewrites Studio.
    loaded = client.get(f"/api/fbd-studio/{source['id']}").json()
    assert loaded["revision"] == source["revision"]
    assert loaded["data"] == _studio_graph()


def test_fbd_studio_compiler_refuses_unknown_semantics_without_creating_core_document(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"][0]["modules"][2]["type"] = "PID_LOOP"
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Unsupported PID", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    before = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]

    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200
    assert preview.json()["compilable"] is False
    assert any("PID_LOOP" in issue for issue in preview.json()["issues"])

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 400
    after = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]
    assert after == before


def test_fbd_studio_compiler_rejects_stale_revision(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Stale", "data": _studio_graph()})
    source = created.json()
    response = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                           json={"expected_revision": source["revision"] + 1})
    assert response.status_code == 409
    assert "CONCURRENCY_CONFLICT" in response.json()["detail"]


def test_fbd_studio_compiler_preserves_multiple_pages(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"].append({"id": "page-second", "name": "Нагрев", "code": "P2", "modules": [
        {"id": "heat", "type": "FLOAT_INPUT", "name": "Температура подачи", "x": 40, "y": 40,
         "params": {"value": 35.0}, "ins": [], "outs": [{"id": "heat-out", "name": "OUT", "type": "num"}]}
    ]})
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Two pages", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    pages = compiled.json()["core_document"]["pages"]
    assert [page["name"] for page in pages] == ["Основная", "Нагрев"]
    assert len(compiled.json()["core_document"]["nodes"]) == 5
    assert {node["page_id"] for node in compiled.json()["core_document"]["nodes"]} == {p["id"] for p in pages}


def test_fbd_studio_compile_is_idempotent_for_same_source_revision(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Idempotent", "data": _studio_graph()})
    source = created.json()
    first = client.post(f"/api/fbd-studio/{source['id']}/compile",
                        json={"expected_revision": source["revision"]})
    second = client.post(f"/api/fbd-studio/{source['id']}/compile",
                         json={"expected_revision": source["revision"]})
    assert first.status_code == second.status_code == 200
    assert first.json()["core_document"]["id"] == second.json()["core_document"]["id"]
    assert second.json()["already_compiled"] is True
    docs = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]
    assert len(docs) == 1


def test_fbd_studio_compiler_normalizes_values_edited_as_text_in_ui(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"][0]["modules"][0]["params"]["value"] = "Да"
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Text values", "data": data})
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200 and preview.json()["compilable"] is True
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    nodes = compiled.json()["core_document"]["nodes"]
    start = next(node for node in nodes if node["name"] == "Команда Пуск")
    assert start["params"]["value"] is True
