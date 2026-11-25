from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV82 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV82 Station")


def test_fbd_points_keep_protocol_neutral_identity_and_provenance_in_tree(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = {
        "pages": [{"id": "page-1", "name": "P1", "code": "P1", "modules": [{"id": "mod-4", "type": "PID_LOOP", "no": 4, "outs": [{"id": "port-pv", "name": "PV"}]}]}],
        "links": [],
        "fbdPoints": [{
            "id": "stable-uid-1", "tag": "FBDP-0001", "name": "Supply temperature",
            "path": "FBD/P1/PID_4/PV", "native_identity": "fbd://doc/page-1/mod-4/0",
            "symbolic_address": "P1.PID_4.PV", "dataType": "analog", "direction": "output",
            "source": {"pageId": "page-1", "moduleId": "mod-4", "portIndex": 0, "portId": "port-pv", "portName": "PV", "moduleType": "PID_LOOP", "moduleNo": 4},
            "license": {"status": "pending_core_registration"},
        }],
    }
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "AHU FBD", "data": data})
    assert created.status_code == 201
    point = client.get("/api/engineering/tree").json()["projects"][0]["stations"][0]["fbd_projects"][0]["points"][0]
    assert point["id"] == "stable-uid-1"
    assert point["native_identity"] == "fbd://doc/page-1/mod-4/0"
    assert point["symbolic_address"] == "P1.PID_4.PV"
    assert point["source"]["portName"] == "PV"
    assert point["source"]["portId"] == "port-pv"
    assert point["license_status"] == "pending_core_registration"


def test_fbd_studio_rejects_duplicate_page_names_and_duplicate_source_points(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    duplicate_pages = {"pages": [
        {"id": "p1", "name": "Main", "modules": []},
        {"id": "p2", "name": " main ", "modules": []},
    ], "links": []}
    response = client.post(f"/api/stations/{station['id']}/fbd-studio",
                           json={"name": "Bad pages", "data": duplicate_pages})
    assert response.status_code == 400

    duplicate_points = {"pages": [{"id": "p1", "name": "Main", "modules": [{"id": "m1", "outs": [{"name": "OUT"}]}]}], "links": [],
        "fbdPoints": [
            {"id": "one", "source": {"pageId": "p1", "moduleId": "m1", "portIndex": 0}},
            {"id": "two", "source": {"pageId": "p1", "moduleId": "m1", "portIndex": 0}},
        ]}
    response = client.post(f"/api/stations/{station['id']}/fbd-studio",
                           json={"name": "Bad points", "data": duplicate_points})
    assert response.status_code == 400


def test_fbd_project_rename_cannot_create_duplicate_station_name(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    base = {"pages": [{"id": "p1", "name": "P1", "modules": []}], "links": []}
    one = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "One", "data": base})
    two = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "Two", "data": base})
    assert one.status_code == two.status_code == 201
    response = client.put(f"/api/fbd-studio/{two.json()['id']}",
                          json={"expected_revision": 1, "name": "one", "data": base})
    assert response.status_code == 400


def test_all_workspaces_have_the_same_left_navigation(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    for route in ("/", "/repository", "/logic", "/graphics"):
        response = client.get(route)
        assert response.status_code == 200
        assert 'avic-global-rail' in response.text
        assert 'href="/logic"' in response.text or 'data-rail-page="logic"' in response.text
        assert 'href="/repository"' in response.text or 'data-rail-page="repository"' in response.text
        assert 'aria-label="Общая навигация AVIC"' in response.text


def test_fbd_studio_rejects_duplicate_module_tags_across_pages(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = {"pages": [
        {"id": "p1", "name": "P1", "modules": [{"id": "m1", "tag": "PID_001", "type": "PID_LOOP", "no": 1, "ins": [], "outs": []}]},
        {"id": "p2", "name": "P2", "modules": [{"id": "m2", "tag": "pid_001", "type": "PID_LOOP", "no": 2, "ins": [], "outs": []}]},
    ], "links": [], "fbdPoints": []}
    response = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "Duplicate tags", "data": data})
    assert response.status_code == 400

def test_fbd_logic_renderer_uses_unfilled_polyline_wires_and_stable_tags(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/logic")
    assert response.status_code == 200
    html = response.text
    assert 'function moduleTagPrefix(type)' in html
    assert 'function normalizeFbdIdentifiers()' in html
    assert 'function nextPointTag(signalType)' in html
    assert 'fill:none!important' in html
    assert '<polyline class="wire ' in html
    assert '<polyline class="wire-hit"' in html
