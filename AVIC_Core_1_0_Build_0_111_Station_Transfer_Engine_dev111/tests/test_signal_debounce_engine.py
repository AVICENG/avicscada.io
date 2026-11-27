from datetime import datetime, timedelta, timezone

import pytest

from avic_core.points.debounce import DebounceConfig, DebounceEngine


T0 = datetime(2026, 1, 1, tzinfo=timezone.utc)


def test_initial_value_is_accepted_without_startup_delay():
    engine = DebounceEngine()
    engine.configure("p", DebounceConfig(on_ms=500, off_ms=700))
    result = engine.ingest("p", False, timestamp=T0)
    assert result.accepted and result.value is False
    assert not result.pending


def test_short_on_pulse_is_cancelled_as_bounce():
    engine = DebounceEngine()
    engine.configure("p", DebounceConfig(on_ms=100, off_ms=100))
    engine.ingest("p", False, timestamp=T0)
    pending = engine.ingest("p", True, timestamp=T0 + timedelta(milliseconds=10))
    assert pending.pending and pending.value is False
    cancelled = engine.ingest("p", False, timestamp=T0 + timedelta(milliseconds=40))
    assert not cancelled.pending
    assert engine.stable_value("p") is False
    assert engine.flush_due(now=T0 + timedelta(seconds=1)) == ()


def test_on_transition_commits_at_deadline_without_followup_sample():
    engine = DebounceEngine()
    engine.configure("p", DebounceConfig(on_ms=100, off_ms=250))
    engine.ingest("p", False, timestamp=T0)
    pending = engine.ingest("p", True, timestamp=T0 + timedelta(milliseconds=10))
    assert pending.deadline == T0 + timedelta(milliseconds=110)
    assert engine.flush_due(now=T0 + timedelta(milliseconds=109)) == ()
    committed = engine.flush_due(now=T0 + timedelta(milliseconds=110))
    assert len(committed) == 1
    assert committed[0].accepted and committed[0].value is True


def test_on_and_off_have_independent_delays():
    engine = DebounceEngine()
    engine.configure("p", DebounceConfig(on_ms=100, off_ms=300))
    engine.ingest("p", False, timestamp=T0)
    engine.ingest("p", True, timestamp=T0 + timedelta(milliseconds=1))
    on = engine.flush_due(now=T0 + timedelta(milliseconds=101))
    assert on[0].value is True
    off_pending = engine.ingest("p", False, timestamp=T0 + timedelta(milliseconds=200))
    assert off_pending.pending
    assert off_pending.deadline == T0 + timedelta(milliseconds=500)
    assert engine.flush_due(now=T0 + timedelta(milliseconds=499)) == ()
    assert engine.flush_due(now=T0 + timedelta(milliseconds=500))[0].value is False


def test_quality_loss_can_cancel_pending_transition():
    engine = DebounceEngine()
    engine.configure("p", DebounceConfig(on_ms=100))
    engine.ingest("p", False, timestamp=T0)
    engine.ingest("p", True, timestamp=T0 + timedelta(milliseconds=1))
    assert engine.cancel_pending("p")
    assert engine.stable_value("p") is False
    assert engine.flush_due(now=T0 + timedelta(seconds=1)) == ()


def test_rejects_non_boolean_and_naive_or_old_timestamps():
    engine = DebounceEngine()
    with pytest.raises(TypeError):
        engine.ingest("p", 1, timestamp=T0)
    with pytest.raises(ValueError):
        engine.ingest("p", True, timestamp=datetime(2026, 1, 1))
    engine.ingest("p", False, timestamp=T0)
    with pytest.raises(ValueError):
        engine.ingest("p", True, timestamp=T0 - timedelta(milliseconds=1))


def test_config_validation_and_point_isolation():
    with pytest.raises(ValueError):
        DebounceConfig(on_ms=-1)
    engine = DebounceEngine()
    engine.configure("a", DebounceConfig(on_ms=100))
    engine.configure("b", DebounceConfig(on_ms=0))
    engine.ingest("a", False, timestamp=T0)
    engine.ingest("b", False, timestamp=T0)
    assert engine.ingest("a", True, timestamp=T0 + timedelta(milliseconds=1)).pending
    assert engine.ingest("b", True, timestamp=T0 + timedelta(milliseconds=1)).accepted
    assert engine.stable_value("a") is False
    assert engine.stable_value("b") is True
