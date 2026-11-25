import struct

import pytest

from avic_core.drivers.knx_adapter import KnxPointAdapter, KnxPointBinding
from avic_core.network.knx_cemi import parse_cemi_frame
from avic_core.network.knxnet_ip import KnxProtocolError


class FakeRuntime:
    def __init__(self):
        self.published = []
        self.qualities = []
    def publish(self, point_id, value, *, quality, source_driver_id):
        sample = type("Sample", (), {"value": value, "quality": "GOOD"})()
        self.published.append((point_id, value, source_driver_id))
        return sample
    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.qualities.append((point_id, quality, source_driver_id))
        sample = type("Sample", (), {"value": 12.3, "quality": quality.value})()
        return sample


class FakeSession:
    def __init__(self, frames=(), fail_connect=False):
        self.frames = list(frames)
        self.fail_connect = fail_connect
        self.connected = False
        self.closed = False
    def connect(self):
        if self.fail_connect:
            raise OSError("simulated gateway down")
        self.connected = True
    def poll_cemi(self):
        return self.frames.pop(0) if self.frames else None
    def disconnect(self):
        self.connected = False
        self.closed = True
    def diagnostics(self):
        return {"state": "CONNECTED" if self.connected else "DISCONNECTED"}


def cemi(tpdu, group=0x0801, source=0x1101, code=0x29):
    return bytes((code, 0, 0xBC, 0xE0, source >> 8, source & 255,
                  group >> 8, group & 255, len(tpdu)-1)) + tpdu


def test_knx_adapter_publishes_short_boolean_into_shared_point_runtime():
    runtime = FakeRuntime()
    session = FakeSession([cemi(bytes((0x00, 0x81)))])
    adapter = KnxPointAdapter(session, runtime, "driver-1", [
        KnxPointBinding("point-1", "1/0/1", "DPT-1.001"),
    ])
    result = adapter.poll_once()
    assert result["results"][0]["ok"] is True
    assert runtime.published == [("point-1", True, "driver-1")]


def test_knx_adapter_decodes_dpt9_and_ignores_unmapped_groups():
    runtime = FakeRuntime()
    session = FakeSession([
        cemi(bytes((0x00, 0x40, 0x0C, 0x1A)), group=0x0802),
        cemi(bytes((0x00, 0x40, 0x0C, 0x1A)), group=0x0801),
    ])
    adapter = KnxPointAdapter(session, runtime, "driver-1", [
        KnxPointBinding("point-1", "1/0/1", "9.001"),
    ])
    assert adapter.poll_once()["results"] == []
    result = adapter.poll_once()
    assert result["results"][0]["value"] == pytest.approx(21.0)
    assert runtime.published[0][1] == pytest.approx(21.0)
    assert adapter.diagnostics()["ignored_count"] == 1


def test_knx_adapter_marks_points_bad_communication_on_transport_failure():
    runtime = FakeRuntime()
    adapter = KnxPointAdapter(FakeSession(fail_connect=True), runtime, "driver-1", [
        KnxPointBinding("point-1", "1/0/1", "1.001"),
    ])
    result = adapter.poll_once()
    assert result["results"][0]["quality"] == "BAD_COMMUNICATION"
    assert runtime.qualities[0][1].value == "BAD_COMMUNICATION"


def test_knx_adapter_marks_bad_configuration_when_dpt_payload_is_invalid():
    runtime = FakeRuntime()
    adapter = KnxPointAdapter(FakeSession([cemi(bytes((0x00, 0x40, 0x0C)))]),
                              runtime, "driver-1", [
        KnxPointBinding("point-1", "1/0/1", "9.001"),
    ])
    result = adapter.poll_once()
    assert result["results"][0]["quality"] == "BAD_CONFIGURATION"


def test_knx_binding_rejects_duplicate_or_unknown_dpt():
    with pytest.raises(ValueError, match="Unsupported KNX DPT"):
        KnxPointBinding("p", "1/0/1", "9.999")
    with pytest.raises(ValueError, match="duplicate KNX group"):
        KnxPointAdapter(FakeSession(), FakeRuntime(), "driver-1", [
            KnxPointBinding("p1", "1/0/1", "1.001"),
            KnxPointBinding("p2", "1/0/1", "1.001"),
        ])


def test_knx_dpt9_signed_mantissa_and_invalid_pattern():
    from avic_core.network.knxnet_ip import decode_datapoint
    assert decode_datapoint(bytes.fromhex("860c"), "9.001") == pytest.approx(-5.0)
    with pytest.raises(KnxProtocolError, match="invalid data pattern"):
        decode_datapoint(bytes.fromhex("7fff"), "9.001")
