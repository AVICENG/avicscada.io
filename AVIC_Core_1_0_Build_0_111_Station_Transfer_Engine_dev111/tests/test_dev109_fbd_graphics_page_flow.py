from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _ahu_fbd(point_id: str) -> dict:
    return {
        "format": "AVIC-FBD-STRATEGY",
        "version": "1.1.1",
        "project": "DEV109 AHU",
        "pages": [{
            "id": "ahu-main", "name": "Основная", "code": "P1",
            "modules": [
                {"id": "start", "type": "BOOL_INPUT", "name": "Пуск", "x": 20, "y": 30,
                 "params": {"value": True}, "ins": [],
                 "outs": [{"id": "start-out", "name": "OUT", "type": "bool"}]},
                {"id": "safety", "type": "BOOL_INPUT", "name": "Защита", "x": 20, "y": 150,
                 "params": {"value": True}, "ins": [],
                 "outs": [{"id": "safety-out", "name": "OUT", "type": "bool"}]},
                {"id": "and", "type": "AND", "name": "Разрешение вентилятора", "x": 220, "y": 80,
                 "params": {}, "ins": [
                     {"id": "and-a", "name": "A", "type": "bool"},
                     {"id": "and-b", "name": "B", "type": "bool"}],
                 "outs": [{"id": "and-out", "name": "OUT", "type": "bool"}]},
                {"id": "out", "type": "BOOL_OUTPUT", "name": "RUN", "x": 420, "y": 80,
                 "params": {}, "ins": [{"id": "out-in", "name": "IN", "type": "bool"}], "outs": []},
            ],
        }],
        "links": [
            {"id": "l1", "pageId": "ahu-main", "from": "out:start:0", "to": "in:and:0", "signalType": "bool"},
            {"id": "l2", "pageId": "ahu-main", "from": "out:safety:0", "to": "in:and:1", "signalType": "bool"},
            {"id": "l3", "pageId": "ahu-main", "from": "out:and:0", "to": "in:out:0", "signalType": "bool"},
        ],
        "references": [],
        "fbdPoints": [{
            "id": point_id, "tag": "AHU_FAN_RUN", "name": "Команда вентилятора (виртуальная)",
            "path": "AHU-01/FBD/AHU_FAN_RUN", "dataType": "digital", "unit": "",
            "direction": "output",
            "source": {"pageId": "ahu-main", "moduleId": "and", "portIndex": 0,
                       "portId": "and-out", "portName": "OUT"},
            "license": {"status": "pending_core_registration"},
        }],
    }


def test_dev109_fbd_tree_point_to_graphic_bindings_and_published_page_survive_restart(tmp_path):
    data_dir = tmp_path / "dev109-data"
    app = create_ui_app(data_dir=str(data_dir))
    with TestClient(app) as client:
        project = client.post("/api/projects", json={"name": "DEV109 AHU"}).json()
        station = client.post("/api/stations", json={
            "project_id": project["id"], "name": "AHU-01",
        }).json()
        point_id = str(uuid4())
        created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={
            "name": "AHU-01 FBD", "data": _ahu_fbd(point_id),
        })
        assert created.status_code == 201, created.text
        source = created.json()
        compiled = client.post(f"/api/fbd-studio/{source['id']}/compile", json={
            "expected_revision": source["revision"],
        })
        assert compiled.status_code == 200, compiled.text
        core_document_id = compiled.json()["core_document"]["id"]

        started = client.post(f"/api/fbd-runtime/{core_document_id}/start", json={
            "interval_ms": 100, "background": False,
        })
        assert started.status_code == 200, started.text
        tick = client.post(f"/api/fbd-runtime/{core_document_id}/tick", json={})
        assert tick.status_code == 200, tick.text
        assert tick.json()["runtime_published"] is True

        tree = client.get("/api/engineering/tree").json()
        station_tree = tree["projects"][0]["stations"][0]
        tree_point = station_tree["fbd_projects"][0]["points"][0]
        assert tree_point["id"] == point_id
        assert tree_point["value"] is True and tree_point["quality"] == "GOOD"

        point_catalog = client.get(
            f"/api/stations/{station['id']}/graphics-points"
        ).json()["points"]
        assert any(p["id"] == point_id and p["quality"] == "GOOD" for p in point_catalog)

        graphics = client.post(f"/api/stations/{station['id']}/graphics", json={
            "name": "AHU-01 Мнемосхема",
        }).json()
        fan_id = str(uuid4())
        saved_graphic = client.put(f"/api/graphics/{graphics['id']}", json={
            "expected_revision": graphics["revision"],
            "elements": [{
                "id": fan_id, "name": "Вентилятор SF-01", "symbol_key": "fan",
                "x": 120, "y": 100, "width": 160, "height": 120,
                "rotation": 0, "layer": 1,
                "bindings": [
                    {"point_id": point_id, "role": "feedback", "binding_type": "status",
                     "target_property": "animation", "settings": {"converter": "boolean"}},
                    {"point_id": point_id, "role": "quality", "binding_type": "status",
                     "target_property": "status", "settings": {}},
                ],
            }],
        })
        assert saved_graphic.status_code == 200, saved_graphic.text
        assert len(saved_graphic.json()["elements"][0]["bindings"]) == 2

        reopened = client.get(f"/api/graphics/{graphics['id']}").json()
        assert reopened["elements"][0]["id"] == fan_id
        assert {b["role"] for b in reopened["elements"][0]["bindings"]} == {"feedback", "quality"}
        # Edit an existing symbol and persist the new graphic revision.
        edited_elements = reopened["elements"]
        edited_elements[0]["x"] = 140
        edited_graphic = client.put(f"/api/graphics/{graphics['id']}", json={
            "expected_revision": reopened["revision"], "elements": edited_elements,
        })
        assert edited_graphic.status_code == 200, edited_graphic.text
        assert edited_graphic.json()["elements"][0]["x"] == 140

        site = client.post("/api/web-pages", json={
            "station_id": station["id"], "name": "Здание", "kind": "site",
        }).json()
        page = client.post("/api/web-pages", json={
            "station_id": station["id"], "name": "AHU-01", "kind": "page",
            "parent_id": site["id"], "slug": "ahu-01",
        }).json()
        assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
            "expected_revision": page["revision"], "graphic_id": graphics["id"],
        })
        assert assigned.status_code == 200, assigned.text
        layout = [
            {"type": "heading", "text": "Приточная установка AHU-01",
             "x": 24, "y": 20, "width": 600, "height": 58},
            {"type": "value", "label": "Вентилятор SF-01",
             "point_id": point_id, "x": 24, "y": 100, "width": 260, "height": 90},
            {"type": "graphic", "graphic_id": graphics["id"],
             "label": "Мнемосхема AHU-01", "x": 320, "y": 90, "width": 700, "height": 520},
        ]
        saved_page = client.put(f"/api/web-pages/{page['id']}", json={
            "expected_revision": assigned.json()["revision"], "layout": layout,
        })
        assert saved_page.status_code == 200, saved_page.text
        published = client.post(f"/api/web-pages/{page['id']}/publish", json={
            "expected_revision": saved_page.json()["revision"],
        })
        assert published.status_code == 200, published.text
        first_published_revision = published.json()["published_revision"]

        # Re-open and edit the same page, then publish the next revision.
        page_reopened = client.get(f"/api/web-pages/{page['id']}").json()
        edited_layout = page_reopened["layout"]
        edited_layout[0]["text"] = "Приточная установка AHU-01 · редакция 2"
        edited_page = client.put(f"/api/web-pages/{page['id']}", json={
            "expected_revision": page_reopened["revision"], "layout": edited_layout,
        })
        assert edited_page.status_code == 200, edited_page.text
        republished = client.post(f"/api/web-pages/{page['id']}/publish", json={
            "expected_revision": edited_page.json()["revision"],
        })
        assert republished.status_code == 200, republished.text

        # Published geometry and bindings must remain frozen if the source graphic changes.
        live_graphic = client.get(f"/api/graphics/{graphics['id']}").json()
        changed_elements = live_graphic["elements"]
        changed_elements[0]["x"] = 900
        changed_elements[0]["bindings"] = []
        changed_graphic = client.put(f"/api/graphics/{graphics['id']}", json={
            "expected_revision": live_graphic["revision"], "elements": changed_elements,
        })
        assert changed_graphic.status_code == 200, changed_graphic.text

        rendered = client.get(f"/published/{station['id']}/ahu-01")
        assert rendered.status_code == 200
        assert "Приточная установка AHU-01 · редакция 2" in rendered.text
        assert point_id in rendered.text
        assert f"/published-graphics/{station['id']}/{graphics['id']}" in rendered.text

        graphic_runtime = client.get(
            f"/published-graphics/{station['id']}/{graphics['id']}?page_id={page['id']}"
        )
        assert graphic_runtime.status_code == 200, graphic_runtime.text
        assert "left:140px" in graphic_runtime.text
        assert "left:900px" not in graphic_runtime.text

        runtime = client.get(
            f"/published-graphics/{station['id']}/{graphics['id']}/bindings?page_id={page['id']}"
        )
        assert runtime.status_code == 200, runtime.text
        assert len(runtime.json()["bindings"]) == 2
        assert any(v["quality"] == "GOOD" and v["value"] is True
                   for v in runtime.json()["bindings"].values())

        # Roll back to the first published revision; its graphic snapshot must also survive.
        rolled_back = client.post(f"/api/web-pages/{page['id']}/rollback", json={
            "expected_revision": republished.json()["revision"],
            "target_published_revision": first_published_revision,
        })
        assert rolled_back.status_code == 200, rolled_back.text
        rolled_page = client.get(f"/published/{station['id']}/ahu-01")
        assert rolled_page.status_code == 200
        assert "Приточная установка AHU-01" in rolled_page.text
        assert "редакция 2" not in rolled_page.text
        rolled_graphic = client.get(
            f"/published-graphics/{station['id']}/{graphics['id']}?page_id={page['id']}"
        )
        assert rolled_graphic.status_code == 200, rolled_graphic.text
        assert "left:140px" in rolled_graphic.text
        rolled_bindings = client.get(
            f"/published-graphics/{station['id']}/{graphics['id']}/bindings?page_id={page['id']}"
        )
        assert rolled_bindings.status_code == 200, rolled_bindings.text
        assert len(rolled_bindings.json()["bindings"]) == 2

        # UI contract: the engineering tree emits the exact point IDs consumed by
        # Graphics Workbench; the editor accepts both physical and FBD drag payloads.
        from pathlib import Path
        from avic_core.ui import app as ui_module
        source_root = Path(ui_module.__file__).parent
        tree_ui = (source_root / "static" / "index.html").read_text(encoding="utf-8")
        graphics_ui = (source_root / "static" / "graphics.html").read_text(encoding="utf-8")
        assert "setData('fbd-point'" in tree_ui or "setData('fbd-point'" in (source_root / "app.py").read_text(encoding="utf-8")
        assert "getData('point')||e.dataTransfer.getData('fbd-point')" in graphics_ui
        assert "bindDroppedPoint(pointId,target)" in graphics_ui
        assert "getScreenCTM().inverse()" in graphics_ui
        pages_ui = (source_root / "static" / "pages.html").read_text(encoding="utf-8")
        assert 'id="publish"' in pages_ui and "function publishPage()" in pages_ui
        assert 'id="openPublished"' in pages_ui and "function openPublishedPage()" in pages_ui
        assert 'id="unpublish"' in pages_ui and "function unpublishPage()" in pages_ui
        assert 'id="rollback"' in pages_ui and "function rollbackPage()" in pages_ui
        assert 'id="publishedVersion"' in pages_ui and "/rollback" in pages_ui
        assert "/unpublish" in pages_ui and "/publish" in pages_ui

        client.post(f"/api/fbd-runtime/{core_document_id}/stop")
        app.state.core.close()

    # A fresh application process must reopen the persisted page and graphics data.
    reopened_app = create_ui_app(data_dir=str(data_dir))
    with TestClient(reopened_app) as client:
        page_after_restart = client.get(f"/api/web-pages/{page['id']}")
        assert page_after_restart.status_code == 200, page_after_restart.text
        graphic_after_restart = client.get(f"/api/graphics/{graphics['id']}")
        assert graphic_after_restart.status_code == 200, graphic_after_restart.text
        # The editable source graphic reflects the deliberate post-publication edit.
        assert graphic_after_restart.json()["elements"][0]["bindings"] == []
        # The published revision still owns the original frozen two bindings after restart.
        published_bindings_after_restart = client.get(
            f"/published-graphics/{station['id']}/{graphics['id']}/bindings?page_id={page['id']}"
        )
        assert published_bindings_after_restart.status_code == 200
        assert len(published_bindings_after_restart.json()["bindings"]) == 2
        reopened_app.state.core.close()
