from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app
from avic_core.events import EventService
from avic_core.history import HistoryService
from avic_core.dependencies import DependencyService
from avic_core.analytics import AnalyticsService


def test_event_service_persists_filters_and_orders(tmp_path):
    service = EventService(tmp_path / "events.sqlite3")
    first = service.record("device.connected", "Device online", station_id="s1", severity="INFO")
    service.record("device.timeout", "No response", station_id="s1", severity="WARNING")
    rows = service.list(station_id="s1", severity="WARNING")
    assert len(rows) == 1
    assert rows[0].message == "No response"
    assert first.event_id


def test_history_service_quality_filter_and_rollup(tmp_path):
    service = HistoryService(tmp_path / "history.sqlite3")
    service.append("s1", "p1", 20.0, quality="GOOD")
    service.append("s1", "p1", 100.0, quality="BAD")
    service.append("s1", "p1", 22.0, quality="GOOD")
    assert len(service.query("s1", "p1", include_bad=False)) == 2
    result = service.rollup("s1", "p1", method="average")
    assert result["value"] == 21.0
    assert result["valid_numeric_count"] == 2


def test_dependency_delete_preview_blocks_referenced_object(tmp_path):
    service = DependencyService(tmp_path / "deps.sqlite3")
    service.add("graphic-1", "point-1", "binding", station_id="s1")
    preview = service.delete_preview("point-1")
    assert preview["safe_to_delete"] is False
    assert preview["blocking_dependents"][0]["object_id"] == "graphic-1"


def test_analytics_tag_search_and_missing_data_strategies(tmp_path):
    service = AnalyticsService(tmp_path / "analytics.sqlite3")
    service.tag_point("p1", "meter", hierarchy_path="Site/A/Building/1")
    service.tag_point("p2", "meter", hierarchy_path="Site/A/Building/2")
    assert service.find_points("meter", hierarchy_prefix="Site/A/Building/1") == ["p1"]
    assert service.aggregate([2, None, 4], "average", missing_strategy="linear_interpolation")["value"] == 3.0
    assert service.aggregate([2, None, 4], "sum", missing_strategy="ignore_series")["value"] is None


def test_dev49_platform_service_apis_are_persistent_and_separate(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    catalog = client.get("/api/platform/catalog").json()
    assert catalog["total"] >= 35
    assert any(x["id"] == "scheduler" for x in catalog["modules"])
    assert any(x["id"] == "signature" for x in catalog["modules"])

    event = client.post("/api/events", json={"event_type": "operator.note", "message": "Test event", "severity": "NOTICE"})
    assert event.status_code == 201
    assert client.get("/api/events?severity=NOTICE").json()["events"][0]["message"] == "Test event"

    from avic_core.domain.models import Device, Point, PointQuality
    project = client.post("/api/projects", json={"name": "History API validation"}).json()
    station = client.post("/api/stations", json={
        "project_id": project["id"], "name": "History station",
    }).json()
    device = Device(name="History device", station_id=station["id"],
                    protocol="manual", address="manual://history")
    client.app.state.core.repository.save(device)
    point = Point(name="History point", device_id=device.id, data_type="analog-input",
                  value=None, quality=PointQuality.UNCERTAIN, native_identity="history:test")
    client.app.state.core.repository.save(point)
    sample = client.post("/api/history/samples", json={
        "station_id": station["id"], "point_id": point.id, "value": 23.5, "quality": "GOOD"})
    assert sample.status_code == 201, sample.text
    assert len(client.get(f"/api/stations/{station['id']}/points/{point.id}/history").json()["samples"]) == 1

    dep = client.post("/api/dependencies", json={"dependent_id": "graphic-1", "dependency_id": "p1", "relation_type": "binding"})
    assert dep.status_code == 201
    assert client.get("/api/engineering/objects/p1/cleanup-preview").json()["safe_to_delete"] is False

    route = client.post("/api/notifications/routes", json={"name": "Duty engineer", "channel": "EMAIL", "recipient": "ops@example.invalid"})
    assert route.status_code == 201
    assert client.get("/api/notifications/routes").json()["routes"][0]["name"] == "Duty engineer"

    time_cfg = client.put("/api/stations/s1/time", json={"timezone": "Europe/Moscow", "ntp_enabled": False, "ntp_servers": []})
    assert time_cfg.status_code == 200
    assert client.get("/api/stations/s1/time").json()["timezone"] == "Europe/Moscow"


def test_alarm_console_api_acknowledgement_and_event_journal(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    created = client.post("/api/alarms", json={
        "station_id": "station-1", "source_id": "point-1", "alarm_key": "high-temp",
        "name": "High temperature", "message": "Supply temperature exceeds limit", "priority": 2,
        "category": "PROCESS",
    })
    assert created.status_code == 201
    alarm_id = created.json()["alarm_id"]
    assert created.json()["state"] == "ACTIVE"
    ack = client.post(f"/api/alarms/{alarm_id}/acknowledge", json={"actor_id": "operator-1", "comment": "Investigating"})
    assert ack.status_code == 200 and ack.json()["state"] == "ACKNOWLEDGED"
    normal = client.post(f"/api/alarms/{alarm_id}/return-to-normal", json={"message": "Temperature normal"})
    assert normal.status_code == 200 and normal.json()["state"] == "NORMAL"
    assert len(client.get("/api/alarm-history?station_id=station-1").json()["events"]) == 3
    assert any(e["event_type"].startswith("alarm.") for e in client.get("/api/events?station_id=station-1").json()["events"])


def test_time_management_persists_station_policy_and_device_permission(tmp_path):
    from avic_core.time_management import TimeManagementService
    path = tmp_path / "time.sqlite3"
    first = TimeManagementService(path)
    first.configure_station("s1", "Europe/Moscow", ntp_enabled=True, ntp_servers=["10.0.0.1"])
    first.set_device_sync_permission("s1", "d1", True, approved_by="admin", reason="Commissioning approved")
    second = TimeManagementService(path)
    assert second.station_time("s1")["timezone"] == "Europe/Moscow"
    assert second.authorize_sync("s1", "d1") is True


def test_notification_outbox_rejects_missing_or_disabled_route(tmp_path):
    service = __import__("avic_core.notifications", fromlist=["NotificationService"]).NotificationService(tmp_path / "notifications.sqlite3")
    import pytest
    with pytest.raises(ValueError, match="does not exist"):
        service.enqueue({"text": "x"}, route_id="missing")
    route = service.add_route("Disabled", "EMAIL", "ops@example.invalid", enabled=False)
    with pytest.raises(ValueError, match="disabled"):
        service.enqueue({"text": "x"}, route_id=route["route_id"])


def test_point_manager_endpoint_returns_catalog_shape(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/api/engineering/points")
    assert response.status_code == 200
    assert response.json() == {"points": [], "total": 0, "offset": 0, "limit": 1000, "sort_by": "name", "sort_dir": "asc", "favorite_count": 0}
