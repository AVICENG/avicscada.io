from pathlib import Path

from fastapi.testclient import TestClient

from avic_core.points.runtime import FBDExposedPoint
from avic_core.ui import create_ui_app


def test_page_builder_selects_station_points_and_publishes_live_value_and_link(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "dev195-pages"))
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"name": "DEV195", "description": ""}).json()
        station = client.post("/api/stations", json={
            "project_id": project["id"], "name": "AHU station", "description": "",
        }).json()
        site = client.post("/api/web-pages", json={
            "station_id": station["id"], "name": "Plant", "kind": "site",
        }).json()
        page = client.post("/api/web-pages", json={
            "station_id": station["id"], "name": "AHU overview", "kind": "page",
            "parent_id": site["id"], "slug": "ahu-overview",
        }).json()

        point = FBDExposedPoint(
            name="Supply air temperature", station_id=station["id"],
            value=22.5, quality="GOOD", unit="°C", data_type="float",
        )
        app.state.core.repository.save(point)

        catalog = client.get(f"/api/engineering/points?station_id={station['id']}&limit=5000")
        assert catalog.status_code == 200
        assert any(item["id"] == point.id for item in catalog.json()["points"])

        saved = client.put(f"/api/web-pages/{page['id']}", json={
            "expected_revision": page["revision"],
            "layout": [
                {"type": "value", "label": "Температура притока", "point_id": point.id,
                 "x": 20, "y": 20, "width": 260, "height": 90},
                {"type": "button", "text": "Аварии", "href": "/alarms",
                 "x": 20, "y": 130, "width": 180, "height": 48},
            ],
        })
        assert saved.status_code == 200, saved.text
        published = client.post(f"/api/web-pages/{page['id']}/publish", json={
            "expected_revision": saved.json()["revision"],
        })
        assert published.status_code == 200, published.text

        rendered = client.get(f"/published/{station['id']}/ahu-overview")
        assert rendered.status_code == 200
        assert f'data-point-id="{point.id}"' in rendered.text
        assert 'href="/alarms"' in rendered.text
        assert "Аварии" in rendered.text

        # Cross-station point IDs must never be accepted by a page editor.
        other_station = client.post("/api/stations", json={
            "project_id": project["id"], "name": "Other station", "description": "",
        }).json()
        foreign_point = FBDExposedPoint(
            name="Foreign point", station_id=other_station["id"],
            value=1.0, quality="GOOD", unit="", data_type="float",
        )
        app.state.core.repository.save(foreign_point)
        rejected = client.put(f"/api/web-pages/{page['id']}", json={
            "expected_revision": published.json()["revision"],
            "layout": [{"type": "value", "label": "Wrong station",
                        "point_id": foreign_point.id, "x": 0, "y": 0,
                        "width": 200, "height": 80}],
        })
        assert rejected.status_code == 400
        app.state.core.close()

    ui_path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "pages.html"
    source = ui_path.read_text(encoding="utf-8")
    assert 'id="blockPoint"' in source
    assert "loadPointCatalog()" in source
    assert "/api/engineering/points?station_id=" in source
    assert "b.point_id=$('blockPoint').value" in source
    assert "bindDroppedPagePoint(pointId,index)" in source
    assert "getData('point')||e.dataTransfer.getData('fbd-point')" in source
