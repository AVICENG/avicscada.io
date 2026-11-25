from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

class DriverCapability(str, Enum):
    DISCOVERY = "discovery"
    READ = "read"
    WRITE = "write"
    SUBSCRIPTIONS = "subscriptions"
    DIAGNOSTICS = "diagnostics"
    TIME_SYNC = "time_sync"

@dataclass(frozen=True)
class DriverManifest:
    driver_id: str
    version: str
    vendor: str
    core_api_version: str
    protocols: tuple[str, ...]
    capabilities: frozenset[DriverCapability] = frozenset()
    license_features: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()

@dataclass(frozen=True)
class DriverContext:
    installation_id: str
    project_id: str
    station_id: str
    driver_instance_id: str
    config: dict[str, Any] = field(default_factory=dict)

@runtime_checkable
class Driver(Protocol):
    manifest: DriverManifest
    def initialize(self, context: DriverContext) -> None: ...
    def configure(self, config: dict[str, Any]) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_status(self) -> dict[str, Any]: ...
    def get_diagnostics(self) -> dict[str, Any]: ...
    def shutdown(self) -> None: ...

# Optional methods are capability-gated: discover/read_points/write_point are not
# assumed to exist unless the manifest advertises the corresponding capability.
