from avic_core.scheduling import ScheduleService


class FakeRepository:
    def __init__(self):
        self.rows = {
            "point-1": {"entity_type": "Point", "payload": {
                "direction": "output", "data_type": "float", "device_id": "device-1"
            }},
            "device-1": {"entity_type": "Device", "payload": {"station_id": "station-1"}},
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


def make_schedule(tmp_path, usage):
    return ScheduleService(
        tmp_path / "schedules.sqlite3",
        repository=FakeRepository(),
        point_usage_service=usage,
    )


def test_scheduler_binding_activates_and_releases_point_license_reference(tmp_path):
    usage = UsageRecorder()
    scheduler = make_schedule(tmp_path, usage)
    schedule = scheduler.create(
        station_id="station-1", name="ПВ-1", value_type="NUMERIC", default_value=0
    )

    scheduler.bind_point(schedule["id"], "point-1")
    assert usage.calls == [(f"schedule:{schedule['id']}", ["point-1"])]
    assert scheduler.get(schedule["id"])["point_ids"] == ["point-1"]

    scheduler.unbind_point(schedule["id"], "point-1")
    assert usage.calls[-1] == (f"schedule:{schedule['id']}", [])
    assert scheduler.get(schedule["id"])["point_ids"] == []


def test_scheduler_license_denial_does_not_persist_binding(tmp_path):
    usage = UsageRecorder(fail=True)
    scheduler = make_schedule(tmp_path, usage)
    schedule = scheduler.create(
        station_id="station-1", name="ПВ-1", value_type="NUMERIC", default_value=0
    )

    try:
        scheduler.bind_point(schedule["id"], "point-1")
    except PermissionError as exc:
        assert "capacity exhausted" in str(exc)
    else:
        raise AssertionError("Expected the license gate to reject the binding")

    assert scheduler.get(schedule["id"])["point_ids"] == []
