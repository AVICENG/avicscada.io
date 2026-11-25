from __future__ import annotations

from avic_core.repository.sqlite_repository import EntityNotFound


class EngineeringWorkflowService:
    """Read-only readiness assessment across the real station engineering artifacts.

    It deliberately does not infer that discovery, commissioning, publishing or field
    control happened. Every stage is derived from persisted station-scoped records.
    """

    def __init__(self, core):
        self.core = core

    def inspect(self, station_id: str) -> dict:
        station = self.core.repository.get_record(station_id)
        if station["entity_type"] != "Station":
            raise ValueError("Целевой объект не является станцией")

        def rows(kind: str):
            return self.core.repository.list_records(entity_type=kind, station_id=station_id)

        networks = rows("PhysicalNetwork")
        channels = rows("ProtocolChannel")
        drivers = rows("DriverInstance")
        devices = rows("Device")
        device_ids = {d["entity_id"] for d in devices}
        points = [r for r in self.core.repository.list_records(entity_type="Point")
                  if r["payload"].get("device_id") in device_ids]
        fbd_docs = rows("LogicDocument")
        graphics_docs = rows("GraphicDocument")

        driver_by_id = {r["entity_id"]: r for r in drivers}
        driver_issues = []
        for device in devices:
            driver_id = device["payload"].get("driver_instance_id")
            driver = driver_by_id.get(driver_id)
            if not driver:
                driver_issues.append({"code": "DEVICE_DRIVER_MISSING", "object_id": device["entity_id"],
                                      "message": f"Устройство «{device['name']}» не связано с драйвером"})
                continue
            cfg = driver["payload"].get("configuration") or {}
            if cfg.get("mode") != "read_only":
                driver_issues.append({"code": "DRIVER_MODE_UNSAFE", "object_id": driver["entity_id"],
                                      "message": f"Драйвер «{driver['name']}» не имеет явного режима read_only"})
            if driver["payload"].get("state") not in {"STOPPED", "CONFIGURED"}:
                driver_issues.append({"code": "DRIVER_STATE_UNEXPECTED", "object_id": driver["entity_id"],
                                      "message": f"Драйвер «{driver['name']}» имеет неподдерживаемое состояние"})

        fbd_doc_ids = {d["entity_id"] for d in fbd_docs}
        fbd_nodes = [r for r in self.core.repository.list_records(entity_type="LogicNode")
                     if r["payload"].get("document_id") in fbd_doc_ids]
        fbd_links = [r for r in self.core.repository.list_records(entity_type="LogicLink")
                     if r["payload"].get("document_id") in fbd_doc_ids]
        graphics_doc_ids = {d["entity_id"] for d in graphics_docs}
        graphics_elements = [r for r in self.core.repository.list_records(entity_type="GraphicElement")
                             if r["payload"].get("document_id") in graphics_doc_ids]
        graphic_element_ids = {e["entity_id"] for e in graphics_elements}
        point_bindings = [r for r in self.core.repository.list_records(entity_type="PointBinding")
                          if r["payload"].get("element_id") in graphic_element_ids]
        logic_bindings = [r for r in self.core.repository.list_records(entity_type="LogicGraphicsBinding")
                          if r["payload"].get("graphic_element_id") in graphic_element_ids]

        network_ids = {r["entity_id"] for r in networks}
        network_issues = []
        for channel in channels:
            network_id = channel["payload"].get("network_id")
            if network_id not in network_ids:
                network_issues.append({"code": "CHANNEL_NETWORK_MISSING", "object_id": channel["entity_id"],
                                       "message": f"Канал «{channel['name']}» не связан с физической сетью этой станции"})
        for network in networks:
            if not network["payload"].get("interface_id"):
                network_issues.append({"code": "NETWORK_INTERFACE_MISSING", "object_id": network["entity_id"],
                                       "message": f"У сети «{network['name']}» не выбран сетевой интерфейс"})

        stages = [
            self._stage("network", "Сеть и каналы", bool(networks) and bool(channels) and not network_issues,
                        {"networks": len(networks), "protocol_channels": len(channels), "issues": len(network_issues)},
                        "Создать физическую сеть, выбрать интерфейс и добавить протокольный канал", network_issues),
            self._stage("drivers", "Драйверы и устройства", bool(devices) and not driver_issues,
                        {"drivers": len(drivers), "devices": len(devices), "issues": len(driver_issues)},
                        "Выполнить обнаружение и импортировать устройство", driver_issues),
            self._stage("points", "Point Manager", bool(points), {"points": len(points)},
                        "Проверить и импортировать выбранные точки"),
            self._stage("logic", "FBD / Wiresheet", bool(fbd_docs) and bool(fbd_nodes),
                        {"diagrams": len(fbd_docs), "blocks": len(fbd_nodes), "links": len(fbd_links)},
                        "Создать FBD-схему, добавить блоки и проверить связи"),
            self._stage("graphics", "Мнемосхемы / PX", bool(graphics_docs) and bool(graphics_elements),
                        {"pages": len(graphics_docs), "symbols": len(graphics_elements),
                         "point_bindings": len(point_bindings), "logic_bindings": len(logic_bindings)},
                        "Создать мнемосхему и привязать точки или FBD-выходы"),
        ]
        ready = sum(1 for s in stages if s["complete"])
        return {"station_id": station_id, "station_name": station["name"], "stages": stages,
                "completed_stages": ready, "total_stages": len(stages),
                "completion_percent": round(ready * 100 / len(stages)),
                "engineering_ready": ready == len(stages),
                "publish_ready": False,
                "publish_blockers": ["В DEV56 нет production runtime deploy/publish и приёмочных испытаний OT"],
                "safety": {"field_writes_enabled": False, "driver_autostart": False,
                           "simulation_is_offline": True}}

    @staticmethod
    def _stage(stage_id, title, complete, counts, next_action, issues=None):
        return {"id": stage_id, "title": title, "complete": bool(complete), "counts": counts,
                "next_action": None if complete else next_action, "issues": issues or []}
