"""Typed engineering topology: physical media, protocol channels and devices."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class PhysicalMedium(str, Enum):
    ETHERNET = "ethernet"
    RS485 = "rs485"
    WIFI = "wifi"
    SERIAL = "serial"
    OTHER = "other"

@dataclass(frozen=True)
class PhysicalNetwork:
    network_id: str
    name: str
    medium: PhysicalMedium
    description: str = ""

    def __post_init__(self) -> None:
        if not self.network_id.strip() or not self.name.strip():
            raise ValueError("network_id and name are required")

@dataclass(frozen=True)
class ProtocolChannel:
    channel_id: str
    network_id: str
    protocol: str
    transport: str
    port: int | None = None
    description: str = ""

    def __post_init__(self) -> None:
        if not self.channel_id.strip() or not self.network_id.strip() or not self.protocol.strip() or not self.transport.strip():
            raise ValueError("channel_id, network_id, protocol and transport are required")
        if self.port is not None and not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")

@dataclass(frozen=True)
class DeviceNetworkBinding:
    device_id: str
    channel_id: str
    address: str
    native_identity: str | None = None

    def __post_init__(self) -> None:
        if not self.device_id.strip() or not self.channel_id.strip() or not self.address.strip():
            raise ValueError("device_id, channel_id and address are required")
