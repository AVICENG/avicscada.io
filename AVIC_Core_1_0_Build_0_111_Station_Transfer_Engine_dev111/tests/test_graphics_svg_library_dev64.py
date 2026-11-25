"""DEV64: packaged SVG library, safe delivery and persisted editor symbols."""
from fastapi.testclient import TestClient

from avic_core.graphics.svg_library import SVG_SYMBOLS, list_symbols, read_symbol_svg
from avic_core.ui.app import create_ui_app


def test_svg_library_has_real_packaged_vector_files():
    items = list_symbols()
    assert len(items) == len(SVG_SYMBOLS) >= 24
    assert {x["id"] for x in items} == set(SVG_SYMBOLS)
    assert len({x["category"] for x in items}) >= 5
    for item in items:
        data = read_symbol_svg(item["id"])
        text = data.decode("utf-8")
        assert text.startswith("<svg")
        assert "viewBox=" in text
        assert "<path" in text or "<circle" in text or "<rect" in text
        assert "<script" not in text.lower()


def test_svg_library_api_lists_categories_and_serves_whitelisted_assets(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    response = client.get("/api/graphics/library")
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == len(SVG_SYMBOLS)
    assert "Вентиляция" in payload["categories"]
    assert any(x["id"] == "temperature_sensor" for x in payload["items"])
    for item in payload["items"]:
        svg = client.get(item["svg_url"])
        assert svg.status_code == 200
        assert svg.headers["content-type"].startswith("image/svg+xml")
        assert svg.headers["x-content-type-options"] == "nosniff"
        assert b"<svg" in svg.content
    assert client.get("/api/graphics/library/not-a-symbol/svg").status_code == 404
    app.state.core.close()


def test_new_svg_symbol_can_be_saved_and_reopened_in_graphics_document(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "SVG test"}).json()
    station = client.post("/api/stations", json={"name": "Boiler room", "project_id": project["id"]}).json()
    created = client.post(f"/api/stations/{station['id']}/graphics", json={"name": "Схема котельной"})
    assert created.status_code == 201
    graphic = created.json()
    element = {
        "name": "Датчик температуры подачи",
        "symbol_key": "temperature_sensor",
        "x": 120, "y": 140, "width": 120, "height": 90,
        "rotation": 0, "bindings": [],
    }
    saved = client.put(
        f"/api/graphics/{graphic['id']}",
        json={"expected_revision": graphic["revision"], "elements": [element]},
    )
    assert saved.status_code == 200, saved.text
    reopened = client.get(f"/api/graphics/{graphic['id']}")
    assert reopened.status_code == 200
    assert reopened.json()["elements"][0]["symbol_key"] == "temperature_sensor"
    app.state.core.close()


def test_fbd_editor_uses_station_picker_existing_documents_and_port_wiring(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    page = client.get("/logic")
    assert page.status_code == 200
    html = page.text
    # DEV81+ uses the persistent engineering tree as the station/document selector.
    assert 'id="systemTree"' in html and "Инженерное дерево AVIC" in html
    assert 'data-fbd-document' in html and 'data-page=' in html
    assert "isCompatiblePortPair" in html and "data-port=" in html
    assert 'data-act="simulate"' in html
    app.state.core.close()


def test_fbd_workbench_can_create_open_save_and_simulate_fan_logic(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "FBD test"}).json()
    station = client.post("/api/stations", json={"name": "AHU", "project_id": project["id"]}).json()
    tree = client.get("/api/projects/tree").json()
    assert any(x["id"] == station["id"] for x in tree["stations"])

    created = client.post(f"/api/stations/{station['id']}/fbd/fan-demo", json={})
    assert created.status_code == 201, created.text
    graph = created.json()
    assert len(graph["nodes"]) == 4 and len(graph["links"]) == 3

    reopened = client.get(f"/api/fbd/{graph['id']}")
    assert reopened.status_code == 200
    assert reopened.json()["station_id"] == station["id"]

    sim = client.post(f"/api/fbd/{graph['id']}/simulate", json={"inputs": {}})
    assert sim.status_code == 200, sim.text
    result = sim.json()
    assert result["outputs"]["Вентилятор: RUN"] is True
    assert result["field_writes_performed"] is False
    app.state.core.close()


def test_main_workbench_menu_opens_the_real_svg_library_and_keeps_dropdowns_unclipped(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    root = client.get("/")
    assert root.status_code == 200
    html = root.text
    assert 'data-menu-toggle="engineering"' in html
    assert 'data-menu-action="symbols"' in html
    assert 'location.href=\'/graphics?panel=library\'' in html
    assert ".menu-dropdown.portal-open{position:fixed" in html
    assert "document.body.appendChild(menu)" in html
    assert "if(e.key==='Escape'){closeTopMenus()" in html
    app.state.core.close()


def test_graphics_editor_uses_flat_project_tree_and_real_svg_drag_drop_target(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "Tree contract"}).json()
    station = client.post("/api/stations", json={"name": "AHU station", "project_id": project["id"]}).json()
    tree = client.get("/api/projects/tree").json()
    assert any(x["id"] == project["id"] for x in tree["projects"])
    assert any(x["id"] == station["id"] and x["project_id"] == project["id"] for x in tree["stations"])
    html = client.get("/graphics").text
    assert "d.stations||[]).filter(x=>x.project_id===p.id)" in html
    assert "application/x-avic-svg-symbol" in html
    assert "$ ('canvas')" not in html
    app.state.core.close()
