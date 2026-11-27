from __future__ import annotations

import struct
from types import SimpleNamespace

import pytest

from avic_core.domain.models import PointQuality
from avic_core.drivers.knx_adapter import KnxPointAdapter, KnxPointBinding
from avic_core.network.knxnet_ip import KnxProtocolError, decode_datapoint


@pytest.mark.parametrize(("dpt", "payload", "expected"), [
    ("1.001", b"\x01", True),
    ("1.017", b"\x00", False),
    ("5.001", b"\xff", 100.0),
    ("5.003", b"\xff", 360.0),
    ("5.004", b"\xff", 255),
    ("6.001", b"\xff", -1),
    ("7.001", b"\x12\x34", 0x1234),
    ("8.001", b"\xff\xfe", -2),
    ("12.001", b"\x00\x00\x01\x00", 256),
    ("13.001", b"\xff\xff\xff\xfe", -2),
    ("14.000", struct.pack(">f", 21.5), 21.5),
    ("16.000", b"AVIC".ljust(14, b"\x00"), "AVIC"),
    ("17.001", b"\x05", 5),
])
def test_common_knx_datapoints_decode_strictly(dpt, payload, expected):
    assert decode_datapoint(payload, dpt) == expected


@pytest.mark.parametrize(("dpt", "payload"), [
    ("5.001", b""),
    ("7.001", b"\x01"),
    ("9.001", b"\x7f\xff"),
    ("14.000", struct.pack(">f", float("inf"))),
    ("17.001", b"\x00"),
])
def test_invalid_knx_datapoint_payloads_are_rejected(dpt, payload):
    with pytest.raises(KnxProtocolError):
        decode_datapoint(payload, dpt)


class Runtime:
    def __init__(self):
        self.values = []
        self.qualities = []

    def publish(self, point_id, value, *, quality, source_driver_id):
        self.values.append((point_id, value, quality, source_driver_id))
        return SimpleNamespace(value=value, quality=quality)

    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.qualities.append((point_id, quality, source_driver_id))
        return SimpleNamespace(value=None, quality=quality)


class Session:
    connected = True
    individual_address = 0x1101

    def __init__(self, frame):
        self.frame = frame
        self.sent = []

    def send_cemi(self, frame):
        self.sent.append(frame)

    def poll_cemi(self):
        return self.frame

    def disconnect(self):
        self.connected = False

    def diagnostics(self):
        return {"connected": self.connected}


def group_write_frame(short_value: int) -> bytes:
    # cEMI L_DATA.ind, group destination, GroupValueWrite, one-bit short APDU.
    return bytes((0x29, 0, 0, 0x80, 0x11, 0x01, 0x0A, 0x03,
                  0x01, 0x00, (0x02 << 6) | short_value))


def test_knx_adapter_routes_dpt1_short_value_to_bound_point():
    runtime = Runtime()
    binding = KnxPointBinding("point-bool", "1/2/3", "1.017")
    adapter = KnxPointAdapter(Session(group_write_frame(1)), runtime, "knx-1", [binding])
    result = adapter.poll_once()
    assert result["success_count"] == 1
    assert runtime.values == [("point-bool", True, PointQuality.GOOD, "knx-1")]


def test_knx_binding_accepts_extended_common_dpt_types():
    for dpt in ("5.003", "5.004", "6.001", "7.001", "8.001",
                "12.001", "13.001", "16.000", "17.001", "18.001"):
        assert KnxPointBinding("point-" + dpt, "1/2/3", dpt).datapoint_type == dpt


def group_response_frame(short_value: int) -> bytes:
    return bytes((0x29, 0, 0, 0x80, 0x11, 0x01, 0x0A, 0x03,
                  0x01, 0x00, (0x01 << 6) | short_value))


def test_knx_active_poll_sends_group_value_read_and_publishes_response():
    runtime = Runtime()
    session = Session(group_response_frame(1))
    adapter = KnxPointAdapter(
        session, runtime, "knx-poll", [KnxPointBinding("point-bool", "1/2/3", "1.001")],
        read_mode="poll",
    )
    result = adapter.poll_once()
    assert result["success_count"] == 1
    assert runtime.values[0][0:2] == ("point-bool", True)
    assert session.sent == [bytes((0x11, 0, 0xBC, 0xE0, 0x11, 0x01,
                                   0x0A, 0x03, 0x01, 0, 0))]
    assert adapter.diagnostics()["read_mode"] == "poll"


def test_knx_active_poll_marks_requested_point_bad_on_response_timeout():
    runtime = Runtime()
    session = Session(None)
    adapter = KnxPointAdapter(
        session, runtime, "knx-poll-timeout",
        [KnxPointBinding("point-bool", "1/2/3", "1.001")], read_mode="poll",
    )
    result = adapter.poll_once()
    assert result["failure_count"] == 1
    assert runtime.qualities[0][0:2] == ("point-bool", PointQuality.BAD_COMMUNICATION)
