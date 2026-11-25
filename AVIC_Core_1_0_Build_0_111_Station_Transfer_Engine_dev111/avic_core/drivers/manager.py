"""Persistent driver inventory and explicitly controlled runtime lifecycle."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import RLock
from typing import Callable, Any
from uuid import UUID, uuid4

from avic_core.drivers.catalog import list_builtin_drivers
from avic_core.drivers.polling import PollingSession
from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.network.modbus_tcp import ModbusTcpClient
from avic_core.network.bacnet_ip import BacnetIpClient
from avic_core.network.contracts import BacnetIpNetworkConfig, DiscoveryPolicy


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
        if self.package_trust not in {"BUILTIN", "VERIFIED", "UNVERIFIED", "REJECTED"}:
            raise ValueError("Недопустимый статус доверия пакету")


class DriverManagerService:
    """Owns explicit read-only adapter sessions; no implicit field I/O at Core startup."""

    _SECRET_KEYS = {"password", "secret", "token", "private_key", "credential", "client_secret"}

    def __init__(self, core):
        self.core = core
        self._lock = RLock()
        self._factories: dict[str, Callable[[Any, DriverInstance], Any]] = {
            "modbus-tcp": self._build_modbus_adapter,
            "bacnet-ip": self._build_bacnet_adapter,
        }
        self._sessions: dict[str, PollingSession] = {}
        self._adapters: dict[str, Any] = {}

    @classmethod
    def _reject_secrets(cls, value: Any, path: str = "config") -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).casefold() in cls._SECRET_KEYS:
                    raise ValueError(f"Секреты нельзя хранить в конфигурации экземпляра ({path}.{key}); используйте SecretStore")
                cls._reject_secrets(item, f"{path}.{key}")
        elif isinstance(value, (list, tuple)):
            for index, item in enumerate(value):
                cls._reject_secrets(item, f"{path}[{index}]")

    def register_adapter_factory(self, driver_id: str, factory: Callable[[Any, DriverInstance], Any]) -> None:
        if driver_id not in {item.driver_id for item in list_builtin_drivers()}:
            raise ValueError("Драйвер отсутствует во встроенном каталоге")
        if not callable(factory):
            raise TypeError("factory must be callable")
        with self._lock:
            if self._sessions:
                raise RuntimeError("Нельзя менять factory во время активных сессий драйверов")
            self._factories[driver_id] = factory

    def _build_modbus_adapter(self, core, instance: DriverInstance):
        cfg = dict(instance.config)
        allowed = {"host", "port", "unit_id", "timeout", "poll_interval_seconds", "bindings"}
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры Modbus TCP: {sorted(unknown)}")
        if not cfg.get("host") or not isinstance(cfg.get("bindings"), list) or not cfg["bindings"]:
            raise ValueError("Для Modbus TCP требуются host и непустой bindings")
        client = ModbusTcpClient(
            cfg["host"], port=int(cfg.get("port", 502)),
            unit_id=int(cfg.get("unit_id", 1)), timeout=float(cfg.get("timeout", 2.0)),
        )
        bindings = [ModbusTcpPointBinding(**item) for item in cfg["bindings"]]
        return ModbusTcpPointAdapter(client, core.point_runtime, instance.id, bindings)

    def _build_bacnet_adapter(self, core, instance: DriverInstance):
        cfg = dict(instance.config)
        allowed = {"network_id", "interface_name", "local_address", "subnet_cidr",
                   "udp_port", "device_instance", "timeout", "poll_interval_seconds", "bindings"}
        unknown = set(cfg) - allowed
        if unknown:
            raise ValueError(f"Неизвестные параметры BACnet/IP: {sorted(unknown)}")
        required = ("network_id", "interface_name", "local_address", "subnet_cidr")
        if any(not cfg.get(key) for key in required) or not isinstance(cfg.get("bindings"), list) or not cfg["bindings"]:
            raise ValueError("Для BACnet/IP требуются параметры сети и непустой bindings")
        network = BacnetIpNetworkConfig(
            network_id=cfg["network_id"], interface_name=cfg["interface_name"],
            local_address=cfg["local_address"], subnet_cidr=cfg["subnet_cidr"],
            udp_port=int(cfg.get("udp_port", 47808)),
            device_instance=cfg.get("device_instance"),
        )
        client = BacnetIpClient(network, DiscoveryPolicy(
            request_timeout_seconds=float(cfg.get("timeout", 3.0)),
        ))
        bindings = []
        for raw in cfg["bindings"]:
            item = dict(raw)
            if "address" in item:
                item["address"] = tuple(item["address"])
            bindings.append(BacnetIpPointBinding(**item))
        return BacnetIpPointAdapter(client, core.point_runtime, instance.id, bindings)

    def catalog(self):
        return [{"driver_id": x.driver_id, "name": x.display_name, "protocol": x.protocol,
                 "lifecycle": x.lifecycle.value, "read_supported": x.read_supported,
                 "write_supported": False, "discovery_supported": x.discovery_supported,
                 "runtime_start_supported": x.driver_id in self._factories,
                 "notes": x.notes} for x in list_builtin_drivers()]

    def list_instances(self, station_id: str):
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        result = []
        for row in self.core.repository.list_records(entity_type="DriverInstance", station_id=station_id):
            p = row["payload"]
            result.append({"id": row["entity_id"], "name": row["name"], "driver_id": p["driver_id"],
                "protocol": p["protocol"], "version": p.get("version", ""), "state": p["state"],
                "enabled": p["enabled"], "package_trust": p["package_trust"], "config": p.get("config", {})})
        return result

    def create_instance(self, station_id: str, driver_id: str, name: str, config: dict | None = None):
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")
        entry = next((x for x in list_builtin_drivers() if x.driver_id == driver_id), None)
        if entry is None:
            raise ValueError("Драйвер отсутствует в доверенном встроенном каталоге")
        if entry.lifecycle.value == "planned":
            raise ValueError("Драйвер пока не реализован")
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

    def _load(self, instance_id: str):
        item, version = self.core.repository.get(instance_id, DriverInstance)
        return item, version

    def _save_state(self, item: DriverInstance, version: int, state: str, enabled: bool) -> None:
        item.state = state
        item.enabled = enabled
        item.updated_at = _now()
        self.core.repository.save(item, expected_version=version)

    def start_instance(self, instance_id: str, *, poll_interval_seconds: float | None = None) -> dict:
        with self._lock:
            if instance_id in self._sessions:
                return self.diagnostics(instance_id)
            item, version = self._load(instance_id)
            factory = self._factories.get(item.driver_id)
            if factory is None:
                raise RuntimeError(f"Для {item.driver_id} runtime adapter factory не зарегистрирована")
            if item.package_trust == "REJECTED":
                raise RuntimeError("Пакет драйвера помечен как REJECTED")
            self._save_state(item, version, "STARTING", True)
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
        with self._lock:
            session = self._sessions.get(instance_id)
            adapter = self._adapters.get(instance_id)
            item, version = self._load(instance_id)
            if session is not None:
                session.stop(timeout=timeout)
            close = getattr(adapter, "close", None)
            if callable(close):
                close()
            self._sessions.pop(instance_id, None)
            self._adapters.pop(instance_id, None)
            self._save_state(item, version, "STOPPED", False)
            self.core.audit.append(actor_id="local-engineer", action="driver.instance_stopped",
                resource_type="driver_instance", resource_id=instance_id,
                details={"driver_id": item.driver_id})
            return self.diagnostics(instance_id)

    def diagnostics(self, instance_id: str) -> dict:
        item, _ = self._load(instance_id)
        session = self._sessions.get(instance_id)
        adapter = self._adapters.get(instance_id)
        return {"instance_id": instance_id, "driver_id": item.driver_id,
            "state": item.state, "enabled": item.enabled,
            "polling": session.diagnostics() if session else {"state": "STOPPED", "worker_alive": False},
            "adapter": adapter.diagnostics() if adapter and callable(getattr(adapter, "diagnostics", None)) else None}

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
        return {"id": row["entity_id"], "name": row["name"], "station_id": p["station_id"],
            "driver_id": p["driver_id"], "protocol": p["protocol"], "state": p["state"],
            "enabled": p["enabled"], "package_trust": p["package_trust"], "config": p.get("config", {}),
            "field_io_enabled": False, "start_supported": p["driver_id"] in self._factories}
