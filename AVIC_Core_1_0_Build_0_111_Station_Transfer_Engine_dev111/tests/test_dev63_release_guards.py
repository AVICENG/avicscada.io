from pathlib import Path

from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "avic_core" / "ui" / "static"


def test_all_workbench_entrypoints_load_and_share_dev67_theme(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    for route in ("/", "/pages", "/logic", "/graphics"):
        response = client.get(route)
        assert response.status_code == 200, route
        assert 'id="avic-theme-dev67"' in response.text, route
        assert "#111111" in response.text, route
        assert "#eef0f2" in response.text, route


def test_dev67_theme_contract_is_neutral_and_preserves_semantic_status_colors():
    for page in ("index.html", "pages.html", "logic.html", "graphics.html"):
        content = (STATIC / page).read_text(encoding="utf-8")
        theme = content.split('<style id="avic-theme-dev67">', 1)[1].split("</style>", 1)[0]
        assert "color:#111111!important" in theme
        assert "background:#eef0f2!important" in theme
        assert "#2563b8" in theme
        assert "#16803c" in theme  # semantic GOOD state remains green, not a green selection fill
        assert "#9a6700" in theme
        assert "#c62828" in theme


def test_critical_engineering_api_routes_remain_registered(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    route_methods = {
        (route.path, method)
        for route in app.routes
        for method in getattr(route, "methods", set())
    }
    required = {
        ("/api/ui/manifest", "GET"),
        ("/api/ui/health", "GET"),
        ("/api/platform/status", "GET"),
        ("/api/network/discovery-sessions", "GET"),
        ("/api/fbd/library", "GET"),
        ("/api/alarms", "GET"),
        ("/api/events", "GET"),
        ("/api/engineering/points", "GET"),
        ("/api/drivers/catalog", "GET"),
        ("/api/projects/tree", "GET"),
    }
    assert required <= route_methods
    assert len(route_methods) >= 100


def test_previous_core_packages_are_preserved():
    required = [
        "application/container.py",
        "network/bacnet_ip.py",
        "network/modbus_tcp.py",
        "network/discovery_history.py",
        "drivers/manager.py",
        "graphics/service.py",
        "logic_fbd.py",
        "scheduling/service.py",
        "alarm/service.py",
        "history/service.py",
        "security/gateway.py",
        "config/project_backup.py",
        "engineering/workflow.py",
        "ui/app.py",
    ]
    for relative in required:
        assert (ROOT / "avic_core" / relative).is_file(), relative


def test_dev67_version_is_reported_consistently(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    manifest = client.get("/api/ui/manifest")
    assert manifest.status_code == 200
    assert manifest.json()["version"] == "1.0.0.dev196"
    status = client.get("/api/platform/status")
    assert status.status_code == 200
    assert status.json()["version"] == "1.0.0.dev196"


def test_all_internal_editor_links_resolve_to_live_workbench_routes(tmp_path):
    from html.parser import HTMLParser
    from urllib.parse import urlsplit

    class LinkParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.hrefs = []

        def handle_starttag(self, tag, attrs):
            if tag == "a":
                href = dict(attrs).get("href")
                if href:
                    self.hrefs.append(href)

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    for page in ("index.html", "pages.html", "logic.html", "graphics.html"):
        parser = LinkParser()
        parser.feed((STATIC / page).read_text(encoding="utf-8"))
        for href in parser.hrefs:
            parsed = urlsplit(href)
            if parsed.scheme or parsed.netloc or href.startswith("#"):
                continue
            response = client.get(href)
            assert response.status_code == 200, (page, href, response.status_code)


def test_every_registered_get_api_path_fails_closed_without_server_error(tmp_path):
    import re

    app = create_ui_app(data_dir=str(tmp_path))
    client = TestClient(app, raise_server_exceptions=False)
    get_routes = [
        route for route in app.routes
        if getattr(route, "path", "").startswith("/api/")
        and "GET" in getattr(route, "methods", set())
    ]
    assert len(get_routes) >= 45
    probe_id = "00000000-0000-4000-8000-000000000001"
    for route in get_routes:
        path = re.sub(r"\{[^}]+\}", probe_id, route.path)
        response = client.get(path)
        assert response.status_code < 500, (route.path, response.status_code, response.text[:240])


def test_malformed_web_page_id_returns_client_error_not_server_error(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)), raise_server_exceptions=False)
    response = client.get("/api/web-pages/not-a-uuid")
    assert response.status_code == 400


def test_every_registered_mutation_api_rejects_probe_without_server_error(tmp_path):
    import re

    app = create_ui_app(data_dir=str(tmp_path))
    client = TestClient(app, raise_server_exceptions=False)
    probe_id = "00000000-0000-4000-8000-000000000001"
    mutation_count = 0
    for route in app.routes:
        if not getattr(route, "path", "").startswith("/api/"):
            continue
        methods = getattr(route, "methods", set()) - {"GET", "HEAD", "OPTIONS"}
        for method in methods:
            mutation_count += 1
            path = re.sub(r"\{[^}]+\}", probe_id, route.path)
            response = client.request(method, path, json={})
            assert response.status_code < 500, (method, route.path, response.status_code, response.text[:240])
    assert mutation_count >= 45
