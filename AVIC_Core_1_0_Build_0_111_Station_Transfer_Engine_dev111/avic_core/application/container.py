from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock

from avic_core.alarm.service import AlarmService
from avic_core.audit.service import AuditService
from avic_core.config.manager import ConfigurationManager
from avic_core.config.project_backup import ProjectBackupManager
from avic_core.backup import SystemBackupManager
from avic_core.deployment import DeploymentManager
from avic_core.transfer import StationTransferManager
from avic_core.domain.service import CoreObjectService
from avic_core.engineering.lifecycle import EngineeringLifecycleService
from avic_core.repository.sqlite_repository import SQLiteRepository
from avic_core.runtime.manager import RuntimeManager, RuntimeState
from avic_core.runtime.fbd_execution import FBDExecutionService
from avic_core.scheduling import ScheduleService
from avic_core.events import EventService
from avic_core.history import HistoryService
from avic_core.dependencies import DependencyService
from avic_core.analytics import AnalyticsService
from avic_core.notifications import NotificationService
from avic_core.time_management import TimeManagementService
from avic_core.platform import ModuleCatalog
from avic_core.domain.point_views import PointViewService
from avic_core.points import PointRuntimeService
from avic_core.drivers.manager import DriverManagerService
from avic_core.graphics.custom_svg_library import CustomSvgLibrary
from .health import CoreHealthService, HealthReport


class CoreClosedError(RuntimeError):
    pass


@dataclass(frozen=True)
class CorePaths:
    root: Path
    databases: Path
    configuration: Path
    backups: Path

    @classmethod
    def under(cls, root: str | Path) -> "CorePaths":
        base = Path(root).expanduser().resolve()
        return cls(base, base / "databases", base / "configuration", base / "backups")


class CoreApplication:
    """Composition root for the local AVIC Core foundation.

    This starts the Core services and owns their lifecycle. It deliberately does not
    start network listeners, drivers or control loops implicitly.
    """

    def __init__(self, data_dir: str | Path):
        self.paths = CorePaths.under(data_dir)
        for directory in (self.paths.root, self.paths.databases, self.paths.configuration, self.paths.backups):
            directory.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._closed = False

        self.repository = SQLiteRepository(self.paths.databases / "objects.sqlite3")
        self.point_views = PointViewService(self.paths.databases / "point_views.sqlite3")
        self.point_runtime = PointRuntimeService(self.repository)
        self.driver_manager = DriverManagerService(self)
        self.audit = AuditService(self.paths.databases / "audit.sqlite3")
        self.custom_svg = CustomSvgLibrary(self.paths.databases / "custom_svg_library.sqlite3")
        self.runtime = RuntimeManager()
        self.fbd_execution = FBDExecutionService(self)
        self._shutdown_in_progress = False
        self._shutdown_blocked = False
        self.events = EventService(self.paths.databases / "events.sqlite3")
        self.history = HistoryService(self.paths.databases / "history.sqlite3")
        self.dependencies = DependencyService(self.paths.databases / "dependencies.sqlite3")
        self.analytics = AnalyticsService(self.paths.databases / "analytics.sqlite3")
        self.notifications = NotificationService(self.paths.databases / "notifications.sqlite3")
        self.time_management = TimeManagementService(self.paths.databases / "time_management.sqlite3")
        self.module_catalog = ModuleCatalog()
        self.configuration = ConfigurationManager(self.paths.configuration)
        self.backups = ProjectBackupManager()
        self.system_backups = SystemBackupManager()
        self.deployment = DeploymentManager()  # Legacy generic project-package API; Station transfer is separate.
        self.station_transfer = StationTransferManager()
        self.objects = CoreObjectService(self.repository)
        self.engineering_lifecycle = EngineeringLifecycleService(self.paths.databases / "engineering_lifecycle.sqlite3")
        self.alarms = AlarmService(self.paths.databases / "alarms.sqlite3", audit_service=self.audit, event_publisher=lambda e: self.events.record("alarm." + e.event_type.lower(), e.message, station_id=e.station_id, severity="WARNING" if e.to_state in {"ACTIVE", "RETURNED_TO_NORMAL"} else "NOTICE", source_id=e.alarm_id, actor_id=e.actor_id, details={"from_state":e.from_state,"to_state":e.to_state,"alarm_id":e.alarm_id}))
        self.schedules = ScheduleService(self.paths.databases / "schedules.sqlite3", repository=self.repository, audit_service=self.audit)
        self.health = CoreHealthService(self.paths.root, self.runtime, self.audit)
        # Retry durable Station Transfer journal deliveries before normal operation.
        # Crash-interrupted PREPARED operations are deliberately flagged for manual
        # reconciliation rather than being reported as successful imports.
        self.station_transfer_recovery = self.station_transfer.recover_pending(self)
        self.events.record("core.initialized", "AVIC Core initialized", severity="INFO", details={"api_version": "1.0.0.dev112"})
        self.audit.append(actor_id="system", action="core.initialized", resource_type="core",
                          resource_id="local", details={"data_dir": str(self.paths.root), "api_version": "1.0.0.dev112"})

    @property
    def closed(self) -> bool:
        return self._closed

    def _ensure_open(self) -> None:
        if self._closed:
            raise CoreClosedError("AVIC Core application is closed")
        if self._shutdown_in_progress or self._shutdown_blocked:
            raise CoreClosedError("AVIC Core shutdown is in progress or blocked; new operations are rejected")

    def shutdown_preview(self) -> dict:
        """Return an operational snapshot; this method never stops services."""
        with self._lock:
            core_state = ("STOPPED" if self._closed else
                          "STOPPING" if self._shutdown_in_progress else
                          "SHUTDOWN_BLOCKED" if self._shutdown_blocked else "RUNNING")
        stations = [
            {"station_id": item.station_id, "state": item.state.value}
            for item in self.runtime.all()
        ]
        drivers = []
        driver_issues = []
        for row in self.repository.list_records(entity_type="DriverInstance"):
            try:
                item = self.driver_manager.diagnostics(row["entity_id"])
                summary = {"instance_id": item["instance_id"], "driver_id": item["driver_id"],
                           "state": item["state"], "field_write_enabled": False}
                if item["state"] in {"STARTING", "RUNNING", "DEGRADED", "STOPPING"}:
                    drivers.append(summary)
                elif item["state"] in {"ORPHANED", "ERROR"}:
                    driver_issues.append(summary)
            except Exception as exc:
                driver_issues.append({"instance_id": row["entity_id"], "state": "INSPECTION_ERROR",
                                      "error": f"{type(exc).__name__}: {exc}"})
        strategies = self.fbd_execution.all_status()
        active_strategies = [
            item for item in strategies
            if item.get("state") in {"RUNNING", "STARTING", "STOPPING"} or item.get("in_flight")
        ]
        return {
            "core_state": core_state,
            "stations": stations,
            "active_stations": [item for item in stations if item["state"] != RuntimeState.STOPPED.value],
            "active_drivers": drivers,
            "driver_issues": driver_issues,
            "active_fbd_strategies": active_strategies,
            "fbd_errors": [item for item in strategies if item.get("state") == "ERROR"],
            "can_shutdown": core_state in {"RUNNING", "SHUTDOWN_BLOCKED"},
            "confirmation_required": "STOP AVIC CORE",
            "field_writes_enabled": False,
        }

    def register_station(self, station_id: str):
        with self._lock:
            self._ensure_open()
            return self.runtime.register(station_id)

    def start_station(self, station_id: str, start_hook=None):
        with self._lock:
            self._ensure_open()
            result = self.runtime.start(station_id, start_hook=start_hook)
        self.events.record("runtime.station_started", f"Station {station_id} started", station_id=station_id, severity="INFO", details={"state": result.state.value})
        self.audit.append(actor_id="system", action="runtime.station_started", resource_type="station",
                          resource_id=station_id, details={"state": result.state.value})
        return result

    def stop_station(self, station_id: str, stop_hook=None):
        with self._lock:
            self._ensure_open()
        driver_error = None
        try:
            self.driver_manager.stop_station(station_id)
        except Exception as exc:
            driver_error = exc
        # Station runtime shutdown is attempted even if a driver worker reports a
        # shutdown failure; the caller receives an explicit error after the stop.
        result = self.runtime.stop(station_id, stop_hook=stop_hook)
        details = {"state": result.state.value,
                   "driver_shutdown_error": f"{type(driver_error).__name__}: {driver_error}" if driver_error else None}
        self.events.record("runtime.station_stopped", f"Station {station_id} stopped", station_id=station_id,
                           severity="ERROR" if driver_error else "NOTICE", details=details)
        self.audit.append(actor_id="system", action="runtime.station_stopped", resource_type="station",
                          resource_id=station_id, outcome="error" if driver_error else "success", details=details)
        if driver_error:
            raise RuntimeError(f"Станция остановлена, но не все драйверы удалось корректно остановить: {driver_error}") from driver_error
        return result

    def health_report(self) -> HealthReport:
        with self._lock:
            self._ensure_open()
        return self.health.inspect()

    def create_backup(self, project_root: str | Path, destination: str | Path | None = None) -> Path:
        with self._lock:
            self._ensure_open()
        output = Path(destination) if destination is not None else self.paths.backups / (Path(project_root).name + ".avicbackup.zip")
        result = self.backups.create_backup(project_root, output)
        self.events.record("backup.created", f"Backup created: {result.name}", severity="INFO", details={"path": str(result)})
        self.audit.append(actor_id="system", action="backup.created", resource_type="project_backup",
                          resource_id=result.name, details={"path": str(result)})
        return result

    def restore_backup(self, backup_path: str | Path, target_root: str | Path, *, expected_backup_id: str):
        with self._lock:
            self._ensure_open()
        # Restore requires the caller to pass the ID obtained from an explicit preview.
        preview = self.backups.preview(backup_path)
        if preview.backup_id != expected_backup_id:
            raise ValueError("Backup changed after preview; restore cancelled")
        result = self.backups.restore(backup_path, target_root, expected_backup_id=expected_backup_id)
        self.events.record("backup.restored", f"Backup restored to {Path(target_root).name}", severity="NOTICE", details={"backup_id": expected_backup_id})
        self.audit.append(actor_id="system", action="backup.restored", resource_type="project",
                          resource_id=Path(target_root).name, details={"backup_id": expected_backup_id})
        return result

    def create_system_backup(self, destination: str | Path | None = None, *, passphrase: str) -> Path:
        with self._lock:
            self._ensure_open()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = Path(destination) if destination is not None else self.paths.backups / f"avic-system-{stamp}.avicbackup"
        result = self.system_backups.create_backup(
            self, output, passphrase=passphrase, core_version="1.0.0.dev145"
        )
        details = {"path": str(result), "encrypted": True}
        self.events.record("system_backup.created", f"Encrypted system backup created: {result.name}",
                           severity="INFO", details=details)
        self.audit.append(actor_id="system", action="system_backup.created", resource_type="system_backup",
                          resource_id=result.name, details=details)
        return result

    def list_system_backups(self):
        with self._lock:
            self._ensure_open()
        return self.system_backups.list_backups(self.paths.backups)

    def prune_system_backups(self, *, keep_last: int):
        with self._lock:
            self._ensure_open()
        removed = self.system_backups.prune_backups(self.paths.backups, keep_last=keep_last)
        if removed:
            details = {"removed": [item.name for item in removed], "keep_last": keep_last}
            self.events.record("system_backup.retention_applied", "System backup retention applied",
                               severity="NOTICE", details=details)
            self.audit.append(actor_id="system", action="system_backup.retention_applied",
                              resource_type="system_backup_catalog", resource_id="local", details=details)
        return removed

    def inspect_system_backup(self, backup_path: str | Path, *, passphrase: str):
        with self._lock:
            self._ensure_open()
        return self.system_backups.inspect_backup(backup_path, passphrase=passphrase)

    def restore_system_backup(self, backup_path: str | Path, target_root: str | Path, *,
                              passphrase: str, expected_backup_id: str) -> Path:
        with self._lock:
            self._ensure_open()
        target = Path(target_root).expanduser().resolve()
        if target == self.paths.root or self.paths.root in target.parents:
            raise ValueError("System restore target must be outside the currently running Core data directory")
        result = self.system_backups.restore_backup(
            backup_path, target, passphrase=passphrase, expected_backup_id=expected_backup_id
        )
        details = {"target": str(result), "backup_id": expected_backup_id}
        self.events.record("system_backup.restored", f"System backup restored to {result}",
                           severity="NOTICE", details=details)
        self.audit.append(actor_id="system", action="system_backup.restored", resource_type="system_backup",
                          resource_id=expected_backup_id, details=details)
        return result

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            if self._shutdown_in_progress:
                raise RuntimeError("AVIC Core shutdown is already in progress")
            self._shutdown_in_progress = True

        # Until FBD execution is hosted by the independent Field Runtime process,
        # an active strategy is a hard shutdown interlock. Closing this Core process
        # would otherwise terminate the only execution owner.
        active_field_strategies = [
            item for item in self.fbd_execution.all_status()
            if item.get("state") in {"RUNNING", "STARTING", "STOPPING"} or item.get("in_flight")
        ]
        if active_field_strategies:
            details = {"active_field_strategies": [
                {"document_id": item.get("document_id"), "station_id": item.get("station_id"),
                 "state": item.get("state"), "in_flight": bool(item.get("in_flight"))}
                for item in active_field_strategies
            ], "reason": "Field Runtime is not yet process-isolated from Core"}
            self.events.record(
                "core.shutdown_blocked_field_runtime",
                "Core shutdown refused: active FBD strategies still belong to this process",
                severity="ERROR", details=details,
            )
            self.audit.append(
                actor_id="system", action="core.shutdown_blocked_field_runtime",
                resource_type="core", resource_id="local", outcome="error", details=details,
            )
            with self._lock:
                self._shutdown_in_progress = False
                self._shutdown_blocked = True
            ids = ", ".join(str(item.get("document_id")) for item in active_field_strategies)
            raise RuntimeError(
                "Остановка AVIC Core заблокирована: активные FBD-стратегии ещё выполняются "
                "в процессе Core. Это временная защитная блокировка до выделения отдельного "
                f"Field Runtime. Стратегии: {ids}"
            )

        failures: list[tuple[str, Exception]] = []
        # No active Field Runtime strategy remains, so the local FBD service can
        # now be closed as part of the Core process teardown.
        try:
            self.fbd_execution.close()
        except Exception as exc:
            failures.append(("fbd_runtime", exc))
        try:
            self.driver_manager.stop_all()
        except Exception as exc:
            failures.append(("drivers", exc))
        for status in self.runtime.all():
            if status.state != RuntimeState.STOPPED:
                try:
                    self.runtime.stop(status.station_id)
                except Exception as exc:
                    failures.append((status.station_id, exc))

        # Do not report a clean shutdown or terminate the host process while any
        # FBD worker, driver worker or station runtime remains active.
        for item in self.fbd_execution.all_status():
            if item.get("in_flight") or item.get("state") in {"RUNNING", "STARTING", "STOPPING"}:
                failures.append((f"fbd:{item.get('document_id')}",
                                 RuntimeError("FBD worker remains active")))
        for status in self.runtime.all():
            if status.state != RuntimeState.STOPPED:
                failures.append((status.station_id, RuntimeError(f"Runtime state is {status.state.value}")))

        details = {"failures": [{"component": name, "error": f"{type(exc).__name__}: {exc}"}
                                for name, exc in failures]}
        if failures:
            self.events.record("core.shutdown_blocked", "AVIC Core shutdown blocked; active workers may remain",
                               severity="ERROR", details=details)
            self.audit.append(actor_id="system", action="core.shutdown_blocked", resource_type="core",
                              resource_id="local", outcome="error", details=details)
            with self._lock:
                self._shutdown_in_progress = False
                self._shutdown_blocked = True
            names = ", ".join(name for name, _ in failures)
            raise RuntimeError(f"AVIC Core shutdown was not confirmed: {names}") from failures[0][1]

        self.events.record("core.shutdown", "AVIC Core shutdown", severity="INFO", details=details)
        self.audit.append(actor_id="system", action="core.shutdown", resource_type="core",
                          resource_id="local", outcome="success", details=details)
        with self._lock:
            self._closed = True
            self._shutdown_in_progress = False

    def __enter__(self) -> "CoreApplication":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
