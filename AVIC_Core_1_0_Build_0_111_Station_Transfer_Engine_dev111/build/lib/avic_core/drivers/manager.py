"""Persistent driver inventory and safe lifecycle manager (no field I/O)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4
from avic_core.drivers.catalog import list_builtin_drivers
from avic_core.repository.sqlite_repository import EntityNotFound


def _now(): return datetime.now(timezone.utc)

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
        UUID(self.id); UUID(self.station_id)
        if not self.name.strip() or not self.driver_id.strip() or not self.protocol.strip():
            raise ValueError("Имя, идентификатор драйвера и протокол обязательны")
        if self.state != "STOPPED" or self.enabled:
            raise ValueError("Новый экземпляр драйвера обязан оставаться остановленным")
        if self.package_trust not in {"BUILTIN", "VERIFIED", "UNVERIFIED", "REJECTED"}:
            raise ValueError("Недопустимый статус доверия пакету")

class DriverManagerService:
    """Catalog + persistent inventory. It deliberately cannot start drivers or write to devices."""
    def __init__(self, core): self.core = core

    def catalog(self):
        return [{"driver_id":x.driver_id,"name":x.display_name,"protocol":x.protocol,
                 "lifecycle":x.lifecycle.value,"read_supported":x.read_supported,
                 "write_supported":False,"discovery_supported":x.discovery_supported,
                 "notes":x.notes} for x in list_builtin_drivers()]

    def list_instances(self, station_id: str):
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station": raise ValueError("Целевой объект не является станцией")
        result=[]
        for row in self.core.repository.list_records(entity_type="DriverInstance", station_id=station_id):
            p=row["payload"]
            result.append({"id":row["entity_id"],"name":row["name"],"driver_id":p["driver_id"],
                "protocol":p["protocol"],"version":p.get("version",""),"state":p["state"],
                "enabled":p["enabled"],"package_trust":p["package_trust"],"config":p.get("config",{})})
        return result

    def create_instance(self, station_id: str, driver_id: str, name: str, config: dict | None = None):
        station=self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station": raise ValueError("Целевой объект не является станцией")
        entry=next((x for x in list_builtin_drivers() if x.driver_id == driver_id),None)
        if entry is None: raise ValueError("Драйвер отсутствует в доверенном встроенном каталоге")
        if entry.lifecycle.value == "planned": raise ValueError("Драйвер пока не реализован")
        if config is not None and not isinstance(config,dict): raise ValueError("Конфигурация должна быть объектом")
        # Config is inventory metadata only. No credentials, sockets, polling or writes are initiated.
        safe_config=dict(config or {})
        forbidden={"password","secret","token","private_key","credential"}
        if any(str(k).casefold() in forbidden for k in safe_config):
            raise ValueError("Секреты нельзя хранить в конфигурации экземпляра; используйте SecretStore")
        item=DriverInstance(name=name,station_id=station_id,driver_id=entry.driver_id,
            protocol=entry.protocol,config=safe_config)
        self.core.repository.save(item)
        self.core.audit.append(actor_id="local-engineer",action="driver.instance_created",
            resource_type="driver_instance",resource_id=item.id,
            details={"station_id":station_id,"driver_id":driver_id,"state":"STOPPED"})
        return {"id":item.id,"name":item.name,"station_id":station_id,"driver_id":driver_id,
            "protocol":item.protocol,"state":"STOPPED","enabled":False,"package_trust":"BUILTIN",
            "field_io_enabled":False}

    def get_instance(self, instance_id: str):
        row=self.core.repository.get_record(instance_id)
        if row["entity_type"] != "DriverInstance": raise ValueError("Объект не является экземпляром драйвера")
        p=row["payload"]
        return {"id":row["entity_id"],"name":row["name"],"station_id":p["station_id"],
            "driver_id":p["driver_id"],"protocol":p["protocol"],"state":p["state"],
            "enabled":p["enabled"],"package_trust":p["package_trust"],"config":p.get("config",{}),
            "field_io_enabled":False,"start_supported":False}
