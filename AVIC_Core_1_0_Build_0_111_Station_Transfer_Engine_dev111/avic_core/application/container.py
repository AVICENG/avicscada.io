from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from avic_core.alarm.service import AlarmService
from avic_core.audit.service import AuditService
from avic_core.config.manager import ConfigurationManager
from avic_core.config.project_backup import ProjectBackupManager
from avic_core.deployment import DeploymentManager
from avic_core.transfer import StationTransferManager
from avic_core.domain.service import CoreObjectService
from avic_core.engineering.lifecycle import EngineeringLifecycleService
from avic_core.repository.sqlite_repository import SQLiteRepository
from avic_core.runtime.manager import RuntimeManager, RuntimeState
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
        self.events = EventService(self.paths.databases / "events.sqlite3")
        self.history = HistoryService(self.paths.databases / "history.sqlite3")
        self.dependencies = DependencyService(self.paths.databases / "dependencies.sqlite3")
        self.analytics = AnalyticsService(self.paths.databases / "analytics.sqlite3")
        self.notifications = NotificationService(self.paths.databases / "notifications.sqlite3")
        self.time_management = TimeManagementService(self.paths.databases / "time_management.sqlite3")
        self.module_catalog = ModuleCatalog()
        self.configuration = ConfigurationManager(self.paths.configuration)
        self.backups = ProjectBackupManager()
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

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            failures: list[tuple[str, Exception]] = []
            try:
                self.driver_manager.stop_all()
            except Exception as exc:
                failures.append(("drivers", exc))
            for status in self.runtime.all():
                if status.state != RuntimeState.STOPPED:
                    try:
                        self.runtime.stop(status.station_id)
                    except Exception as exc:  # attempt orderly stop for every station
                        failures.append((status.station_id, exc))
            self.events.record("core.shutdown", "AVIC Core shutdown", severity="INFO", details={"failed_stations": [name for name, _ in failures]})
            self.audit.append(actor_id="system", action="core.shutdown", resource_type="core",
                              resource_id="local", outcome="error" if failures else "success",
                              details={"failed_stations": [name for name, _ in failures]})
            self._closed = True
            if failures:
                names = ", ".join(name for name, _ in failures)
                raise RuntimeError(f"Core closed with station shutdown failures: {names}") from failures[0][1]

    def __enter__(self) -> "CoreApplication":
        self._ensure_open()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
