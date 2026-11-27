"""Persistent driver inventory and explicitly controlled runtime lifecycle."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import ipaddress
from threading import RLock
from typing import Callable, Any
from uuid import UUID, uuid4

from avic_core.drivers.catalog import list_builtin_drivers
from avic_core.drivers.polling import PollingSession
from avic_core.runtime.point_scheduler import PointRuntimeScheduler
from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.drivers.knx_adapter import KnxPointAdapter, KnxPointBinding
from avic_core.network.modbus_tcp import ModbusTcpClient
from avic_core.network.bacnet_ip import BacnetIpClient
from avic_core.network.contracts import BacnetIpNetworkConfig, DiscoveryPolicy
from avic_core.network.knx_tunneling import KnxTunnelingSession
from avic_core.drivers.rust_point_adapter import RustDriverPointAdapter


def _now():
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class DriverInstance:
    name: str
    station_id: str
    driver_id: str
    protocol: str
    id: str = field(default_factory=lambda: str(uuid4()))
    version: str = ""
    state: str = "STOPPED"
    config: dict = field(default_factory=dict)
    enabled: bool = False
    package_trust: str = "BUILTIN"
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    runtime_generation: int = 0

    def __post_init__(self):
        UUID(self.id)
        UUID(self.station_id)
        if not self.name.strip() or not self.driver_id.strip() or not self.protocol.strip():
            raise ValueError("Имя, идентификатор драйвера и протокол обязательны")
        states = {"STOPPED", "STARTING", "RUNNING", "DEGRADED", "STOPPING", "ERROR"}
        if self.state not in states:
            raise ValueError("Недопустимое состояние экземпляра драйвера")
        active = self.state in {"STARTING", "RUNNING", "DEGRADED", "STOPPING"}
        if self.enabled != active:
            raise ValueError("Флаг enabled не соответствует состоянию драйвера")
        if isinstance(self.runtime_generation, bool) or not isinstance(self.runtime_generation, int) or self.runtime_generation < 0:
            raise ValueError("runtime_generation must be a non-negative integer")
        if self.package_trust not in {"BUILTIN", "VERIFIED", "UNVERIFIED", "REJECTED"}:
            raise ValueError("Недопустимый статус доверия пакету")


class DriverManagerService:
    """Owns explicit read-only adapter sessions; no implicit field I/O at Core startup."""

    _SECRET_KEYS = {
        "password", "passwd", "secret", "token", "privatekey", "credential",
        "credentials", "clientsecret", "clientkey", "apikey", "accesstoken",
        "refreshtoken", "authtoken", "authorization", "bearer", "tlskey",
        "tlsprivatekey", "mqttpassword", "databasepassword", "jwt",
    }
    _SECRET_SUFFIXES = (
        "password", "passwd", "secret", "secretkey", "privatekey", "apikey",
        "credential", "accesstoken", "refreshtoken", "authtoken", "clientkey",
        "tlskey", "token", "signingkey", "accesskey", "sharedsecret", "sessionkey",
    )

    def __init__(self, core):
        self.core = core
        self._lock = RLock()
        self._rust_worker_command: str | None = None
        self._factories: dict[str, Callable[[Any, DriverInstance], Any]] = {
            "modbus-tcp": self._build_modbus_adapter,
            "bacnet-ip": self._build_bacnet_adapter,
            "knxnet-ip": self._build_knx_adapter,
        }
        self._sessions: dict[str, PollingSession] = {}
        self._adapters: dict[str, Any] = {}
        self._point_runtime_scheduler = PointRuntimeScheduler(core.point_runtime)
        self._scheduler_lifecycle_lock = RLock()

    @classmethod
    def _reject_secrets(cls, value: Any, path: str = "config") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                normalized = "".join(ch for ch in str(key).casefold() if ch.isalnum())
                if normalized in cls._SECRET_KEYS or normalized.endswith(cls._SECRET_SUFFIXES):
                    raise ValueError(f"Секреты нельзя хранить в конфигурации экземпляра ({path}.{key}); используйте SecretStore")
                cls._reject_secrets(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                cls._reject_secrets(item, f"{path}[{index}]")

    def register_rust_worker_command(self, executable: str) -> str:
        """Register an administrator-selected, absolute Rust worker executable path."""
        from pathlib import Path
        path = Path(executable).expanduser()
        if not path.is_absolute() or not path.is_file():
            raise ValueError("Rust worker must be an existing absolute executable path")
        resolved_path = path.resolve(strict=True)
        import os
        if os.name != "nt" and not os.access(resolved_path, os.X_OK):
            raise ValueError("Rust worker file is not executable")
        resolved = str(resolved_path)
        with self._lock:
            if self._sessions:
                raise RuntimeError("Rust worker executable cannot change while drivers are active")
            self._rust_worker_command = resolved
        return resolved

    def _build_rust_adapter(self, core, instance: DriverInstance, cfg: dict, protocol: str, bindings):
        if not self._rust_worker_command:
            raise RuntimeError("Rust worker executable is not registered by the AVIC administrator")
        station = core.repository.get_record(instance.station_id)
        project_id = station["payload"].get("project_id")
        if not project_id:
            raise ValueError("Station has no owning Project; Rust worker scope cannot be established")
        project = core.repository.get_record(project_id)
        platform_id = project["payload"].get("platform_id")
        installation_id = None
        if platform_id:
            platform = core.repository.get_record(platform_id)
            installation_id = platform["payload"].get("installation_id")
        # Older projects may not yet have a Platform record. Use the Core data
        # directory as a stable local installation scope, never a caller value.
        if not installation_id:
            installation_id = str(core.paths.root.resolve())
        worker_config = dict(cfg)
        worker_config["project_id"] = project_id
        worker_config["station_id"] = instance.station_id
        return RustDriverPointAdapter(
            worker_command=[self._rust_worker_command], core=core,
            driver_instance_id=instance.id, protocol=protocol,
            config=worker_config, bindings=bindings,
            installation_id=str(installation_id), project_id=str(project_id),
            station_id=instance.station_id,
            generation=max(1, int(instance.runtime_generation)),
        )

    def register_adapter_factory(self, driver_id: str, factory: Callable[[Any, DriverInstance], Any]) -> None:
        if driver_id not in {item.driver_id for item in list_builtin_drivers()}:
            raise ValueError("Драйвер отсутствует во встроенном каталоге")
        if not callable(factory):
            raise TypeError("factory must be callable")
        with self._lock:
            for instance_id in self._sessions:
                active_item, _ = self._load(instance_id)
                if active_item.driver_id == driver_id:
                    raise RuntimeError(
                        f"Нельзя менять factory {driver_id} во время активной сессии этого драйвера"
                    )
            self._factories[driver_id] = factory

    def _build_modbus_adapter(self, core, instance: DriverInstance):
        cfg = dict(instance.config)
        allowed = {"host", "port", "unit_id", "timeout", "poll_interval_seconds", "bindings", "engine"}
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры Modbus TCP: {sorted(unknown)}")
        engine = cfg.get("engine", "python")
        if engine not in {"python", "rust"}:
            raise ValueError("engine must be python or rust")
        if not cfg.get("host") or not isinstance(cfg.get("bindings"), list) or not cfg["bindings"]:
            raise ValueError("Для Modbus TCP требуются host и непустой bindings")
        bindings = [ModbusTcpPointBinding(**item) for item in cfg["bindings"]]
        client = ModbusTcpClient(
            cfg["host"], port=int(cfg.get("port", 502)),
            unit_id=int(cfg.get("unit_id", 1)), timeout=float(cfg.get("timeout", 2.0)),
        )
        if engine == "rust":
            return self._build_rust_adapter(core, instance, cfg, "modbus-tcp", [asdict(item) for item in bindings])
        return ModbusTcpPointAdapter(client, core.point_runtime, instance.id, bindings)

    def _build_bacnet_adapter(self, core, instance: DriverInstance):
        cfg = dict(instance.config)
        allowed = {"network_id", "interface_name", "local_address", "subnet_cidr",
                   "udp_port", "device_instance", "timeout", "poll_interval_seconds", "bindings", "engine"}
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры BACnet/IP: {sorted(unknown)}")
        engine = cfg.get("engine", "python")
        if engine not in {"python", "rust"}:
            raise ValueError("engine must be python or rust")
        required = ("network_id", "interface_name", "local_address", "subnet_cidr")
        if any(not cfg.get(key) for key in required) or not isinstance(cfg.get("bindings"), list) or not cfg["bindings"]:
            raise ValueError("Для BACnet/IP требуются параметры сети и непустой bindings")
        network = BacnetIpNetworkConfig(
            network_id=cfg["network_id"], interface_name=cfg["interface_name"],
            local_address=cfg["local_address"], subnet_cidr=cfg["subnet_cidr"],
            udp_port=int(cfg.get("udp_port", 47808)),
            device_instance=cfg.get("device_instance"),
        )
        bindings = []
        for raw in cfg["bindings"]:
            item = dict(raw)
            if "address" in item:
                item["address"] = tuple(item["address"])
            bindings.append(BacnetIpPointBinding(**item))
        if engine == "rust":
            return self._build_rust_adapter(core, instance, cfg, "bacnet-ip", [asdict(item) for item in bindings])
        client = BacnetIpClient(network, DiscoveryPolicy(
            request_timeout_seconds=float(cfg.get("timeout", 3.0)),
        ))
        return BacnetIpPointAdapter(client, core.point_runtime, instance.id, bindings)

    def _build_knx_adapter(self, core, instance: DriverInstance):
        cfg = dict(instance.config)
        allowed = {
            "gateway_host", "gateway_port", "local_host", "local_port", "timeout",
            "retries", "heartbeat_interval_seconds", "poll_interval_seconds", "bindings", "engine",
        }
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры KNXnet/IP: {sorted(unknown)}")
        engine = cfg.get("engine", "python")
        if engine not in {"python", "rust"}:
            raise ValueError("engine must be python or rust")
        required = ("gateway_host", "local_host")
        if any(not cfg.get(key) for key in required) or not isinstance(cfg.get("bindings"), list) or not cfg["bindings"]:
            raise ValueError("Для KNXnet/IP требуются gateway_host, local_host и непустой bindings")
        bindings = [KnxPointBinding(**item) for item in cfg["bindings"]]
        if engine == "rust":
            return self._build_rust_adapter(core, instance, cfg, "knxnet-ip", [asdict(item) for item in bindings])
        session = KnxTunnelingSession(
            cfg["gateway_host"], gateway_port=int(cfg.get("gateway_port", 3671)),
            local_host=cfg["local_host"], local_port=int(cfg.get("local_port", 0)),
            timeout_seconds=float(cfg.get("timeout", 1.0)), retries=int(cfg.get("retries", 2)),
            heartbeat_interval_seconds=float(cfg.get("heartbeat_interval_seconds", 60.0)),
        )
        return KnxPointAdapter(session, core.point_runtime, instance.id, bindings)

    def catalog(self):
        return [{"driver_id": x.driver_id, "name": x.display_name, "protocol": x.protocol,
                 "lifecycle": x.lifecycle.value, "read_supported": x.read_supported,
                 "write_supported": False, "discovery_supported": x.discovery_supported,
                 "runtime_start_supported": x.driver_id in self._factories,
                 "rust_engine_available": self._rust_worker_command is not None,
                 "license_feature": x.license_feature, "notes": x.notes} for x in list_builtin_drivers()]

    def list_instances(self, station_id: str):
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        result = []
        for row in self.core.repository.list_records(entity_type="DriverInstance", station_id=station_id):
            p = row["payload"]
            runtime = self.diagnostics(row["entity_id"])
            result.append({"id": row["entity_id"], "name": row["name"], "driver_id": p["driver_id"],
                "protocol": p["protocol"], "version": p.get("version", ""),
                "state": runtime["state"], "persisted_state": p["state"],
                "enabled": runtime["enabled"], "field_read_enabled": runtime["field_read_enabled"],
                "field_write_enabled": False, "package_trust": p["package_trust"],
                "config": p.get("config", {})})
        return result

    def assert_driver_entitlement(self, driver_id: str) -> None:
        """Require the signed feature entitlement for an operational driver action."""
        self._assert_driver_entitlement(driver_id)

    def _assert_driver_entitlement(self, driver_id: str) -> None:
        service = getattr(self.core, "installation_license_service", None)
        license_file = getattr(self.core, "license_file", None)
        if service is None:
            return  # Explicit development/unconfigured mode; production must inject a signed license service.
        entry = next((item for item in list_builtin_drivers() if item.driver_id == driver_id), None)
        if entry is None:
            raise ValueError("Драйвер отсутствует во встроенном каталоге")
        status = service.inspect(license_file).status
        service.assert_feature_enabled(status, entry.license_feature)

    def create_instance(self, station_id: str, driver_id: str, name: str, config: dict | None = None):
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        entry = next((x for x in list_builtin_drivers() if x.driver_id == driver_id), None)
        if entry is None:
            raise ValueError("Драйвер отсутствует в доверенном встроенном каталоге")
        if entry.lifecycle.value == "planned":
            raise ValueError("Драйвер пока не реализован")
        self._assert_driver_entitlement(driver_id)
        if config is not None and not isinstance(config, dict):
            raise ValueError("Конфигурация должна быть объектом")
        safe_config = dict(config or {})
        self._reject_secrets(safe_config)
        item = DriverInstance(name=name, station_id=station_id, driver_id=entry.driver_id,
            protocol=entry.protocol, config=safe_config)
        self.core.repository.save(item)
        self.core.audit.append(actor_id="local-engineer", action="driver.instance_created",
            resource_type="driver_instance", resource_id=item.id,
            details={"station_id": station_id, "driver_id": driver_id, "state": "STOPPED"})
        return {"id": item.id, "name": item.name, "station_id": station_id, "driver_id": driver_id,
            "protocol": item.protocol, "state": "STOPPED", "enabled": False,
            "package_trust": "BUILTIN", "field_io_enabled": False}

    def update_config(self, instance_id: str, config: dict, *, expected_version: int) -> dict:
        """Replace a stopped driver's configuration with optimistic concurrency."""
        if not isinstance(config, dict):
            raise ValueError("Конфигурация должна быть объектом")
        safe_config = dict(config)
        self._reject_secrets(safe_config)
        with self._lock:
            item, version = self._load(instance_id)
            self._assert_driver_entitlement(item.driver_id)
            if version != expected_version:
                from avic_core.repository.sqlite_repository import ConcurrencyConflict
                raise ConcurrencyConflict(
                    f"Driver instance {instance_id} version changed: expected {expected_version}, current {version}"
                )
            if item.state != "STOPPED" or item.enabled or instance_id in self._sessions:
                raise RuntimeError("Конфигурацию можно менять только у остановленного драйвера")
            item.config = safe_config
            item.updated_at = _now()
            new_version = self.core.repository.save(item, expected_version=version)
            self.core.audit.append(actor_id="local-engineer", action="driver.instance_config_updated",
                resource_type="driver_instance", resource_id=instance_id,
                details={"driver_id": item.driver_id, "config_keys": sorted(safe_config)})
            return {"id": instance_id, "version": new_version, "state": "STOPPED",
                    "config": dict(item.config), "field_write_enabled": False}

    def _load(self, instance_id: str):
        item, version = self.core.repository.get(instance_id, DriverInstance)
        return item, version

    def _save_state(self, item: DriverInstance, version: int, state: str, enabled: bool) -> None:
        item.state = state
        item.enabled = enabled
        item.updated_at = _now()
        self.core.repository.save(item, expected_version=version)

    def start_instance(self, instance_id: str, *, poll_interval_seconds: float | None = None) -> dict:
        # Serialize driver and scheduler lifecycle against stop/close operations.
        with self._scheduler_lifecycle_lock:
            with self.core._lock:
                self.core._ensure_open()
                result = self._start_instance_unlocked(
                    instance_id, poll_interval_seconds=poll_interval_seconds
                )
            # Start the shared scheduler only after releasing the driver registry
            # lock: scheduler callbacks may inspect driver diagnostics.
            try:
                self._point_runtime_scheduler.start()
            except Exception:
                try:
                    self.stop_instance(instance_id)
                except Exception:
                    pass
                raise
            return self.diagnostics(instance_id)

    def _start_instance_unlocked(self, instance_id: str, *, poll_interval_seconds: float | None = None) -> dict:
        with self._lock:
            if instance_id in self._sessions:
                return self.diagnostics(instance_id)
            item, version = self._load(instance_id)
            self._assert_driver_entitlement(item.driver_id)
            factory = self._factories.get(item.driver_id)
            if factory is None:
                raise RuntimeError(f"Для {item.driver_id} runtime adapter factory не зарегистрирована")
            if item.package_trust == "REJECTED":
                raise RuntimeError("Пакет драйвера помечен как REJECTED")
            item.runtime_generation += 1
            self._save_state(item, version, "STARTING", True)
            version += 1
            adapter = None
            session = None
            try:
                adapter = factory(self.core, item)
                interval = float(poll_interval_seconds if poll_interval_seconds is not None
                                 else item.config.get("poll_interval_seconds", 5.0))
                session = PollingSession(adapter, interval, name=f"avic-{item.driver_id}-{item.id[:8]}")
                session.start()
                self._adapters[instance_id] = adapter
                self._sessions[instance_id] = session
                item.state = "RUNNING"
                item.enabled = True
                item.updated_at = _now()
                self.core.repository.save(item, expected_version=version + 1)
                self.core.audit.append(actor_id="local-engineer", action="driver.instance_started",
                    resource_type="driver_instance", resource_id=instance_id,
                    details={"driver_id": item.driver_id, "poll_interval_seconds": interval})
                return self.diagnostics(instance_id)
            except Exception as exc:
                if session is not None:
                    try:
                        session.stop(timeout=5.0)
                    except Exception:
                        pass
                close = getattr(adapter, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception:
                        pass
                self._sessions.pop(instance_id, None)
                self._adapters.pop(instance_id, None)
                try:
                    failed, current_version = self._load(instance_id)
                    self._save_state(failed, current_version, "ERROR", False)
                except Exception:
                    pass
                self.core.audit.append(actor_id="local-engineer", action="driver.instance_start_failed",
                    resource_type="driver_instance", resource_id=instance_id,
                    outcome="error", details={"error": f"{type(exc).__name__}: {exc}"})
                raise

    def stop_instance(self, instance_id: str, *, timeout: float = 5.0) -> dict:
        with self._scheduler_lifecycle_lock:
            with self._lock:
                session = self._sessions.get(instance_id)
                adapter = self._adapters.get(instance_id)
                item, version = self._load(instance_id)
                # A timeout means the worker may still be inside field I/O. Keep its
                # adapter and registry entries intact; closing underneath it is unsafe.
                if session is not None:
                    session.stop(timeout=timeout)

                close_error = None
                close = getattr(adapter, "close", None)
                if callable(close):
                    try:
                        close()
                    except Exception as exc:
                        close_error = exc

                # Once the worker has stopped, never retain a dead session in the
                # manager: it would make later start_instance() report a stale session.
                self._sessions.pop(instance_id, None)
                self._adapters.pop(instance_id, None)
                stop_scheduler = not self._sessions

            # Do not join the scheduler while holding DriverManager's registry lock:
            # subscriber callbacks may inspect driver diagnostics during a final tick.
            if stop_scheduler:
                try:
                    self._point_runtime_scheduler.stop(timeout=5.0)
                except Exception as exc:
                    close_error = close_error or exc

            with self._lock:
                final_state = "ERROR" if close_error is not None else "STOPPED"
                self._save_state(item, version, final_state, False)
                if close_error is None:
                    self.core.audit.append(actor_id="local-engineer", action="driver.instance_stopped",
                        resource_type="driver_instance", resource_id=instance_id,
                        details={"driver_id": item.driver_id})
                else:
                    self.core.audit.append(actor_id="local-engineer", action="driver.instance_stop_failed",
                        resource_type="driver_instance", resource_id=instance_id, outcome="error",
                        details={"driver_id": item.driver_id,
                                 "error": f"{type(close_error).__name__}: {close_error}"})
                    raise RuntimeError(
                        f"Драйвер {instance_id} остановлен, но адаптер/планировщик не освободил ресурсы"
                    ) from close_error
                return self.diagnostics(instance_id)

    def diagnostics(self, instance_id: str) -> dict:
        item, _ = self._load(instance_id)
        session = self._sessions.get(instance_id)
        adapter = self._adapters.get(instance_id)
        polling = session.diagnostics() if session else {"state": "STOPPED", "worker_alive": False}
        if session is not None:
            effective_state = polling["state"]
        elif item.state in {"STARTING", "RUNNING", "DEGRADED", "STOPPING"}:
            # A persisted active state without an in-process worker is not a live driver.
            effective_state = "ORPHANED"
        else:
            effective_state = item.state
        return {"instance_id": instance_id, "driver_id": item.driver_id,
            "state": effective_state, "persisted_state": item.state,
            "enabled": effective_state in {"STARTING", "RUNNING", "DEGRADED", "STOPPING"},
            "field_read_enabled": session is not None and effective_state in {"RUNNING", "DEGRADED"},
            "field_write_enabled": False,
            "polling": polling,
            "point_runtime_scheduler": self._point_runtime_scheduler.diagnostics(),
            "runtime_generation": int(item.runtime_generation),
            "adapter": adapter.diagnostics() if adapter and callable(getattr(adapter, "diagnostics", None)) else None}

    def stop_station(self, station_id: str) -> dict:
        """Stop every driver owned by a station before that station is taken offline."""
        # Runtime may register a station before its engineering inventory record
        # exists (bootstrap and isolated runtime workflows). Shutdown is scoped by
        # DriverInstance.station_id and must remain safe in that case.
        rows = self.core.repository.list_records(entity_type="DriverInstance", station_id=station_id)
        stopped: list[str] = []
        failures: list[tuple[str, Exception]] = []
        for row in rows:
            instance_id = row["entity_id"]
            payload = row["payload"]
            if instance_id not in self._sessions and payload.get("state") == "STOPPED":
                continue
            try:
                self.stop_instance(instance_id)
                stopped.append(instance_id)
            except Exception as exc:
                failures.append((instance_id, exc))
        if failures:
            ids = ", ".join(instance_id for instance_id, _ in failures)
            raise RuntimeError(f"Не удалось остановить драйверы станции {station_id}: {ids}") from failures[0][1]
        return {"station_id": station_id, "stopped_instance_ids": stopped, "failures": []}

    def stop_all(self) -> None:
        failures = []
        with self._lock:
            ids = list(self._sessions)
        for instance_id in ids:
            try:
                self.stop_instance(instance_id)
            except Exception as exc:
                failures.append((instance_id, exc))
        if failures:
            raise RuntimeError(f"Не удалось остановить драйверы: {', '.join(i for i, _ in failures)}") from failures[0][1]

    def get_instance(self, instance_id: str):
        row = self.core.repository.get_record(instance_id)
        if row["entity_type"] != "DriverInstance":
            raise ValueError("Объект не является экземпляром драйвера")
        p = row["payload"]
        runtime = self.diagnostics(instance_id)
        return {"id": row["entity_id"], "name": row["name"], "station_id": p["station_id"],
            "driver_id": p["driver_id"], "protocol": p["protocol"], "state": runtime["state"],
            "persisted_state": p["state"], "enabled": runtime["enabled"],
            "package_trust": p["package_trust"], "config": p.get("config", {}),
            "version": int(row["version"]), "runtime_generation": int(p.get("runtime_generation", 0)),
            "field_io_enabled": False, "field_read_enabled": runtime["field_read_enabled"],
            "field_write_enabled": False, "start_supported": p["driver_id"] in self._factories}
