import pytest

from avic_core.network.knx_cemi import (
    CemiMessageCode, KnxGroupService, parse_cemi_frame,
)
from avic_core.network.knxnet_ip import KnxProtocolError


def _frame(tpdu: bytes, *, message=0x29, destination=0x0801, group=True, info=b""):
    ctrl2 = (0x80 if group else 0) | 0x60
    return (
        bytes((message, len(info))) + info + bytes((0xBC, ctrl2, 0x11, 0x01))
        + destination.to_bytes(2, "big") + bytes((len(tpdu) - 1,)) + tpdu
    )


def test_parse_cemi_group_value_write_short_boolean():
    frame = parse_cemi_frame(_frame(bytes((0x00, 0x81))))
    assert frame.message_code is CemiMessageCode.L_DATA_INDICATION
    assert frame.source_address == 0x1101
    assert frame.group_address == 0x0801
    assert frame.hop_count == 6
    assert frame.service is KnxGroupService.GROUP_VALUE_WRITE
    assert frame.apci == 2
    assert frame.short_value == 1
    assert frame.data == b""


def test_parse_cemi_group_value_read_short_zero():
    frame = parse_cemi_frame(_frame(bytes((0x00, 0x00))))
    assert frame.service is KnxGroupService.GROUP_VALUE_READ
    assert frame.short_value == 0


def test_parse_cemi_group_value_response_with_dpt9_payload():
    frame = parse_cemi_frame(_frame(bytes((0x00, 0x40, 0x0C, 0x1A))))
    assert frame.service is KnxGroupService.GROUP_VALUE_RESPONSE
    assert frame.short_value is None
    assert frame.data == bytes.fromhex("0c1a")


def test_parse_cemi_additional_info_and_individual_destination():
    frame = parse_cemi_frame(_frame(
        bytes((0x00, 0x40, 0x0C, 0x1A)), message=0x2E,
        destination=0x1102, group=False, info=b"\x01\x02\x03",
    ))
    assert frame.message_code is CemiMessageCode.L_DATA_CONFIRM
    assert frame.additional_info == b"\x01\x02\x03"
    assert frame.group_address is None
    assert frame.destination_address == 0x1102


@pytest.mark.parametrize("packet", [
    b"", b"\x29", b"\x29\x04\x00", b"\x99" + b"\x00" * 12,
    bytes((0x29, 0, 0xFC, 0xE0, 0x11, 1, 8, 1, 1, 0, 0x81)),
])
def test_parse_cemi_rejects_truncated_unknown_or_reserved_frames(packet):
    with pytest.raises(KnxProtocolError):
        parse_cemi_frame(packet)


def test_parse_cemi_rejects_npdu_length_mismatch():
    packet = _frame(bytes((0x00, 0x40, 0x0C, 0x1A)))
    with pytest.raises(KnxProtocolError, match="NPDU length mismatch"):
        parse_cemi_frame(packet[:-1])
