"""Strict parser for KNX cEMI L_Data frames and group-value APDUs."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from avic_core.network.knxnet_ip import KnxProtocolError


class CemiMessageCode(str, Enum):
    L_DATA_REQUEST = "L_DATA.req"
    L_DATA_CONFIRM = "L_DATA.con"
    L_DATA_INDICATION = "L_DATA.ind"


class KnxGroupService(str, Enum):
    GROUP_VALUE_READ = "GroupValueRead"
    GROUP_VALUE_RESPONSE = "GroupValueResponse"
    GROUP_VALUE_WRITE = "GroupValueWrite"
    OTHER = "Other"


@dataclass(frozen=True, slots=True)
class KnxCemiFrame:
    message_code: CemiMessageCode
    additional_info: bytes
    control_1: int
    control_2: int
    source_address: int
    destination_address: int
    destination_is_group: bool
    hop_count: int
    priority: int
    tpci: int
    apci: int
    service: KnxGroupService
    short_value: int | None
    data: bytes

    @property
    def group_address(self) -> int | None:
        return self.destination_address if self.destination_is_group else None


_MESSAGE_CODES = {
    0x11: CemiMessageCode.L_DATA_REQUEST,
    0x2E: CemiMessageCode.L_DATA_CONFIRM,
    0x29: CemiMessageCode.L_DATA_INDICATION,
}
_GROUP_SERVICES = {
    0x00: KnxGroupService.GROUP_VALUE_READ,
    0x01: KnxGroupService.GROUP_VALUE_RESPONSE,
    0x02: KnxGroupService.GROUP_VALUE_WRITE,
}


def parse_cemi_frame(packet: bytes) -> KnxCemiFrame:
    """Parse exactly one cEMI L_Data frame; unknown APCI is preserved as OTHER."""
    if not isinstance(packet, bytes) or len(packet) < 11:
        raise KnxProtocolError("cEMI L_Data frame is shorter than its fixed header")
    message_raw, info_length = packet[0], packet[1]
    message_code = _MESSAGE_CODES.get(message_raw)
    if message_code is None:
        raise KnxProtocolError(f"unsupported cEMI message code 0x{message_raw:02X}")
    fixed = 2 + info_length
    if len(packet) < fixed + 9:
        raise KnxProtocolError("cEMI additional information or L_Data header is truncated")
    additional_info = packet[2:fixed]
    control_1, control_2 = packet[fixed], packet[fixed + 1]
    if control_1 & 0x40:
        raise KnxProtocolError("cEMI control field 1 reserved bit is set")
    source = int.from_bytes(packet[fixed + 2:fixed + 4], "big")
    destination = int.from_bytes(packet[fixed + 4:fixed + 6], "big")
    npdu_length = packet[fixed + 6]
    if npdu_length < 1:
        raise KnxProtocolError("cEMI NPDU length must be at least 1")
    tpdu_start = fixed + 7
    if len(packet) < tpdu_start + 2:
        raise KnxProtocolError("cEMI TPDU is truncated")
    tpci_apci_1, apci_data = packet[tpdu_start], packet[tpdu_start + 1]
    data = packet[tpdu_start + 2:]
    expected_data_length = npdu_length - 1
    if len(data) != expected_data_length:
        raise KnxProtocolError(
            f"cEMI NPDU length mismatch: expected {expected_data_length} data octets, got {len(data)}"
        )
    # APCI is split across the lower two bits of octet 1 and upper two
    # bits of octet 2. The remaining six bits carry a short value.
    apci = ((tpci_apci_1 & 0x03) << 2) | (apci_data >> 6)
    short_value = (apci_data & 0x3F) if npdu_length == 1 else None
    service = _GROUP_SERVICES.get(apci, KnxGroupService.OTHER)
    return KnxCemiFrame(
        message_code=message_code,
        additional_info=additional_info,
        control_1=control_1,
        control_2=control_2,
        source_address=source,
        destination_address=destination,
        destination_is_group=bool(control_2 & 0x80),
        hop_count=(control_2 >> 4) & 0x07,
        priority=(control_1 >> 2) & 0x03,
        tpci=tpci_apci_1 >> 6,
        apci=apci,
        service=service,
        short_value=short_value,
        data=data,
    )


__all__ = [
    "CemiMessageCode", "KnxGroupService", "KnxCemiFrame", "parse_cemi_frame",
]
