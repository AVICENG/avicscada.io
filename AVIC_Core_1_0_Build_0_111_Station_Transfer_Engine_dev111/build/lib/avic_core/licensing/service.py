"""Application-facing licensing facade and point-creation guard."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from .host_identity import HostIdentity
from .manager import LicenseManager, LicenseStatus

class LicenseLimitExceeded(PermissionError):
    """Raised when a new unique Point would exceed the signed license limit."""

@dataclass(frozen=True)
class InstallationLicenseState:
    host_id: str
    status: LicenseStatus

class InstallationLicenseService:
    """Binds LicenseManager to this installation's Host ID.

    Runtime preservation is intentionally separate from point-creation authorization.
    """
    def __init__(self, data_dir: str | Path, manager: LicenseManager, identity: HostIdentity | None = None):
        self.identity = identity or HostIdentity(data_dir)
        self.manager = manager

    def host_id(self) -> str:
        return self.identity.get_host_id()

    def inspect(self, license_file: str | Path) -> InstallationLicenseState:
        host = self.host_id()
        return InstallationLicenseState(host, self.manager.verify(license_file, host))

    def assert_can_create_point(self, status: LicenseStatus, existing_point_ids: Iterable[str], new_point_id: str) -> None:
        """A UUID already present is an update/reference, not a new licensed point."""
        ids = {str(item) for item in existing_point_ids}
        if new_point_id in ids: return
        if not status.valid:
            raise LicenseLimitExceeded(f"Создание точки запрещено: лицензия недействительна ({status.reason})")
        if len(ids) >= status.point_limit:
            raise LicenseLimitExceeded(f"Лимит лицензии исчерпан: {len(ids)} из {status.point_limit} точек")


def summarize_point_usage(point_records: Iterable[dict], point_limit: int | None = None) -> dict:
    """Return project and installation point counters from unique Core Point records.

    Legacy Point records remain active physical points. FBD wires/internal signals are
    not Point records and therefore never enter either counter. A calculated point is
    licensed only after it is explicitly published/activated in the Core catalogue.
    """
    records = list(point_records)
    unique: dict[str, dict] = {}
    for record in records:
        if record.get("entity_type") != "Point":
            continue
        point_id = str(record.get("entity_id", ""))
        if not point_id:
            continue
        unique[point_id] = record

    by_type = {"physical": 0, "calculated": 0, "software": 0, "manual": 0}
    licensed_ids: set[str] = set()
    for point_id, record in unique.items():
        payload = record.get("payload", {}) or {}
        kind = str(payload.get("point_type", "physical")).lower()
        if kind not in by_type:
            kind = "software"
        by_type[kind] += 1
        active = payload.get("licensed_active")
        if active is None:
            # Backward compatibility: imported/legacy physical points are active.
            active = kind == "physical"
        if kind != "calculated" or payload.get("published", False):
            if bool(active):
                licensed_ids.add(point_id)

    total = len(unique)
    licensed = len(licensed_ids)
    remaining = None if point_limit is None else max(0, int(point_limit) - licensed)
    ratio = 0 if not point_limit else licensed / int(point_limit)
    warning = "LIMIT_REACHED" if point_limit is not None and licensed >= point_limit else (
        "WARNING_90" if ratio >= .9 else "WARNING_80" if ratio >= .8 else "OK")
    return {
        "project_total_points": total,
        "licensed_active_points": licensed,
        "point_limit": point_limit,
        "remaining_points": remaining,
        "by_type": by_type,
        "warning": warning,
        "unique_point_ids": sorted(unique),
    }
