from fastapi.testclient import TestClient

from avic_core.ui.app import create_ui_app


def _workspace(client: TestClient):
    project = client.post("/api/projects", json={"name": "Pages DEV65"}).json()
    station = client.post("/api/stations", json={"name": "Station A", "project_id": project["id"]}).json()
    return project, station


def test_visual_page_components_save_reopen_and_keep_graphic_assignment(tmp_path):
    data_dir = tmp_path / "persisted"
    app = create_ui_app(data_dir=str(data_dir))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Plant", "kind": "site",
    }).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Overview", "kind": "page",
        "parent_id": site["id"], "slug": "overview",
    }).json()
    graphic = client.post(f"/api/stations/{station['id']}/graphics", json={"name": "AHU-01"}).json()
    assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
        "expected_revision": page["revision"], "graphic_id": graphic["id"],
    })
    assert assigned.status_code == 200, assigned.text

    from avic_core.points.runtime import FBDExposedPoint
    virtual_point = FBDExposedPoint(name="Supply temperature", station_id=station["id"], value=22.0, quality="GOOD", unit="°C")
    app.state.core.repository.save(virtual_point)
    layout = [
        {"type": "heading", "text": "Приточная установка", "x": 20, "y": 20, "width": 520, "height": 64, "font_size": 28},
        {"type": "text", "text": "Состояние оборудования", "x": 20, "y": 100, "width": 420, "height": 80},
        {"type": "card", "text": "Фильтр\nПерепад давления", "x": 20, "y": 200, "width": 300, "height": 150},
        {"type": "button", "text": "Аварии", "href": "/pages/alarms", "x": 350, "y": 200, "width": 160, "height": 48},
        {"type": "image", "alt": "План", "src": "/static/plan.png", "x": 20, "y": 370, "width": 320, "height": 180},
        {"type": "divider", "x": 20, "y": 570, "width": 520, "height": 3},
        {"type": "value", "text": "Температура подачи", "point_id": virtual_point.id, "x": 20, "y": 590, "width": 220, "height": 100},
        {"type": "graphic", "graphic_id": graphic["id"], "label": "Мнемосхема AHU-01", "x": 560, "y": 20, "width": 600, "height": 480},
    ]
    saved = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": assigned.json()["revision"], "layout": layout,
        "html": "<header>Производственный объект</header>",
        "css": ".visual-page { background: #f5f7fa; }",
    })
    assert saved.status_code == 200, saved.text
    assert len(saved.json()["layout"]) == 8
    assert saved.json()["layout"][5]["height"] == 3  # divider is intentionally thin
    app.state.core.close()

    reopened_app = create_ui_app(data_dir=str(data_dir))
    reopened = TestClient(reopened_app).get(f"/api/web-pages/{page['id']}")
    assert reopened.status_code == 200
    body = reopened.json()
    assert [item["type"] for item in body["layout"]] == [
        "heading", "text", "card", "button", "image", "divider", "value", "graphic"
    ]
    assert body["graphic_ids"] == [graphic["id"]]
    assert body["layout"][-1]["graphic_id"] == graphic["id"]
    reopened_app.state.core.close()


def test_page_builder_rejects_active_and_protocol_relative_urls(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Site", "kind": "site"}).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Page", "kind": "page", "parent_id": site["id"], "slug": "home",
    }).json()

    unsafe_href = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"],
        "layout": [{"type": "button", "text": "Run", "href": "javascript:alert(1)"}],
    })
    assert unsafe_href.status_code == 400
    protocol_relative_src = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"],
        "layout": [{"type": "image", "src": "//evil.example/pixel.svg"}],
    })
    assert protocol_relative_src.status_code == 400
    malformed_type = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"], "layout": [{"type": {"invalid": True}}],
    })
    assert malformed_type.status_code == 400
    malformed_alignment = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"], "layout": [{"type": "text", "align": ["left"]}],
    })
    assert malformed_alignment.status_code == 400
    app.state.core.close()


def test_web_page_reorder_endpoint_changes_sibling_order_and_slug_is_unique_across_folder_and_page(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Site", "kind": "site"}).json()
    folder = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Section", "kind": "folder", "parent_id": site["id"], "slug": "section",
    }).json()
    page_a = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "A", "kind": "page", "parent_id": site["id"], "slug": "a",
    }).json()
    page_b = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "B", "kind": "page", "parent_id": site["id"], "slug": "b",
    }).json()
    collision = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Collision", "kind": "page", "parent_id": site["id"], "slug": "section",
    })
    assert collision.status_code == 400

    moved = client.post(f"/api/web-pages/{page_b['id']}/reorder", json={"direction": "up"})
    assert moved.status_code == 200, moved.text
    tree = client.get(f"/api/stations/{station['id']}/web-pages").json()
    site_node = tree["nodes"][0]
    assert [x["id"] for x in site_node["children"]] == [page_b["id"], page_a["id"], folder["id"]]

    bad_direction = client.post(f"/api/web-pages/{page_b['id']}/reorder", json={"direction": "sideways"})
    assert bad_direction.status_code == 422
    app.state.core.close()


def test_unassigning_graphic_also_removes_visual_component_reference(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Site", "kind": "site"}).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Page", "kind": "page", "parent_id": site["id"], "slug": "home",
    }).json()
    graphic = client.post(f"/api/stations/{station['id']}/graphics", json={"name": "Mimic"}).json()
    assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
        "expected_revision": page["revision"], "graphic_id": graphic["id"],
    }).json()
    with_layout = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": assigned["revision"],
        "layout": [{"type": "graphic", "graphic_id": graphic["id"], "x": 20, "y": 20, "width": 500, "height": 300}],
    }).json()
    response = client.delete(
        f"/api/web-pages/{page['id']}/graphics/{graphic['id']}?expected_revision={with_layout['revision']}"
    )
    assert response.status_code == 200, response.text
    assert response.json()["graphic_ids"] == []
    assert response.json()["layout"] == []
    app.state.core.close()


def test_page_publish_creates_immutable_snapshot_and_operator_route(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "publish-data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Plant", "kind": "site"}).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "AHU Overview", "kind": "page",
        "parent_id": site["id"], "slug": "ahu-overview",
    }).json()
    from avic_core.points.runtime import FBDExposedPoint
    virtual_point = FBDExposedPoint(name="Supply temperature", station_id=station["id"], value=23.5, quality="GOOD", unit="°C")
    app.state.core.repository.save(virtual_point)
    saved = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"],
        "layout": [
            {"type": "heading", "text": "Приточная установка", "x": 20, "y": 20, "width": 500, "height": 60},
            {"type": "image", "src": "https://example.com/ahu.svg", "alt": "AHU", "x": 20, "y": 100, "width": 220, "height": 140},
            {"type": "value", "label": "Температура подачи", "point_id": virtual_point.id, "x": 270, "y": 100, "width": 220, "height": 80},
        ],
    }).json()
    published = client.post(f"/api/web-pages/{page['id']}/publish", json={"expected_revision": saved["revision"]})
    assert published.status_code == 200, published.text
    body = published.json()
    assert body["published"] is True
    assert body["published_revision"] == body["revision"]
    assert body["published_at"]
    runtime = client.get(f"/api/engineering/points/runtime?station_id={station['id']}").json()
    assert any(item["point_id"] == virtual_point.id and item["value"] == 23.5 for item in runtime["points"])
    url = f"/published/{station['id']}/ahu-overview"
    response = client.get(url)
    assert response.status_code == 200
    assert "Приточная установка" in response.text
    assert "Температура подачи" in response.text
    assert "23.5 °C" in response.text
    assert "script-src 'nonce-" in response.headers["content-security-policy"]
    assert "setInterval(update,2000)" in response.text
    assert "/api/engineering/points/runtime?station_id=" in response.text
    assert f'data-point-id="{virtual_point.id}"' in response.text
    # Draft changes do not mutate the already published layout snapshot.
    draft = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": body["revision"], "layout": [{"type": "heading", "text": "Черновик"}],
    })
    assert draft.status_code == 200
    response = client.get(url)
    assert "Приточная установка" in response.text
    assert "Черновик" not in response.text
    second_publish = client.post(f"/api/web-pages/{page['id']}/publish", json={"expected_revision": draft.json()["revision"]})
    assert second_publish.status_code == 200, second_publish.text
    assert "Черновик" in client.get(url).text
    rolled_back = client.post(f"/api/web-pages/{page['id']}/rollback", json={
        "expected_revision": second_publish.json()["revision"],
        "target_published_revision": body["published_revision"],
    })
    assert rolled_back.status_code == 200, rolled_back.text
    assert "Приточная установка" in client.get(url).text
    assert rolled_back.json()["published_versions"][-1]["rollback_of"] == body["published_revision"]
    app.state.core.close()


def test_empty_page_cannot_be_published_and_repository_uses_new_editor(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "editor-data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Plant", "kind": "site"}).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Empty", "kind": "page", "parent_id": site["id"], "slug": "empty",
    }).json()
    response = client.post(f"/api/web-pages/{page['id']}/publish", json={"expected_revision": page["revision"]})
    assert response.status_code == 400
    editor = client.get(f"/repository?station={station['id']}&section=WebApplication")
    assert editor.status_code == 200
    assert "Библиотека элементов" in editor.text
    assert "pages.html" not in editor.text
    app.state.core.close()


def test_repository_image_upload_is_station_scoped_and_served_after_publish(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "assets-data"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Plant", "kind": "site"}).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Home", "kind": "page", "parent_id": site["id"], "slug": "home",
    }).json()
    png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000b49444154789c636000020000050001a5f645400000000049454e44ae426082")
    uploaded = client.post(f"/api/stations/{station['id']}/repository-assets?filename=ahu.png", content=png, headers={"content-type": "image/png"})
    assert uploaded.status_code == 201, uploaded.text
    asset = uploaded.json()
    assert asset["byte_size"] == len(png)
    assert client.get(asset["url"]).content == png
    saved = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": page["revision"],
        "layout": [{"type": "image", "src": asset["url"], "alt": "AHU", "x": 10, "y": 10, "width": 220, "height": 120}],
    }).json()
    assert saved["layout"][0]["src"] == asset["url"]
    published = client.post(f"/api/web-pages/{page['id']}/publish", json={"expected_revision": saved["revision"]}).json()
    public_asset = client.get(asset["url"])
    assert public_asset.status_code == 200
    assert public_asset.headers["x-content-type-options"] == "nosniff"
    assert client.get(f"/published/{station['id']}/home").status_code == 200
    bad = client.post(f"/api/stations/{station['id']}/repository-assets?filename=bad.png", content=b"not an image", headers={"content-type": "image/png"})
    assert bad.status_code == 400
    app.state.core.close()


def test_created_pages_are_projected_into_the_shared_engineering_tree(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path / "shared-tree")))
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={"station_id": station["id"], "name": "Plant Web", "kind": "site"}).json()
    folder = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "HVAC", "kind": "folder", "parent_id": site["id"], "slug": "hvac",
    }).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "AHU", "kind": "page", "parent_id": folder["id"], "slug": "ahu",
    }).json()
    tree = client.get("/api/engineering/tree").json()
    station_node = next(st for project in tree["projects"] for st in project["stations"] if st["id"] == station["id"])
    web_app = next(x for x in station_node["repository"]["children"] if x["type"] == "WebApplication")
    assert web_app["children"][0]["id"] == site["id"]
    assert web_app["children"][0]["children"][0]["id"] == folder["id"]
    assert web_app["children"][0]["children"][0]["children"][0]["id"] == page["id"]


def test_published_page_embeds_frozen_graphics_runtime_with_live_point_values(tmp_path):
    from avic_core.points.runtime import FBDExposedPoint
    from avic_core.graphics import GraphicsService

    app = create_ui_app(data_dir=str(tmp_path / "published-graphic-runtime"))
    client = TestClient(app)
    _, station = _workspace(client)
    site = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "Plant", "kind": "site",
    }).json()
    page = client.post("/api/web-pages", json={
        "station_id": station["id"], "name": "AHU", "kind": "page",
        "parent_id": site["id"], "slug": "ahu",
    }).json()

    point = FBDExposedPoint(name="Fan feedback", station_id=station["id"], value=True,
                            quality="GOOD", data_type="boolean")
    app.state.core.repository.save(point)
    graphics = GraphicsService(app.state.core)
    graphic = graphics.create(station["id"], "AHU fan")
    element_id = "7c56d5a0-02f5-4a5a-99e6-9a9a5a7d2099"
    saved_graphic = graphics.save(graphic["id"], graphic["revision"], [{
        "id": element_id, "name": "Вентилятор ПВ-1", "symbol_key": "fan",
        "x": 100, "y": 120, "width": 180, "height": 140,
        "bindings": [{"point_id": point.id, "role": "feedback", "binding_type": "status",
                      "target_property": "animation", "settings": {"converter": "boolean"}}],
    }])
    assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
        "expected_revision": page["revision"], "graphic_id": graphic["id"],
    }).json()
    saved_page = client.put(f"/api/web-pages/{page['id']}", json={
        "expected_revision": assigned["revision"],
        "layout": [{"type": "graphic", "graphic_id": graphic["id"],
                    "x": 20, "y": 20, "width": 800, "height": 500}],
    }).json()
    published = client.post(f"/api/web-pages/{page['id']}/publish", json={
        "expected_revision": saved_page["revision"],
    })
    assert published.status_code == 200, published.text

    page_response = client.get(f"/published/{station['id']}/ahu")
    assert page_response.status_code == 200
    assert f"/published-graphics/{station['id']}/{graphic['id']}?page_id={page['id']}" in page_response.text

    runtime = client.get(f"/published-graphics/{station['id']}/{graphic['id']}?page_id={page['id']}")
    assert runtime.status_code == 200, runtime.text
    assert "Вентилятор ПВ-1" in runtime.text
    assert f"/api/graphics/library/fan/svg" in runtime.text
    assert "data-bindings-url" in runtime.text

    live = client.get(f"/published-graphics/{station['id']}/{graphic['id']}/bindings?page_id={page['id']}")
    assert live.status_code == 200, live.text
    binding = next(iter(live.json()["bindings"].values()))
    assert binding["quality"] == "GOOD"
    assert binding["animation_allowed"] is True

    # Editing the source graphic after publication must not change the published view.
    changed = graphics.save(graphic["id"], saved_graphic["revision"], [{
        "id": element_id, "name": "ИЗМЕНЁННЫЙ ЭЛЕМЕНТ", "symbol_key": "sensor",
        "x": 400, "y": 400, "width": 80, "height": 60, "bindings": [],
    }])
    frozen = client.get(f"/published-graphics/{station['id']}/{graphic['id']}?page_id={page['id']}")
    assert frozen.status_code == 200
    assert "Вентилятор ПВ-1" in frozen.text
    assert "/api/graphics/library/fan/svg" in frozen.text
    assert "ИЗМЕНЁННЫЙ ЭЛЕМЕНТ" not in frozen.text
    app.state.core.close()
