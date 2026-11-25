import pytest

from avic_core.alarm import AlarmDefinitionManager, AlarmService, AlarmState


def test_definition_on_off_delay_and_hysteresis(tmp_path):
    alarms = AlarmService(tmp_path / "alarms.db")
    defs = AlarmDefinitionManager(tmp_path / "rules.db", alarms)
    d = defs.create(station_id="s", source_id="ahu", alarm_key="high_temp",
                    name="High temperature", message="Above limit", setpoint=30,
                    hysteresis=2, on_delay=5, off_delay=3)
    assert defs.evaluate(d.definition_id, 31, now=100) is None
    assert defs.evaluate(d.definition_id, 32, now=104) is None
    raised = defs.evaluate(d.definition_id, 33, now=105)
    assert raised.state == AlarmState.ACTIVE
    assert defs.evaluate(d.definition_id, 29, now=106).state == AlarmState.ACTIVE  # inside deadband
    assert defs.evaluate(d.definition_id, 27, now=107) is None
    cleared = defs.evaluate(d.definition_id, 27, now=110)
    assert cleared.state == AlarmState.RETURNED_TO_NORMAL


def test_bad_quality_does_not_trigger_or_clear_alarm(tmp_path):
    alarms = AlarmService(tmp_path / "alarms.db")
    defs = AlarmDefinitionManager(tmp_path / "rules.db", alarms)
    d = defs.create(station_id="s", source_id="p", alarm_key="x", name="X",
                    message="X high", setpoint=10)
    assert defs.evaluate(d.definition_id, 100, quality="Bad", now=10) is None
    assert alarms.active_count() == 0


def test_shelving_and_suppression_do_not_lose_condition_transition(tmp_path):
    alarms = AlarmService(tmp_path / "alarms.db")
    defs = AlarmDefinitionManager(tmp_path / "rules.db", alarms)
    d = defs.create(station_id="s", source_id="p", alarm_key="x", name="X",
                    message="X high", setpoint=10)
    import time
    start = time.time()
    defs.set_shelved(d.definition_id, duration_seconds=60)
    assert defs.evaluate(d.definition_id, 11, now=start + 1) is None
    assert defs.evaluate(d.definition_id, 11, now=start + 61).state == AlarmState.ACTIVE
    defs.set_suppressed(d.definition_id, True)
    assert defs.evaluate(d.definition_id, 0, now=start + 62) is None
    assert defs.evaluate(d.definition_id, 0, now=start + 63).state == AlarmState.RETURNED_TO_NORMAL


def test_latching_requires_operator_ack_after_condition_normal(tmp_path):
    alarms = AlarmService(tmp_path / "alarms.db")
    defs = AlarmDefinitionManager(tmp_path / "rules.db", alarms)
    d = defs.create(station_id="s", source_id="p", alarm_key="x", name="X",
                    message="X high", setpoint=10, latching=True)
    defs.evaluate(d.definition_id, 11, now=100)
    raised = defs.evaluate(d.definition_id, 11, now=101)
    assert raised.state == AlarmState.ACTIVE
    assert defs.evaluate(d.definition_id, 0, now=102) is None
    still_latched = defs.evaluate(d.definition_id, 0, now=103)
    assert still_latched.state == AlarmState.ACTIVE
    cleared = defs.acknowledge(d.definition_id, actor_id="operator")
    assert cleared.state == AlarmState.NORMAL


def test_outbox_retries_and_recovers_after_restart(tmp_path):
    db = tmp_path / "alarms.db"
    calls = []
    def broken(event):
        calls.append(event.event_id)
        raise RuntimeError("temporary bus outage")
    service = AlarmService(db, event_publisher=broken)
    service.raise_alarm(station_id="s", source_id="p", alarm_key="x", name="X", message="X")
    assert service.outbox_pending_count() == 1
    good_calls = []
    restarted = AlarmService(db, event_publisher=good_calls.append)
    result = restarted.dispatch_outbox(force=True)
    assert result["delivered"] == 1
    assert result["pending"] == 0
    assert len(good_calls) == 1


def test_definition_validation_rejects_negative_hysteresis(tmp_path):
    defs = AlarmDefinitionManager(tmp_path / "rules.db", AlarmService(tmp_path / "alarms.db"))
    with pytest.raises(ValueError):
        defs.create(station_id="s", source_id="p", alarm_key="x", name="X",
                    message="X", hysteresis=-1)
