import pytest

from avic_core.alarm import AlarmCategory, AlarmPriority, AlarmService, AlarmState
from avic_core.audit.service import AuditService


def test_alarm_lifecycle_ack_then_return_normal_and_history(tmp_path):
    audit = AuditService(tmp_path / "audit.db")
    published = []
    service = AlarmService(tmp_path / "alarms.db", audit_service=audit,
                           event_publisher=published.append)
    alarm = service.raise_alarm(
        station_id="station-a", source_id="boiler-1", alarm_key="high_temp",
        name="Высокая температура", message="Температура выше уставки",
        category=AlarmCategory.PROCESS, priority=AlarmPriority.CRITICAL,
        metadata={"value": 98.2, "unit": "C"},
    )
    assert alarm.state == AlarmState.ACTIVE
    assert service.active_count(station_id="station-a") == 1
    ack = service.acknowledge(alarm.alarm_id, actor_id="operator-7", comment="Проверяю")
    assert ack.state == AlarmState.ACKNOWLEDGED
    cleared = service.return_to_normal(alarm.alarm_id)
    assert cleared.state == AlarmState.NORMAL
    assert cleared.acknowledged_by == "operator-7"
    assert len(service.history(alarm_id=alarm.alarm_id)) == 3
    assert [e.event_type for e in published] == [
        "RAISED", "ACKNOWLEDGED", "RETURNED_TO_NORMAL"
    ]
    assert audit.verify_chain()[0]


def test_return_to_normal_before_ack_requires_ack_afterwards(tmp_path):
    service = AlarmService(tmp_path / "alarms.db")
    alarm = service.raise_alarm(station_id="s", source_id="p", alarm_key="k",
                                name="Alarm", message="Active")
    returned = service.return_to_normal(alarm.alarm_id)
    assert returned.state == AlarmState.RETURNED_TO_NORMAL
    assert service.active_count() == 0
    acknowledged = service.acknowledge(alarm.alarm_id, actor_id="dispatcher")
    assert acknowledged.state == AlarmState.NORMAL
    assert acknowledged.acknowledged_by == "dispatcher"


def test_duplicate_active_signal_does_not_create_new_occurrence(tmp_path):
    service = AlarmService(tmp_path / "alarms.db")
    kwargs = dict(station_id="s", source_id="device", alarm_key="offline",
                  name="Offline", message="Device offline")
    first = service.raise_alarm(**kwargs)
    again = service.raise_alarm(**{**kwargs, "message": "Still offline"})
    assert again.alarm_id == first.alarm_id
    assert again.occurrence_count == 1
    assert len(service.history(alarm_id=first.alarm_id)) == 1
    service.return_to_normal(first.alarm_id)
    second_occurrence = service.raise_alarm(**kwargs)
    assert second_occurrence.occurrence_count == 2
    assert second_occurrence.state == AlarmState.ACTIVE
    assert len(service.history(alarm_id=first.alarm_id)) == 3


def test_alarm_filters_sorting_and_station_isolation(tmp_path):
    service = AlarmService(tmp_path / "alarms.db")
    a = service.raise_alarm(station_id="A", source_id="p1", alarm_key="x",
                            name="Pump fault", message="Pump stopped",
                            priority=AlarmPriority.HIGH, category=AlarmCategory.EQUIPMENT)
    service.raise_alarm(station_id="B", source_id="p2", alarm_key="y",
                        name="Link down", message="No response",
                        priority=AlarmPriority.CRITICAL, category=AlarmCategory.COMMUNICATION)
    assert [x.alarm_id for x in service.list_alarms(station_id="A")] == [a.alarm_id]
    assert service.list_alarms(priorities=[1])[0].station_id == "B"
    assert service.list_alarms(search="Pump")[0].alarm_id == a.alarm_id
    assert service.list_alarms(categories=[AlarmCategory.COMMUNICATION])[0].station_id == "B"


def test_state_survives_restart_and_invalid_inputs_rejected(tmp_path):
    db = tmp_path / "alarms.db"
    service = AlarmService(db)
    alarm = service.raise_alarm(station_id="s", source_id="d", alarm_key="x",
                                name="Fault", message="Broken")
    restarted = AlarmService(db)
    assert restarted.get_alarm(alarm.alarm_id).state == AlarmState.ACTIVE
    with pytest.raises(ValueError):
        restarted.raise_alarm(station_id="s", source_id="d", alarm_key="bad",
                              name="Bad", message="Bad", priority=6)
    with pytest.raises(ValueError):
        restarted.list_alarms(limit=5000)
    with pytest.raises(KeyError):
        restarted.acknowledge("missing", actor_id="operator")


def test_publisher_failure_does_not_rollback_durable_alarm_event(tmp_path):
    def broken(_event):
        raise RuntimeError("consumer unavailable")
    service = AlarmService(tmp_path / "alarms.db", event_publisher=broken)
    alarm = service.raise_alarm(station_id="s", source_id="d", alarm_key="x",
                                name="Fault", message="Broken")
    assert alarm.state == AlarmState.ACTIVE
    assert len(service.history(alarm_id=alarm.alarm_id)) == 1
