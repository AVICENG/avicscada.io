import pytest
from avic_core.scheduling import ScheduleConflict, ScheduleError, ScheduleService


def test_copy_weekly_day_replaces_targets_atomically_and_bumps_revision(tmp_path):
    svc = ScheduleService(tmp_path / "schedules.sqlite3")
    s = svc.create(station_id="s", name="Week", value_type="BOOLEAN", default_value=False)
    svc.add_weekly_event(s["id"], day_of_week=0, start_minute=480, end_minute=720, value=True, expected_revision=1)
    svc.add_weekly_event(s["id"], day_of_week=1, start_minute=900, end_minute=1020, value=True, expected_revision=2)
    copied = svc.copy_weekly_day(s["id"], source_day=0, target_days=[1, 2, 3, 4], expected_revision=3)
    assert copied["revision"] == 4
    by_day = {d: [e for e in copied["weekly_events"] if e["day_of_week"] == d] for d in range(7)}
    assert [(e["start_minute"], e["end_minute"], e["value"]) for e in by_day[0]] == [(480, 720, True)]
    assert all([(e["start_minute"], e["end_minute"], e["value"]) for e in by_day[d]] == [(480, 720, True)] for d in [1, 2, 3, 4])
    assert by_day[5] == [] and by_day[6] == []


def test_copy_weekly_day_checks_revision_and_days(tmp_path):
    svc = ScheduleService(tmp_path / "schedules.sqlite3")
    s = svc.create(station_id="s", name="Week", value_type="NUMERIC", default_value=18)
    with pytest.raises(ScheduleConflict, match="CONCURRENCY_CONFLICT"):
        svc.copy_weekly_day(s["id"], source_day=0, target_days=[1], expected_revision=9)
    for source, targets in [(True, [1]), (0, []), (0, [0]), (0, [1, 1]), (0, [7])]:
        with pytest.raises(ScheduleError):
            svc.copy_weekly_day(s["id"], source_day=source, target_days=targets)


def test_copy_weekly_day_api_and_audit(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    client = TestClient(create_ui_app(data_dir=str(tmp_path / "api")))
    project = client.post("/api/projects", json={"name": "P"}).json()
    station = client.post("/api/stations", json={"name": "S", "project_id": project["id"]}).json()
    s = client.post("/api/schedules", json={"station_id": station["id"], "name": "AHU", "value_type": "BOOLEAN", "default_value": False}).json()
    client.post(f"/api/schedules/{s['id']}/weekly-events", json={"day_of_week": 0, "start_minute": 420, "end_minute": 1080, "value": True, "expected_revision": 1})
    response = client.post(f"/api/schedules/{s['id']}/weekly-days/copy", json={"source_day": 0, "target_days": [1, 2, 3, 4], "expected_revision": 2})
    assert response.status_code == 200, response.text
    assert len(response.json()["weekly_events"]) == 5
    assert client.get("/").status_code == 200


def test_scheduler_workbench_exposes_week_grid_and_bulk_day_actions(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    client = TestClient(create_ui_app(data_dir=str(tmp_path / "ui")))
    html = client.get("/").text
    assert "Недельное расписание · 24 часа" in html
    assert "schedule-copy-weekdays" in html
    assert "schedule-copy-week" in html
    assert "weekly-days/copy" in html
