"""Acceptance tests for IQVISION User Manual §6 Alarm Console/History/Portal notes."""
from itertools import product
import pytest
from avic_core.alarm import AlarmService, AlarmState

@pytest.mark.parametrize("actor,note", product([f"operator-{i}" for i in range(12)], [f"Запись смены {j}" for j in range(20)]))
def test_alarm_notes_are_persistent_ordered_and_auditable(tmp_path, actor, note):
    service=AlarmService(tmp_path/"alarms.db")
    alarm=service.raise_alarm(station_id="station-a",source_id="boiler",alarm_key="high-temp",name="Высокая температура",message="Порог превышен")
    saved=service.add_note(alarm.alarm_id,actor_id=actor,note=note)
    reopened=AlarmService(tmp_path/"alarms.db")
    rows=reopened.list_notes(alarm.alarm_id)
    assert rows[0]["note_id"]==saved["note_id"]
    assert rows[0]["actor_id"]==actor and rows[0]["note"]==note
    assert rows[0]["station_id"]=="station-a"

@pytest.mark.parametrize("actor,note", [("", "x"), ("op", ""), ("op", " "), ("op", "x"*4001)])
def test_alarm_notes_reject_invalid_actor_or_note(tmp_path, actor, note):
    service=AlarmService(tmp_path/"alarms.db")
    alarm=service.raise_alarm(station_id="s",source_id="p",alarm_key="k",name="A",message="M")
    with pytest.raises(ValueError): service.add_note(alarm.alarm_id,actor_id=actor,note=note)

def test_alarm_notes_reject_unknown_alarm(tmp_path):
    service=AlarmService(tmp_path/"alarms.db")
    with pytest.raises(KeyError): service.add_note("missing",actor_id="operator",note="test")

@pytest.mark.parametrize("state,expected", [(AlarmState.ACTIVE,AlarmState.ACKNOWLEDGED),(AlarmState.RETURNED_TO_NORMAL,AlarmState.NORMAL)])
def test_console_acknowledge_transitions_match_operator_workflow(tmp_path,state,expected):
    service=AlarmService(tmp_path/"alarms.db")
    alarm=service.raise_alarm(station_id="s",source_id="p",alarm_key="k",name="A",message="M")
    if state==AlarmState.RETURNED_TO_NORMAL: service.return_to_normal(alarm.alarm_id)
    assert service.acknowledge(alarm.alarm_id,actor_id="operator").state==expected
