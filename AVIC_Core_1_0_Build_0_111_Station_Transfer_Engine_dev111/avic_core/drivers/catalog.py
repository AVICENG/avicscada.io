"""Built-in driver catalog. Catalog entries do not start drivers or perform field I/O."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class DriverLifecycle(str, Enum):
    PROFILE_AVAILABLE = "profile_available"
    READ_ONLY_INTEGRATION = "read_only_integration"
    READ_ONLY_TRANSPORT = "read_only_transport"
    PLANNED = "planned"

@dataclass(frozen=True)
class DriverCatalogEntry:
    driver_id: str
    display_name: str
    protocol: str
    lifecycle: DriverLifecycle
    read_supported: bool
    write_supported: bool = False
    discovery_supported: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.driver_id.strip() or not self.display_name.strip() or not self.protocol.strip():
            raise ValueError("driver identity and protocol are required")
        if self.lifecycle == DriverLifecycle.PLANNED and (self.read_supported or self.discovery_supported or self.write_supported):
            raise ValueError("planned drivers cannot advertise operational capabilities")
        if self.write_supported:
            raise ValueError("built-in catalog does not authorize field writes")

BUILTIN_DRIVERS: tuple[DriverCatalogEntry, ...] = (
    DriverCatalogEntry("bacnet-ip", "BACnet/IP", "BACnet/IP", DriverLifecycle.READ_ONLY_INTEGRATION, True, discovery_supported=True, notes="Read-only protocol client and discovery contracts; no writes."),
    DriverCatalogEntry("trend-iq3-bacnet", "Trend IQ3", "BACnet/IP", DriverLifecycle.READ_ONLY_INTEGRATION, True, notes="Read-only inspection profile; target hardware validation required."),
    DriverCatalogEntry("modbus-tcp", "Modbus TCP", "Modbus TCP", DriverLifecycle.READ_ONLY_TRANSPORT, True, discovery_supported=False, notes="Explicit read-only TCP register/coil reads; no scanner, polling scheduler or writes; hardware validation required."),
)

def list_builtin_drivers() -> tuple[DriverCatalogEntry, ...]:
    return BUILTIN_DRIVERS

def get_driver(driver_id: str) -> DriverCatalogEntry | None:
    key = driver_id.strip().casefold()
    return next((item for item in BUILTIN_DRIVERS if item.driver_id.casefold() == key), None)
