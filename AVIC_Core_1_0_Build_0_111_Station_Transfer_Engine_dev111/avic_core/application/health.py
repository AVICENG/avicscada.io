from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from avic_core.runtime.manager import RuntimeManager, RuntimeState


@dataclass(frozen=True)
class HealthCheck:
    name: str
    status: str
    details: str = ""


@dataclass(frozen=True)
class HealthReport:
    status: str
    checked_at: str
    checks: tuple[HealthCheck, ...]


class CoreHealthService:
    """Read-only health aggregation for the local Core process."""

    def __init__(self, data_dir: str | Path, runtime: RuntimeManager, audit_service):
        self.data_dir = Path(data_dir)
        self.runtime = runtime
        self.audit_service = audit_service

    def inspect(self) -> HealthReport:
        checks: list[HealthCheck] = []
        checks.append(HealthCheck("data_directory", "OK" if self.data_dir.is_dir() else "ERROR", str(self.data_dir)))
        audit_ok, audit_count = self.audit_service.verify_chain()
        checks.append(HealthCheck("audit_chain", "OK" if audit_ok else "ERROR", f"records={audit_count}"))
        statuses = self.runtime.all()
        failed = [item for item in statuses if item.state == RuntimeState.ERROR]
        degraded = [item for item in statuses if item.state == RuntimeState.DEGRADED]
        if failed:
            state, detail = "ERROR", f"error_stations={','.join(x.station_id for x in failed)}"
        elif degraded:
            state, detail = "DEGRADED", f"degraded_stations={','.join(x.station_id for x in degraded)}"
        else:
            state, detail = "OK", f"registered_stations={len(statuses)}"
        checks.append(HealthCheck("runtime", state, detail))
        overall = "ERROR" if any(x.status == "ERROR" for x in checks) else ("DEGRADED" if any(x.status == "DEGRADED" for x in checks) else "OK")
        return HealthReport(overall, datetime.now(timezone.utc).isoformat(), tuple(checks))
