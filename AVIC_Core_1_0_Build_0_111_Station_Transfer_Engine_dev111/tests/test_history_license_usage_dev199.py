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
    history.configure_point("station-1", "point-2", enabled=False) if False else None
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
