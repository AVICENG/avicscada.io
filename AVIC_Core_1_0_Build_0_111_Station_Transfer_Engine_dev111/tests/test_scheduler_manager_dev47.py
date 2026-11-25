from datetime import datetime, timezone

import pytest

from avic_core.scheduling import ScheduleConflict, ScheduleError, ScheduleService


def make_service(tmp_path):
    return ScheduleService(tmp_path / "schedules.sqlite3")


def test_weekly_schedule_evaluates_value_and_source(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="station-1", name="HVAC occupied", value_type="BOOLEAN",
                          timezone_name="Europe/Moscow", default_value=False)
    svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=8 * 60,
                         end_minute=18 * 60, value=True, expected_revision=1)
    result = svc.evaluate(schedule["id"], now=datetime(2026, 11, 16, 9, 0, tzinfo=timezone.utc))
    assert result["value"] is True
    assert result["source"] == "WEEKLY_SCHEDULE"
    assert result["output_mode"] == "INTENT_ONLY_NO_FIELD_WRITE"


def test_special_event_overrides_weekly_by_priority(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Setpoint", value_type="NUMERIC",
                          timezone_name="UTC", default_value=18.0)
    svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=0,
                         end_minute=1440, value=21.0, expected_revision=1)
    svc.add_special_event(schedule["id"], name="Holiday", start_date="2026-11-16",
                          end_date="2026-11-16", priority=5, value=16.0, expected_revision=2)
    result = svc.evaluate(schedule["id"], now=datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc))
    assert result["value"] == 16.0
    assert result["source"] == "SPECIAL_EVENT"


def test_manual_override_has_highest_priority_and_expiry(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Mode", value_type="ENUM", default_value="OFF")
    svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=0,
                         end_minute=1440, value="AUTO", expected_revision=1)
    result = svc.set_override(schedule["id"], value="MANUAL", duration_seconds=3600,
                              actor_id="operator-1", reason="Commissioning test")
    assert result["value"] == "MANUAL"
    assert result["source"] == "MANUAL_OVERRIDE"
    svc.clear_override(schedule["id"])
    assert svc.evaluate(schedule["id"], now=datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc))["source"] == "WEEKLY_SCHEDULE"


def test_overlap_is_rejected_and_optimistic_revision_checked(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Fan", value_type="BOOLEAN", default_value=False)
    svc.add_weekly_event(schedule["id"], day_of_week=1, start_minute=480,
                         end_minute=600, value=True, expected_revision=1)
    with pytest.raises(ScheduleConflict):
        svc.add_weekly_event(schedule["id"], day_of_week=1, start_minute=590,
                             end_minute=660, value=False)
    with pytest.raises(ScheduleConflict, match="CONCURRENCY_CONFLICT"):
        svc.add_weekly_event(schedule["id"], day_of_week=2, start_minute=480,
                             end_minute=600, value=True, expected_revision=1)


def test_values_and_intervals_are_type_checked(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Numeric", value_type="NUMERIC", default_value=20)
    with pytest.raises(ScheduleError):
        svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=10,
                             end_minute=20, value=True)
    with pytest.raises(ScheduleError):
        svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=20,
                             end_minute=20, value=22)


def test_schedule_survives_service_restart(tmp_path):
    path = tmp_path / "schedules.sqlite3"
    first = ScheduleService(path)
    created = first.create(station_id="s", name="Persist", value_type="STRING", default_value="Closed")
    first.add_weekly_event(created["id"], day_of_week=4, start_minute=600,
                           end_minute=900, value="Open", expected_revision=1)
    second = ScheduleService(path)
    loaded = second.get(created["id"])
    assert loaded["name"] == "Persist"
    assert loaded["weekly_events"][0]["value"] == "Open"


def test_schedule_api_create_weekly_special_and_evaluate(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app

    client = TestClient(create_ui_app(data_dir=str(tmp_path / "api-data")))
    project = client.post("/api/projects", json={"name": "Schedule Project"}).json()
    station = client.post("/api/stations", json={"name": "AHU Station", "project_id": project["id"]}).json()
    created = client.post("/api/schedules", json={"station_id": station["id"], "name": "AHU Occupancy",
        "value_type": "BOOLEAN", "timezone": "Europe/Moscow", "default_value": False})
    assert created.status_code == 201, created.text
    schedule = created.json()
    weekly = client.post(f"/api/schedules/{schedule['id']}/weekly-events", json={
        "day_of_week": 0, "start_minute": 480, "end_minute": 1080, "value": True,
        "expected_revision": 1})
    assert weekly.status_code == 201, weekly.text
    special = client.post(f"/api/schedules/{schedule['id']}/special-events", json={
        "name": "Holiday", "start_date": "2026-11-16", "end_date": "2026-11-16",
        "priority": 5, "value": False, "expected_revision": 2})
    assert special.status_code == 201, special.text
    listing = client.get(f"/api/stations/{station['id']}/schedules")
    assert listing.status_code == 200 and len(listing.json()["schedules"]) == 1
    evaluation = client.get(f"/api/schedules/{schedule['id']}/evaluate")
    assert evaluation.status_code == 200
    assert evaluation.json()["output_mode"] == "INTENT_ONLY_NO_FIELD_WRITE"


def test_scheduler_is_rendered_inside_main_workbench(tmp_path):
    from avic_core.ui.app import create_ui_app
    from fastapi.testclient import TestClient

    client = TestClient(create_ui_app(data_dir=str(tmp_path / "ui-data")))
    html = client.get("/").text
    assert "SCHEDULER MANAGER" in html
    assert "schedule-add-weekly" in html
    assert "schedule-add-special" in html
    assert "schedulerLoad" in html


def test_next_change_returns_actual_resolved_value_and_source(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Occupied", value_type="BOOLEAN", default_value=False)
    svc.add_weekly_event(schedule["id"], day_of_week=0, start_minute=480,
                         end_minute=600, value=True, expected_revision=1)
    result = svc.evaluate(schedule["id"], now=datetime(2026, 11, 16, 9, 0, tzinfo=timezone.utc))
    assert result["value"] is True
    assert result["next_change"]["at"].startswith("2026-11-16T10:00:00")
    assert result["next_change"]["value"] is False
    assert result["next_change"]["source"] == "DEFAULT"


def test_same_priority_special_event_overlap_is_rejected(tmp_path):
    svc = make_service(tmp_path)
    schedule = svc.create(station_id="s", name="Holiday", value_type="BOOLEAN", default_value=False)
    svc.add_special_event(schedule["id"], name="Holiday A", start_date="2026-12-31",
                          end_date="2027-01-02", start_minute=0, end_minute=1440,
                          priority=5, value=True, expected_revision=1)
    with pytest.raises(ScheduleConflict, match="одного приоритета"):
        svc.add_special_event(schedule["id"], name="Holiday B", start_date="2027-01-01",
                              end_date="2027-01-03", start_minute=600, end_minute=700,
                              priority=5, value=False, expected_revision=2)


def test_point_binding_requires_output_compatible_point_on_same_station(tmp_path):
    from avic_core.application.container import CoreApplication
    from avic_core.domain.models import Device, Point, PointDirection
    from avic_core.ui.project_station import ProjectStationService

    core = CoreApplication(tmp_path / "binding-core")
    ps = ProjectStationService(core)
    project = ps.create_project("Binding Project")
    station = ps.create_station(project["id"], "Station")
    device = Device(name="AHU Controller", station_id=station["id"])
    output = Point(name="Fan Enable", device_id=device.id, data_type="bool", direction=PointDirection.OUTPUT)
    input_point = Point(name="Room Temperature", device_id=device.id, data_type="float", direction=PointDirection.INPUT)
    core.objects.save_graph([device, output, input_point])
    schedule = core.schedules.create(station_id=station["id"], name="Fan Schedule",
                                     value_type="BOOLEAN", default_value=False)
    options = core.schedules.list_bindable_points(station["id"], "BOOLEAN")
    assert [x["id"] for x in options] == [output.id]
    bound = core.schedules.bind_point(schedule["id"], output.id)
    assert bound["point_ids"] == [output.id]
    with pytest.raises(ScheduleError, match="выходной"):
        core.schedules.bind_point(schedule["id"], input_point.id)
    core.close()
