from datetime import datetime, timezone

import pytest

from avic_core.contracts import (
    ExecutionClass, FBDCategory, FBDPortDefinition, FBDType,
    GraphicsBinding, PluginManifest, SignalEnvelope, SignalQuality,
    SymbolManifest,
)


def test_signal_envelope_preserves_value_quality_time_and_source():
    stamp = datetime.now(timezone.utc)
    signal = SignalEnvelope(21.5, FBDType.FLOAT, SignalQuality.GOOD, stamp, "station-1/point-1", 3, "degC")
    assert signal.value == 21.5
    assert signal.quality is SignalQuality.GOOD
    assert signal.timestamp is stamp
    assert signal.source_ref == "station-1/point-1"
    assert signal.sequence == 3


def test_signal_envelope_rejects_naive_timestamp_and_wrong_type():
    with pytest.raises(ValueError):
        SignalEnvelope(1, FBDType.INT, SignalQuality.GOOD, datetime.now(), "point-1")
    with pytest.raises(TypeError):
        SignalEnvelope("yes", FBDType.BOOL, SignalQuality.GOOD, datetime.now(timezone.utc), "point-1")


def test_fbd_catalog_has_the_agreed_sixteen_categories():
    assert len(FBDCategory) == 16
    assert ExecutionClass.EVENT_DRIVEN.value == "EVENT_DRIVEN"
    port = FBDPortDefinition("in", "Enable", "input", FBDType.BOOL)
    assert port.required


def test_plugin_manifest_requires_versioned_identity():
    manifest = PluginManifest("vendor.modbus", "1.0.0", "1", "driver", frozenset({"read"}))
    assert manifest.capabilities == frozenset({"read"})
    with pytest.raises(ValueError):
        PluginManifest("", "1.0.0", "1", "driver")


def test_symbol_manifest_binds_to_existing_runtime_identity():
    binding = GraphicsBinding("station-1/point-1", "value")
    symbol = SymbolManifest("avic.pump.basic", "1.0.0", (0, 0, 100, 100), "Pumps", bindings=(binding,))
    assert symbol.bindings[0].runtime_ref == "station-1/point-1"
    with pytest.raises(ValueError):
        SymbolManifest("bad", "1", (0, 0, 0, 100), "Pumps")


def test_event_envelope_is_correlated_and_requires_aware_time():
    from avic_core.contracts import EventEnvelope

    event = EventEnvelope(
        "point.value_changed", "station-1/point-1", datetime.now(timezone.utc),
        {"value": 22.0}, correlation_id="trace-1", sequence=4,
    )
    assert event.event_id
    assert event.correlation_id == "trace-1"
    assert event.payload["value"] == 22.0
    with pytest.raises(ValueError):
        EventEnvelope("alarm.raised", "station-1", datetime.now(), {})


def test_command_request_is_only_a_validated_proposal():
    from avic_core.contracts import CommandRequest

    request = CommandRequest(
        "station-1/point-1", "set_value", "operator-1", datetime.now(timezone.utc),
        {"value": 1}, priority=80, idempotency_key="cmd-1", requires_confirmation=True,
    )
    assert request.requires_confirmation is True
    assert request.priority == 80
    with pytest.raises(ValueError):
        CommandRequest("point-1", "write", "operator-1", datetime.now(timezone.utc), priority=101)


def test_symbol_manifest_carries_engineering_passport_metadata():
    symbol = SymbolManifest(
        "avic.pump.detailed", "1.0.0", (0, 0, 120, 80), "Pumps",
        scale=1.25, properties_schema=("rotation", "color"),
        animations=("running", "fault"), locales=("ru", "en"),
        license_feature="graphics.symbols",
    )
    assert symbol.scale == 1.25
    assert symbol.animations == ("running", "fault")
    with pytest.raises(ValueError):
        SymbolManifest("bad", "1", (0, 0, 100, 100), "Pumps", scale=0)
