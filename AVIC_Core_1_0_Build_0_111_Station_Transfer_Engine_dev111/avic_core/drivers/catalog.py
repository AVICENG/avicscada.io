"""AVIC protocol catalog: advertised capabilities are deliberately conservative."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DriverLifecycle(str, Enum):
    PROFILE_AVAILABLE = "profile_available"
    READ_ONLY_INTEGRATION = "read_only_integration"
    READ_ONLY_TRANSPORT = "read_only_transport"
    PLANNED = "planned"


class DriverCategory(str, Enum):
    TREND = "trend"
    BUILDING_AUTOMATION = "building_automation"
    INDUSTRIAL = "industrial"
    INTEGRATION = "integration"
    SEMANTIC = "semantic"


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
    category: DriverCategory = DriverCategory.INTEGRATION
    license_feature: str = ""

    def __post_init__(self) -> None:
        if not self.driver_id.strip() or not self.display_name.strip() or not self.protocol.strip():
            raise ValueError("driver identity and protocol are required")
        if self.lifecycle == DriverLifecycle.PLANNED and (
            self.read_supported or self.discovery_supported or self.write_supported
        ):
            raise ValueError("planned drivers cannot advertise operational capabilities")
        if self.write_supported:
            raise ValueError("built-in catalog does not authorize field writes")
        if not self.license_feature.strip():
            raise ValueError("every catalog driver must declare a license feature key")


def _planned(driver_id: str, name: str, protocol: str, category: DriverCategory, note: str) -> DriverCatalogEntry:
    return DriverCatalogEntry(
        driver_id, name, protocol, DriverLifecycle.PLANNED, False,
        notes=note, category=category, license_feature=f"driver.{driver_id}",
    )


# Catalog membership is not a claim that a protocol implementation is complete.
# Only the explicitly listed read-only transports expose operational capabilities.
BUILTIN_DRIVERS: tuple[DriverCatalogEntry, ...] = (
    DriverCatalogEntry(
        "trend-ip", "Trend IP / IQ Network", "Trend vCNC over TCP",
        DriverLifecycle.PLANNED, False,
        notes="Priority implementation target. vCNC codec and hardware acceptance are not complete.",
        category=DriverCategory.TREND, license_feature="driver.trend-ip",
    ),
    DriverCatalogEntry(
        "bacnet-ip", "BACnet/IP", "BACnet/IP",
        DriverLifecycle.READ_ONLY_TRANSPORT, True, discovery_supported=True,
        notes="Read-only discovery and ReadProperty plus one-shot Point Runtime adapter; managed polling/COV/commands are not implemented.",
        category=DriverCategory.BUILDING_AUTOMATION, license_feature="driver.bacnet-ip",
    ),
    _planned(
        "bacnet-mstp", "BACnet MS/TP", "BACnet MS/TP over RS-485",
        DriverCategory.BUILDING_AUTOMATION,
        "Requires serial transport, token-passing implementation and hardware acceptance.",
    ),
    DriverCatalogEntry(
        "modbus-tcp", "Modbus TCP", "Modbus TCP",
        DriverLifecycle.READ_ONLY_TRANSPORT, True,
        notes="Read-only FC01/02/03/04 and one-shot Point Runtime adapter; managed polling/map importer/commands are not implemented.",
        category=DriverCategory.INDUSTRIAL, license_feature="driver.modbus-tcp",
    ),
    _planned(
        "modbus-rtu", "Modbus RTU", "Modbus RTU over RS-485",
        DriverCategory.INDUSTRIAL,
        "Requires serial bus manager, framing/CRC, timing and hardware acceptance.",
    ),
    _planned(
        "lonworks", "LonWorks", "LonTalk / LonWorks",
        DriverCategory.BUILDING_AUTOMATION,
        "One protocol driver with manufacturer/device profiles; media and interface support to be validated.",
    ),
    _planned(
        "mbus", "M-Bus (wired)", "EN 13757-2/-3 wired Meter-Bus",
        DriverCategory.BUILDING_AUTOMATION,
        "Planned read-only meter integration using the libmbus C library candidate. Serial converters and TCP gateways are in scope; Wireless M-Bus is a separate engine and is not included.",
    ),
    DriverCatalogEntry(
        "knxnet-ip", "KNXnet/IP (EIB)", "KNXnet/IP",
        DriverLifecycle.READ_ONLY_TRANSPORT, True,
        notes="Read-only KNXnet/IP tunnelling and passive GroupValue monitor with explicit group-address/DPT bindings; no GroupValueWrite transmit, ETS import or Routing yet. Python engine is retained; evaluate XKNX as the maintained protocol library before replacing the current transport implementation.",
        category=DriverCategory.BUILDING_AUTOMATION, license_feature="driver.knxnet-ip",
    ),
    DriverCatalogEntry(
        "mqtt", "MQTT", "MQTT 3.1.1 / 5.0",
        DriverLifecycle.READ_ONLY_TRANSPORT, True,
        notes="Subscribe-only Paho runtime with JSON/raw topic bindings and optional CA-validated TLS; broker credentials/SecretStore integration and live broker acceptance remain outstanding.",
        category=DriverCategory.INTEGRATION, license_feature="driver.mqtt",
    ),
    _planned(
        "s7comm", "Siemens S7", "S7comm / S7CommPlus over ISO-on-TCP",
        DriverCategory.INDUSTRIAL,
        "C-only AVIC policy. Previous Rust/Python paths are not accepted as the target implementation. No selected mature pure-C engine is approved yet: Snap7 is a C++ codebase/toolchain, while libnodave is pure C but upstream explicitly labels it beta and warns about operational risk. Keep disabled until a C engine passes source/license/API audit and read-only simulator/hardware acceptance.",
    ),
    _planned(
        "opc-ua-client", "OPC UA Client", "OPC UA",
        DriverCategory.INDUSTRIAL,
        "DEV225 contracts plus DEV227/DEV228 secure open62541 read/Browse probe exist; probe is not an AVIC IPC worker. Namespace URI lifecycle, Browse paging, subscriptions, reconnect, SecretStore key handoff and hardware acceptance remain outstanding.",
    ),
    _planned(
        "opc-ua-server", "OPC UA Server", "OPC UA",
        DriverCategory.INTEGRATION,
        "Expose selected AVIC points with namespace, identity, certificates and access control.",
    ),
    _planned(
        "opc-da-gateway", "OPC Classic DA Gateway", "OPC DA / COM-DCOM",
        DriverCategory.INTEGRATION,
        "Legacy Windows-only gateway candidate; isolated bridge process, deployment and security review required.",
    ),
    _planned(
        "obix", "oBIX", "oBIX over HTTP(S)",
        DriverCategory.INTEGRATION,
        "REST/XML-oriented building automation interoperability; version/profile compatibility to be specified.",
    ),
    _planned(
        "snmp", "SNMP", "SNMP v1/v2c/v3",
        DriverCategory.INDUSTRIAL,
        "Read-only monitoring first; v3 authentication/privacy and trap/inform handling planned.",
    ),
    _planned(
        "haystack", "Project Haystack", "Haystack tagging/API",
        DriverCategory.SEMANTIC,
        "Semantic tagging and Haystack API interoperability; complements transports rather than replacing them.",
    ),
    _planned(
        "rest-api", "AVIC REST Integration", "HTTPS REST / JSON",
        DriverCategory.INTEGRATION,
        "Authenticated external integration API; scoped tokens, audit and rate limits required.",
    ),
)


def list_builtin_drivers() -> tuple[DriverCatalogEntry, ...]:
    return BUILTIN_DRIVERS


def get_driver(driver_id: str) -> DriverCatalogEntry | None:
    key = driver_id.strip().casefold()
    return next((item for item in BUILTIN_DRIVERS if item.driver_id.casefold() == key), None)


def list_drivers_by_category(category: DriverCategory) -> tuple[DriverCatalogEntry, ...]:
    return tuple(item for item in BUILTIN_DRIVERS if item.category == category)
