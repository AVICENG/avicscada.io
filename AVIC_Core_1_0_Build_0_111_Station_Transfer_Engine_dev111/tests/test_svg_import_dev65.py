from fastapi.testclient import TestClient

from avic_core.graphics.custom_svg_library import SvgImportError, sanitize_svg
from avic_core.ui.app import create_ui_app

VALID_SVG = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<defs><linearGradient id="paint"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#2563b8"/></linearGradient></defs>
<circle cx="50" cy="50" r="38" fill="url(#paint)" stroke="#111111" stroke-width="3"/>
</svg>'''


def _station(client, name="SVG import"):
    project = client.post("/api/projects", json={"name": name}).json()
    return client.post("/api/stations", json={"name": "Station", "project_id": project["id"]}).json()


def test_svg_sanitizer_keeps_safe_vector_and_normalizes_namespace():
    cleaned, info = sanitize_svg(VALID_SVG)
    text = cleaned.decode("utf-8")
    assert '<svg xmlns="http://www.w3.org/2000/svg"' in text
    assert "linearGradient" in text and 'url(#paint)' in text
    assert info["nodes"] == "6"


def test_svg_sanitizer_rejects_script_events_external_refs_and_dtd():
    bad = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>alert(1)</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect onload="alert(1)" width="10" height="10"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><use href="https://evil.example/a.svg#x"/></svg>',
        '<!DOCTYPE svg [<!ENTITY x "boom">]><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><image href="file:///secret"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" xmlns:evil="https://evil.example/ns" viewBox="0 0 10 10"><rect evil:href="#x" width="10" height="10"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect style="background:url(https://evil.example/a)" width="10" height="10"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><use href="#missing"/></svg>',
    ]
    for source in bad:
        try:
            sanitize_svg(source)
            assert False, "unsafe SVG should be rejected"
        except SvgImportError:
            pass


def test_svg_import_is_station_scoped_persistent_and_usable_in_graphics(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    station = _station(client)
    other = _station(client, "Other project")
    before_import = app.state.core.audit.verify_chain()[1]
    response = client.post(f"/api/stations/{station['id']}/graphics/svg-assets", json={
        "name": "Imported gauge", "category": "Измерение", "filename": "gauge.svg", "svg": VALID_SVG,
    })
    assert response.status_code == 201, response.text
    assert app.state.core.audit.verify_chain()[1] == before_import + 1
    asset = response.json()
    listed = client.get(f"/api/stations/{station['id']}/graphics/svg-assets").json()["items"]
    assert [x["id"] for x in listed] == [asset["id"]]
    assert client.get(f"/api/stations/{other['id']}/graphics/svg-assets").json()["items"] == []
    served = client.get(asset["svg_url"])
    assert served.status_code == 200
    assert served.headers["content-type"].startswith("image/svg+xml")
    assert served.headers["x-content-type-options"] == "nosniff"

    graphic = client.post(f"/api/stations/{station['id']}/graphics", json={"name": "Custom graphic"}).json()
    saved = client.put(f"/api/graphics/{graphic['id']}", json={
        "expected_revision": graphic["revision"],
        "elements": [{"name": "My gauge", "symbol_key": asset["id"], "x": 20, "y": 20,
                      "width": 100, "height": 100, "bindings": []}],
    })
    assert saved.status_code == 200, saved.text
    reopened = client.get(f"/api/graphics/{graphic['id']}").json()
    assert reopened["elements"][0]["symbol_key"] == asset["id"]
    assert reopened["elements"][0]["symbol_name"] == "Imported gauge"
    assert client.delete(f"/api/stations/{station['id']}/graphics/svg-assets/{asset['id']}").status_code == 409
    # Windows-style input paths are reduced to a filename; no path is stored or served.
    second = client.post(f"/api/stations/{station['id']}/graphics/svg-assets", json={
        "name": "Imported second", "category": "Измерение", "filename": r"C:\temp\gauge2.svg", "svg": VALID_SVG,
    })
    assert second.status_code == 201 and second.json()["filename"] == "gauge2.svg"
    deleted = client.delete(f"/api/stations/{station['id']}/graphics/svg-assets/{second.json()['id']}")
    assert deleted.status_code == 200
    app.state.core.close()


def test_svg_import_rejects_invalid_payload_without_persisting(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    station = _station(client)
    response = client.post(f"/api/stations/{station['id']}/graphics/svg-assets", json={
        "name": "Unsafe", "category": "Custom", "filename": "unsafe.svg",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><script>x</script></svg>',
    })
    assert response.status_code == 400
    assert client.get(f"/api/stations/{station['id']}/graphics/svg-assets").json()["items"] == []
    app.state.core.close()


def test_graphics_symbol_catalog_and_current_repository_editor_routes(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    station = _station(client)
    imported = client.post(f"/api/stations/{station['id']}/graphics/svg-assets", json={
        "name": "Valve custom", "category": "Арматура", "filename": "valve.svg",
        "svg": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><path d="M1 1 L19 19" stroke="#111"/></svg>',
    }).json()
    catalog = client.get(f"/api/stations/{station['id']}/graphics/symbols").json()
    assert any(x["id"] == imported["id"] and x["custom"] for x in catalog["items"])

    # DEV99+ intentionally keeps /pages as a compatibility alias for Graphics Workbench.
    legacy_alias = client.get("/pages")
    assert legacy_alias.status_code == 200
    assert "Repository · Graphics Workbench" in legacy_alias.text
    assert 'id="symbolLibrary"' in legacy_alias.text

    # The active Web Application Page Builder is served by the Repository route,
    # not by the retired pages.html editor.
    page_builder = client.get(f"/repository?station={station['id']}&section=WebApplication")
    assert page_builder.status_code == 200
    for component in ("heading", "text", "card", "button", "image", "divider", "value", "graphic"):
        assert f'data-add="{component}"' in page_builder.text
    assert 'id="canvas"' in page_builder.text
    assert 'id="properties"' in page_builder.text
    assert 'id="publish"' in page_builder.text
    app.state.core.close()
