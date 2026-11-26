from avic_core.history import HistoryService


class FakeRepository:
    def __init__(self):
        self.rows = {
            "point-1": {"entity_type": "Point", "payload": {"device_id": "device-1"}},
            "device-1": {"entity_type": "Device", "payload": {"station_id": "station-1"}},
            "point-2": {"entity_type": "Point", "payload": {"device_id": "device-2"}},
            "device-2": {"entity_type": "Device", "payload": {"station_id": "station-2"}},
        }

    def get_record(self, entity_id):
        if entity_id not in self.rows:
            raise KeyError(entity_id)
        return self.rows[entity_id]


class UsageRecorder:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def set_point_usage(self, source_key, point_ids):
        self.calls.append((source_key, sorted(point_ids)))
        if self.fail and point_ids:
            raise PermissionError("license capacity exhausted")


def make_history(tmp_path, usage):
    return HistoryService(tmp_path / "history.sqlite3", repository=FakeRepository(),
                          point_usage_service=usage)


def test_history_configuration_activates_unique_points_and_releases_on_disable(tmp_path):
    usage = UsageRecorder()
    history = make_history(tmp_path, usage)
    history.configure_point("station-1", "point-1", enabled=True)
    history.configure_point("station-1", "point-1", enabled=True)
    assert history.configured_points("station-1") == ["point-1"]
    assert usage.calls == [("history:station-1", ["point-1"]),
                           ("history:station-1", ["point-1"])]

    result = history.configure_point("station-1", "point-1", enabled=False)
    assert result["configured_point_ids"] == []
    assert usage.calls[-1] == ("history:station-1", [])


def test_history_license_denial_does_not_create_binding(tmp_path):
    usage = UsageRecorder(fail=True)
    history = make_history(tmp_path, usage)
    try:
        history.configure_point("station-1", "point-1", enabled=True)
    except PermissionError as exc:
        assert "capacity exhausted" in str(exc)
    else:
        raise AssertionError("Expected license capacity rejection")
    assert history.configured_points("station-1") == []


def test_history_rejects_point_from_another_station(tmp_path):
    history = make_history(tmp_path, UsageRecorder())
    try:
        history.configure_point("station-1", "point-2", enabled=True)
    except ValueError as exc:
        assert "другой станции" in str(exc)
    else:
        raise AssertionError("Cross-station history binding must be rejected")


def test_history_startup_reconciliation_restores_missing_core_usage(tmp_path):
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from avic_core.domain.service import CoreObjectService
    from avic_core.repository import SQLiteRepository

    repo = SQLiteRepository(tmp_path / "objects.sqlite3")
    objects = CoreObjectService(repo)
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    point = Point("Flow", device_id=device.id, licensed_active=False)
    objects.save_graph([platform, project, station, device, point])

    history = HistoryService(tmp_path / "history.sqlite3", repository=repo,
                             point_usage_service=objects)
    history.configure_point(station.id, point.id)
    # Simulate a crash/partial cross-database update that lost the Core usage row.
    objects.set_point_usage(f"history:{station.id}", [])
    result = history.reconcile_point_usage()

    stored = repo.get_record(point.id)["payload"]
    assert result["reconciled"] == 1
    assert stored["licensed_usage"] == [f"history:{station.id}"]
    assert stored["licensed_active"] is True


def test_history_startup_reconciliation_releases_orphaned_usage(tmp_path):
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from avic_core.domain.service import CoreObjectService
    from avic_core.repository import SQLiteRepository

    repo = SQLiteRepository(tmp_path / "objects.sqlite3")
    objects = CoreObjectService(repo)
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    point = Point("Flow", device_id=device.id, licensed_active=False)
    objects.save_graph([platform, project, station, device, point])
    objects.set_point_usage(f"history:{station.id}", [point.id])

    history = HistoryService(tmp_path / "history.sqlite3", repository=repo,
                             point_usage_service=objects)
    result = history.reconcile_point_usage()

    stored = repo.get_record(point.id)["payload"]
    assert result["reconciled"] == 1
    assert stored["licensed_usage"] == []
    assert stored["licensed_active"] is False


def test_history_startup_reconciliation_removes_cross_station_stale_binding(tmp_path):
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from avic_core.domain.service import CoreObjectService
    from avic_core.repository import SQLiteRepository

    repo = SQLiteRepository(tmp_path / "objects.sqlite3")
    objects = CoreObjectService(repo)
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station_a = Station("Station A", project_id=project.id)
    station_b = Station("Station B", project_id=project.id)
    device = Device("Device", station_id=station_b.id)
    point = Point("Flow", device_id=device.id, licensed_active=False)
    objects.save_graph([platform, project, station_a, station_b, device, point])

    history = HistoryService(tmp_path / "history.sqlite3", repository=repo,
                             point_usage_service=objects)
    with history._db() as db:
        db.execute("INSERT INTO history_bindings VALUES(?,?,?)",
                   (station_a.id, point.id, "2026-01-01T00:00:00+00:00"))

    result = history.reconcile_point_usage()
    assert result["removed_invalid_bindings"] == [
        {"station_id": station_a.id, "point_id": point.id}
    ]
    assert history.configured_points(station_a.id) == []
