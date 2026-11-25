"""Offline, Host-ID-bound AVIC license verification (Ed25519)."""
from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

LICENSE_FORMAT = "avic-license-v1"


def canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


@dataclass(frozen=True)
class RuntimePreservationDecision:
    allowed: bool
    reason: str


@dataclass(frozen=True)
class LicenseStatus:
    valid: bool
    reason: str
    host_id: str | None = None
    customer: str | None = None
    point_limit: int = 0
    features: tuple[str, ...] = ()
    license_id: str | None = None


class LicenseManager:
    """Verifies a signed license. The private signing key must never ship with AVIC SCADA."""
    def __init__(self, public_key: Ed25519PublicKey | bytes | str | Path):
        if isinstance(public_key, Ed25519PublicKey):
            self.public_key = public_key
        else:
            raw = Path(public_key).read_bytes() if isinstance(public_key, (str, Path)) else public_key
            key = serialization.load_pem_public_key(raw)
            if not isinstance(key, Ed25519PublicKey):
                raise TypeError("AVIC license public key must be Ed25519")
            self.public_key = key

    def verify(self, license_data: dict[str, Any] | str | Path, host_id: str,
               *, now: datetime | None = None) -> LicenseStatus:
        try:
            if isinstance(license_data, (str, Path)):
                data = json.loads(Path(license_data).read_text(encoding="utf-8"))
            else:
                data = license_data
            if not isinstance(data, dict) or data.get("format") != LICENSE_FORMAT:
                return LicenseStatus(False, "INVALID_FORMAT")
            signature = base64.b64decode(data["signature"], validate=True)
            payload = {k: v for k, v in data.items() if k != "signature"}
            self.public_key.verify(signature, canonical_payload(payload))
            required = {"license_id", "host_id", "customer", "issued_at", "point_limit", "features", "expires_at", "key_id"}
            if not required.issubset(payload):
                return LicenseStatus(False, "MISSING_FIELDS")
            if not isinstance(payload["point_limit"], int) or isinstance(payload["point_limit"], bool) or payload["point_limit"] < 0:
                return LicenseStatus(False, "INVALID_POINT_LIMIT")
            if payload["host_id"] != host_id:
                return LicenseStatus(False, "HOST_ID_MISMATCH", payload.get("host_id"), payload.get("customer"), payload.get("point_limit", 0))
            if payload["expires_at"]:
                expiry = datetime.fromisoformat(payload["expires_at"].replace("Z", "+00:00"))
                current = now or datetime.now(timezone.utc)
                if current.tzinfo is None:
                    current = current.replace(tzinfo=timezone.utc)
                if current > expiry:
                    return LicenseStatus(False, "LICENSE_EXPIRED", payload["host_id"], payload["customer"], payload["point_limit"], tuple(payload["features"]), payload["license_id"])
            return LicenseStatus(True, "OK", payload["host_id"], payload["customer"], payload["point_limit"], tuple(payload["features"]), payload["license_id"])
        except InvalidSignature:
            return LicenseStatus(False, "INVALID_SIGNATURE")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return LicenseStatus(False, "INVALID_LICENSE")

    def can_create_point(self, status: LicenseStatus, current_unique_point_ids: set[str] | list[str] | tuple[str, ...]) -> bool:
        """One persistent Point UUID consumes one slot; graphics/trend references do not."""
        return status.valid and len(set(current_unique_point_ids)) < status.point_limit

    def validate_existing_runtime(self, status: LicenseStatus, current_unique_point_ids: set[str] | list[str] | tuple[str, ...]) -> RuntimePreservationDecision:
        """Licensing never stops an already configured Runtime, even if license is invalid/expired."""
        if not status.valid:
            return RuntimePreservationDecision(True, "EXISTING_RUNTIME_PRESERVED_LICENSE_INVALID")
        if len(set(current_unique_point_ids)) > status.point_limit:
            return RuntimePreservationDecision(True, "EXISTING_RUNTIME_PRESERVED_OVER_LIMIT")
        return RuntimePreservationDecision(True, "OK")
