"""Built-in driver catalog. Entries describe verified capabilities, not UI promises."""
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
        if self.lifecycle == DriverLifecycle.PLANNED and (
            self.read_supported or self.discovery_supported or self.write_supported
        ):
            raise ValueError("planned drivers cannot advertise operational capabilities")
        if self.write_supported:
            raise ValueError("built-in catalog does not authorize field writes")


# Product-level driver set: Trend IP, generic BACnet/IP, generic Modbus TCP.
# Trend-over-BACnet is handled by the generic BACnet driver, not a separate driver.
BUILTIN_DRIVERS: tuple[DriverCatalogEntry, ...] = (
    DriverCatalogEntry(
        "trend-ip", "Trend IP / IQ Network", "Trend vCNC over TCP",
        DriverLifecycle.PLANNED, False,
        notes="Planned standalone Trend driver; vCNC wire codec and field acceptance are not yet implemented.",
    ),
    DriverCatalogEntry(
        "bacnet-ip", "BACnet/IP", "BACnet/IP",
        DriverLifecycle.READ_ONLY_TRANSPORT, True, discovery_supported=True,
        notes="Read-only Who-Is/I-Am, ReadProperty and object inspection transport; polling, COV, PointRuntime adapter and Command Manager are not complete.",
    ),
    DriverCatalogEntry(
        "modbus-tcp", "Modbus TCP", "Modbus TCP",
        DriverLifecycle.READ_ONLY_TRANSPORT, True,
        notes="Read-only FC01/02/03/04 and optional MEI 0x0E transport; point-map import, polling, PointRuntime adapter and Command Manager are not complete.",
    ),
)


def list_builtin_drivers() -> tuple[DriverCatalogEntry, ...]:
    return BUILTIN_DRIVERS


def get_driver(driver_id: str) -> DriverCatalogEntry | None:
    key = driver_id.strip().casefold()
    return next((item for item in BUILTIN_DRIVERS if item.driver_id.casefold() == key), None)
