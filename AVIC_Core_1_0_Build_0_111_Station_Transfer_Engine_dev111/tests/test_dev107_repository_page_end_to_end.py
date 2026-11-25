from fastapi.testclient import TestClient

from avic_core.graphics import GraphicsService
from avic_core.points.runtime import FBDExposedPoint
from avic_core.ui.app import create_ui_app


def test_dev107_engineering_tree_to_published_ahu_page_with_assets_points_and_graphic(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "dev107-e2e"))
    client = TestClient(app)

    project = client.post("/api/projects", json={"name": "AHU Project", "description": ""}).json()
    station = client.post("/api/stations", json={
        "project_id": project["id"], "name": "AHU Station", "description": "",
    }).json()

    # The shared Repository branch must launch the Web Application editor in station scope.
    home = client.get("/")
    assert "section:'WebApplication'" in home.text
    editor = client.get(f"/repository?station={station['id']}&section=WebApplication")
    assert editor.status_code == 200 and "Библиотека элементов" in editor.text

    site = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Plant", "kind": "site",
    }).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "AHU-01 Overview", "kind": "page",
        "parent_id": site["id"], "slug": "ahu-01",
    }).json()

    point = FBDExposedPoint(
        name="Supply air temperature", station_id=station["id"],
        value=22.5, quality="GOOD", unit="°C", data_type="float",
    )
    app.state.core.repository.save(point)

    graphics = GraphicsService(app.state.core)
    graphic = graphics.create(station["id"], "AHU-01 Mimic")
    graphics.save(graphic["id"], graphic["revision"], [{
        "id": "7c56d5a0-02f5-4a5a-99e6-9a9a5a7d2099",
        "name": "Supply fan", "symbol_key": "fan",
        "x": 120, "y": 100, "width": 160, "height": 140,
        "bindings": [{
            "point_id": point.id, "role": "feedback", "binding_type": "status",
            "target_property": "animation", "settings": {"converter": "boolean"},
        }],
    }])

    assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
        "expected_revision": page["revision"], "graphic_id": graphic["id"],
    })
    assert assigned.status_code == 200, assigned.text

    png = bytes.fromhex(
        "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
        "0000000b49444154789c636000020000050001a5f645400000000049454e44ae426082"
    )
    uploaded = client.post(
        f"/api/stations/{station['id']}/repository-assets?filename=ahu.png",
        content=png, headers={"content-type": "image/png"},
    )
    assert uploaded.status_code == 201, uploaded.text
    asset = uploaded.json()

    layout = [
        {"type": "heading", "text": "Приточная установка AHU-01", "x": 24, "y": 18, "width": 600, "height": 58, "font_size": 28},
        {"type": "text", "text": "Состояние оборудования · этаж 1", "x": 24, "y": 82, "width": 440, "height": 42},
        {"type": "image", "src": asset["url"], "alt": "План установки", "x": 24, "y": 140, "width": 240, "height": 160},
        {"type": "value", "label": "Температура приточного воздуха", "point_id": point.id, "x": 290, "y": 140, "width": 260, "height": 90},
        {"type": "graphic", "graphic_id": graphic["id"], "label": "Мнемосхема AHU-01", "x": 580, "y": 90, "width": 700, "height": 520},
        {"type": "card", "text": "Фильтр\nКонтроль перепада давления", "x": 24, "y": 330, "width": 300, "height": 120},
        {"type": "divider", "x": 24, "y": 470, "width": 520, "height": 2},
    ]
    saved = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": assigned.json()["revision"], "layout": layout,
    })
    assert saved.status_code == 200, saved.text
    assert len(saved.json()["layout"]) == 7

    published = client.post(f"/api/web-pages/{page['id']}/publish", json={
        "expected_revision": saved.json()["revision"],
    })
    assert published.status_code == 200, published.text
    page_url = f"/published/{station['id']}/ahu-01"
    rendered = client.get(page_url)
    assert rendered.status_code == 200
    assert "Приточная установка AHU-01" in rendered.text
    assert "data-point-id" in rendered.text and point.id in rendered.text
    assert asset["url"] in rendered.text
    assert f"/published-graphics/{station['id']}/{graphic['id']}" in rendered.text

    live = client.get(f"/api/engineering/points/runtime?station_id={station['id']}")
    assert live.status_code == 200
    value = next(item for item in live.json()["points"] if item["point_id"] == point.id)
    assert value["value"] == 22.5 and value["quality"] == "GOOD"

    graphic_runtime = client.get(
        f"/published-graphics/{station['id']}/{graphic['id']}?page_id={page['id']}"
    )
    assert graphic_runtime.status_code == 200
    assert "Supply fan" in graphic_runtime.text
    bindings = client.get(
        f"/published-graphics/{station['id']}/{graphic['id']}/bindings?page_id={page['id']}"
    )
    assert bindings.status_code == 200
    assert next(iter(bindings.json()["bindings"].values()))["quality"] == "GOOD"

    app.state.core.close()
