from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def test_workbench_home_is_served(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/")
    assert response.status_code == 200
    assert "AVIC" in response.text
    assert "Нижний инспектор" in response.text
    assert "inspectorDock" in response.text
    assert "data-inspector-tab=\"properties\"" in response.text
    assert "data-row-menu" in response.text
    assert "addEventListener(\'dblclick\'" in response.text
    assert 'id="rightPane"' not in response.text
    assert "commandSearch" in response.text
    assert "wizardModal" in response.text
    assert "data-action=\"bacnet-discover\"" in response.text
    assert "data-action=\"modbus-read\"" in response.text
    assert "scrollWidth>name.clientWidth" in response.text
    assert "station-children" in response.text
    assert "data-menu-action=\"web-pages\"" in response.text
    assert "{capture:true}" in response.text
    assert "FBD-проекты" in response.text
    assert "data-fbd-action" in response.text
    assert "data-fbd-new" in response.text


def test_manifest_contains_complete_product_navigation_and_roles(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    data = client.get("/api/ui/manifest").json()
    ids = {item["id"] for item in data["workspaces"]}
    assert data["workspace_count"] == 49
    assert {"projects", "stations", "equipment", "documents", "network", "devices", "points", "drivers", "graphics", "web-pages", "logic", "simulation", "alarms", "events", "history", "analytics", "notifications", "cleanup", "signature", "trends", "commissioning", "service", "supervisor", "sites", "mobile", "ai", "security", "audit", "backup", "licensing", "learning"} <= ids
    assert "Главный инженер" in data["roles"]
    assert "Пусконаладчик" in data["roles"]
    assert "Сервисный инженер" in data["roles"]
    assert data["capabilities"]["command_palette"] is True
    assert data["capabilities"]["guided_onboarding_preview"] is True


def test_workbench_keeps_field_execution_and_discovery_disabled(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    data = client.get("/api/ui/manifest").json()
    health = client.get("/api/ui/health").json()
    assert data["execution_enabled"] is False
    assert data["network_discovery_enabled"] is False
    assert data["capabilities"]["bacnet_ip_discovery"] == "explicit-read-only-manual-trigger"
    assert data["capabilities"]["modbus_tcp_read"] == "explicit-read-only"
    assert data["field_commands_enabled"] is False
    assert data["capabilities"]["project_station_persistence"] is True
    assert data["capabilities"]["server_rbac_integration"] is False
    assert health["status"] == "ok"
    assert health["mode"] == "safe-workbench-project-station"


def test_manifest_distinguishes_implemented_designed_and_planned(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    data = client.get("/api/ui/manifest").json()
    statuses = {item["status"] for item in data["workspaces"]}
    assert statuses == {"implemented", "designed", "planned", "partial", "interface"}
    assert next(x for x in data["workspaces"] if x["id"] == "dashboard")["status"] == "implemented"
