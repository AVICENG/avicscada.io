"""Typed, side-effect-free contracts for network discovery and BACnet/IP onboarding.

This module intentionally performs no socket I/O and never writes to field devices.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import ipaddress
from typing import Any


class DiscoveryMode(str, Enum):
    PASSIVE = "passive"
    SAFE_READ_ONLY = "safe_read_only"
    ADVANCED_READ_ONLY = "advanced_read_only"


class DiscoveryState(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass(frozen=True)
class BacnetIpNetworkConfig:
    """BACnet/IP network parameters; validation only, no network activation."""
    network_id: str
    interface_name: str
    local_address: str
    subnet_cidr: str
    udp_port: int = 47808
    device_instance: int | None = None
    bbmd_address: str | None = None
    foreign_device_ttl_seconds: int | None = None
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.network_id.strip() or not self.interface_name.strip():
            raise ValueError("network_id and interface_name are required")
        local = ipaddress.ip_address(self.local_address)
        network = ipaddress.ip_network(self.subnet_cidr, strict=False)
        if local.version != 4 or network.version != 4 or local not in network:
            raise ValueError("local_address must be IPv4 and belong to subnet_cidr")
        if not 1 <= self.udp_port <= 65535:
            raise ValueError("udp_port must be between 1 and 65535")
        if self.device_instance is not None and not 0 <= self.device_instance <= 4_194_302:
            raise ValueError("BACnet Device Instance must be in range 0..4194302")
        if self.bbmd_address is not None and ipaddress.ip_address(self.bbmd_address).version != 4:
            raise ValueError("bbmd_address must be IPv4")
        if self.foreign_device_ttl_seconds is not None and self.foreign_device_ttl_seconds <= 0:
            raise ValueError("foreign_device_ttl_seconds must be positive")
        if self.foreign_device_ttl_seconds is not None and self.bbmd_address is None:
            raise ValueError("foreign-device registration requires a BBMD address")


@dataclass(frozen=True)
class DiscoveryPolicy:
    mode: DiscoveryMode = DiscoveryMode.SAFE_READ_ONLY
    allowed_protocols: tuple[str, ...] = ("bacnet/ip",)
    request_timeout_seconds: float = 3.0
    max_retries: int = 1
    max_requests_per_second: float = 5.0
    allow_writes: bool = False
    allow_reboot: bool = False
    allow_configuration_changes: bool = False
    require_operator_confirmation: bool = True

    def __post_init__(self) -> None:
        if not self.allowed_protocols or any(not p.strip() for p in self.allowed_protocols):
            raise ValueError("at least one non-empty protocol is required")
        if self.request_timeout_seconds <= 0 or self.max_retries < 0 or self.max_requests_per_second <= 0:
            raise ValueError("timeouts/rate must be positive and retries non-negative")
        if self.mode != DiscoveryMode.ADVANCED_READ_ONLY and (self.allow_writes or self.allow_reboot or self.allow_configuration_changes):
            raise ValueError("discovery modes are read-only; control operations are prohibited")
        if self.allow_writes or self.allow_reboot or self.allow_configuration_changes:
            raise ValueError("discovery policy cannot authorize field-device control")


@dataclass(frozen=True)
class DiscoveredDevice:
    protocol: str
    network_id: str
    address: str
    device_instance: int | None = None
    vendor_id: int | None = None
    vendor_name: str | None = None
    model_name: str | None = None
    firmware_revision: str | None = None
    object_name: str | None = None
    reachable: bool | None = None
    source: str = "discovery"
    native_identity: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.protocol.strip() or not self.network_id.strip() or not self.address.strip():
            raise ValueError("protocol, network_id and address are required")
        if self.device_instance is not None and not 0 <= self.device_instance <= 4_194_302:
            raise ValueError("invalid BACnet Device Instance")


@dataclass(frozen=True)
class DiscoveredPoint:
    device_identity: str
    object_type: str
    object_instance: int
    object_name: str | None = None
    description: str | None = None
    present_value: Any = None
    units: str | None = None
    data_type: str | None = None
    status_flags: tuple[str, ...] = ()
    reliability: str | None = None
    out_of_service: bool | None = None
    writable: bool | None = None
    native_identity: str | None = None

    def __post_init__(self) -> None:
        if not self.device_identity.strip() or not self.object_type.strip():
            raise ValueError("device_identity and object_type are required")
        if self.object_instance < 0:
            raise ValueError("object_instance must be non-negative")

    @property
    def stable_key(self) -> str:
        return f"{self.device_identity}|{self.object_type}|{self.object_instance}"


@dataclass(frozen=True)
class PointImportPreview:
    discovered_count: int
    new_points: tuple[DiscoveredPoint, ...]
    duplicate_keys: tuple[str, ...] = ()
    unresolved_points: tuple[str, ...] = ()

    @classmethod
    def build(cls, points: tuple[DiscoveredPoint, ...] | list[DiscoveredPoint], existing_keys: set[str] | None = None) -> "PointImportPreview":
        existing = existing_keys or set()
        seen: set[str] = set()
        new: list[DiscoveredPoint] = []
        duplicates: list[str] = []
        for point in points:
            key = point.stable_key
            if key in existing or key in seen:
                duplicates.append(key)
            else:
                seen.add(key)
                new.append(point)
        return cls(len(points), tuple(new), tuple(sorted(set(duplicates))))


@dataclass(frozen=True)
class DiscoverySession:
    session_id: str
    network_id: str
    protocol: str
    mode: DiscoveryMode = DiscoveryMode.SAFE_READ_ONLY
    state: DiscoveryState = DiscoveryState.DRAFT
    devices: tuple[DiscoveredDevice, ...] = ()
    errors: tuple[str, ...] = ()
    started_by: str | None = None
    created_at: str | None = None

    def __post_init__(self) -> None:
        if not self.session_id.strip() or not self.network_id.strip() or not self.protocol.strip():
            raise ValueError("session_id, network_id and protocol are required")
