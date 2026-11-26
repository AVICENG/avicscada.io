from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PointDirection(str, Enum):
    INPUT = "input"
    OUTPUT = "output"
    INOUT = "inout"


class PointQuality(str, Enum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    BAD_COMMUNICATION = "BAD_COMMUNICATION"
    BAD_CONFIGURATION = "BAD_CONFIGURATION"
    DISABLED = "DISABLED"


@dataclass(slots=True)
class BaseObject:
    name: str
    id: str = field(default_factory=new_id)
    description: str = ""
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    archived: bool = False

    def __post_init__(self):
        UUID(self.id)
        if not self.name or not self.name.strip():
            raise ValueError("Object name cannot be empty")


@dataclass(slots=True)
class Platform(BaseObject):
    installation_id: str = field(default_factory=new_id)


@dataclass(slots=True)
class Project(BaseObject):
    platform_id: str = ""


@dataclass(slots=True)
class Station(BaseObject):
    project_id: str = ""
    config_revision: int = 0


@dataclass(slots=True)
class PhysicalNetwork(BaseObject):
    """Persistent station network segment; physical interface is explicit."""
    station_id: str = ""
    interface_id: str = ""
    interface_name: str = ""
    ipv4: str = ""
    subnet_cidr: str = ""
    network_kind: str = "ethernet"
    addressing_mode: str = "auto"
    station_ipv4: str = ""
    gateway_ipv4: str = ""
    dns_servers: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ProtocolChannel(BaseObject):
    """Protocol channel bound to one physical network, kept separate from media."""
    station_id: str = ""
    network_id: str = ""
    protocol: str = "bacnet/ip"
    enabled: bool = True
    mode: str = "read_only"


@dataclass(slots=True)
class Device(BaseObject):
    station_id: str = ""
    driver_instance_id: str = ""
    address: str = ""
    protocol: str = ""
    network_id: str = ""
    native_identity: str = ""
    manufacturer: str = ""
    model: str = ""
    firmware_revision: str = ""
    vendor_id: int | None = None
    identity_sources: dict[str, str] = field(default_factory=dict)
    engineering_description: str = ""


@dataclass(slots=True)
class Point(BaseObject):
    device_id: str = ""
    data_type: str = "float"
    unit: str = ""
    direction: PointDirection = PointDirection.INPUT
    source_ref: str = ""
    value: Any = None
    quality: PointQuality = PointQuality.UNCERTAIN
    timestamp: datetime | None = None
    native_identity: str = ""
    object_type: str = ""
    engineering_description: str = ""
    # Licensing metadata: discovered points can remain unlicensed until used.
    point_type: str = "physical"
    licensed_active: bool | None = None
    published: bool = False
    licensed_usage: list[str] = field(default_factory=list)

    def update_value(self, value: Any, quality: PointQuality, timestamp: datetime | None = None):
        self.value = value
        self.quality = quality
        self.timestamp = timestamp or utc_now()
        self.updated_at = utc_now()


@dataclass(slots=True)
class Component(BaseObject):
    station_id: str = ""
    component_type: str = ""
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Link(BaseObject):
    station_id: str = ""
    source_object_id: str = ""
    source_slot: str = ""
    target_object_id: str = ""
    target_slot: str = ""


@dataclass(slots=True)
class PropertyDefinition(BaseObject):
    owner_object_id: str = ""
    property_key: str = ""
    data_type: str = "string"
    writable: bool = False
    default_value: Any = None


@dataclass(slots=True)
class Alarm(BaseObject):
    station_id: str = ""
    source_object_id: str = ""
    alarm_type: str = "standard"
    priority: int = 100
    state: str = "NORMAL"
    acknowledged_by: str | None = None
    acknowledged_at: datetime | None = None


@dataclass(slots=True)
class Event(BaseObject):
    station_id: str = ""
    event_type: str = ""
    source_object_id: str | None = None
    occurred_at: datetime = field(default_factory=utc_now)
    data: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class HistoryRecord(BaseObject):
    station_id: str = ""
    point_id: str = ""
    value: Any = None
    quality: PointQuality = PointQuality.UNCERTAIN
    recorded_at: datetime = field(default_factory=utc_now)


@dataclass(slots=True)
class DriverPackage(BaseObject):
    package_id: str = ""
    version: str = "0.0.0"
    vendor: str = ""
    core_api_version: str = "1.0"
    signature_status: str = "UNVERIFIED"


@dataclass(slots=True)
class DriverInstance(BaseObject):
    station_id: str = ""
    package_id: str = ""
    package_version: str = ""
    configuration: dict[str, Any] = field(default_factory=dict)
    state: str = "STOPPED"


@dataclass(slots=True)
class RuntimeInstance(BaseObject):
    station_id: str = ""
    state: str = "STOPPED"
    generation: int = 0
    worker_id: str | None = None


@dataclass(slots=True)
class User(BaseObject):
    username: str = ""
    password_hash: str = ""
    enabled: bool = True


@dataclass(slots=True)
class Role(BaseObject):
    permissions: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Permission(BaseObject):
    permission_id: str = ""
    description: str = ""
