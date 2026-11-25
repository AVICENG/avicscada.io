"""Cross-protocol device manufacturer/model identity with explicit provenance.

The resolver never guesses a model. Manufacturer mappings are protocol-scoped;
MAC OUI mappings are only used when an authoritative OUI entry is registered.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class IdentityConfidence(str, Enum):
    CONFIRMED = "confirmed"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class IdentityEvidence:
    field: str
    value: str
    source: str
    confidence: IdentityConfidence = IdentityConfidence.CONFIRMED
    protocol: str | None = None


@dataclass(frozen=True)
class DeviceIdentity:
    manufacturer: str | None = None
    model: str | None = None
    device_type: str | None = None
    firmware_revision: str | None = None
    manufacturer_source: str | None = None
    model_source: str | None = None
    confidence: IdentityConfidence = IdentityConfidence.UNKNOWN
    evidence: tuple[IdentityEvidence, ...] = ()


@dataclass(frozen=True)
class VendorRecord:
    name: str
    protocol: str
    identifier: str


class VendorRegistry:
    """Small deterministic registry; can be extended by signed driver/vendor packs."""
    def __init__(self, records: Iterable[VendorRecord] | None = None):
        self._records: dict[tuple[str, str], VendorRecord] = {}
        for record in records or (VendorRecord("Trend Control Systems", "bacnet", "91"),):
            self.register(record)

    def register(self, record: VendorRecord) -> None:
        protocol = record.protocol.strip().lower()
        identifier = record.identifier.strip().lower()
        if not protocol or not identifier or not record.name.strip():
            raise ValueError("vendor record fields must be non-empty")
        self._records[(protocol, identifier)] = VendorRecord(record.name.strip(), protocol, identifier)

    def resolve(self, protocol: str, identifier: str | int | None) -> VendorRecord | None:
        if identifier is None:
            return None
        return self._records.get((protocol.strip().lower(), str(identifier).strip().lower()))


class DeviceIdentityResolver:
    """Resolve identity from explicit protocol IDs and device-reported properties."""
    def __init__(self, registry: VendorRegistry | None = None):
        self.registry = registry or VendorRegistry()

    def resolve(self, *, protocol: str, vendor_id: str | int | None = None,
                vendor_name: str | None = None, model_name: str | None = None,
                device_type: str | None = None, firmware_revision: str | None = None,
                mac_address: str | None = None) -> DeviceIdentity:
        p = protocol.strip().lower()
        evidence: list[IdentityEvidence] = []
        manufacturer = None
        manufacturer_source = None
        if vendor_name and vendor_name.strip():
            manufacturer = vendor_name.strip()
            manufacturer_source = f"{p}.vendor_name"
            evidence.append(IdentityEvidence("manufacturer", manufacturer, manufacturer_source,
                                             IdentityConfidence.CONFIRMED, p))
        else:
            record = self.registry.resolve(p.split("/")[0], vendor_id)
            if record:
                manufacturer = record.name
                manufacturer_source = f"{p}.vendor_id:{vendor_id}"
                evidence.append(IdentityEvidence("manufacturer", manufacturer, manufacturer_source,
                                                 IdentityConfidence.CONFIRMED, p))
        model = model_name.strip() if model_name and model_name.strip() else None
        if model:
            evidence.append(IdentityEvidence("model", model, f"{p}.model_name",
                                             IdentityConfidence.CONFIRMED, p))
        dtype = device_type.strip() if device_type and device_type.strip() else None
        if dtype:
            evidence.append(IdentityEvidence("device_type", dtype, f"{p}.device_type",
                                             IdentityConfidence.CONFIRMED, p))
        firmware = firmware_revision.strip() if firmware_revision and firmware_revision.strip() else None
        if firmware:
            evidence.append(IdentityEvidence("firmware_revision", firmware, f"{p}.firmware_revision",
                                             IdentityConfidence.CONFIRMED, p))
        if mac_address and _valid_mac(mac_address):
            evidence.append(IdentityEvidence("mac_address", mac_address.upper(), "network.mac_address",
                                             IdentityConfidence.CONFIRMED, p))
        confidence = IdentityConfidence.CONFIRMED if manufacturer or model or dtype or firmware else IdentityConfidence.UNKNOWN
        return DeviceIdentity(manufacturer, model, dtype, firmware, manufacturer_source,
                              f"{p}.model_name" if model else None, confidence, tuple(evidence))


def _valid_mac(value: str) -> bool:
    parts = value.replace("-", ":").split(":")
    return len(parts) == 6 and all(len(part) == 2 and all(c in "0123456789abcdefABCDEF" for c in part) for part in parts)
