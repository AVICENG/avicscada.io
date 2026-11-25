from __future__ import annotations

from collections import defaultdict
from typing import Any


class EngineeringTreeService:
    """Persistent Project → Station → Physical Network → Protocol → Device → Point projection."""

    def __init__(self, core):
        self.core = core

    @staticmethod
    def _fbd_point_provenance(point: dict[str, Any], page_by_id: dict[str, dict], module_by_id: dict[str, tuple[dict, dict]]) -> dict[str, Any]:
        source = point.get("source") if isinstance(point.get("source"), dict) else {}
        page_id = str(source.get("pageId") or "")
        module_id = str(source.get("moduleId") or "")
        page = page_by_id.get(page_id, {})
        pair = module_by_id.get(module_id)
        module = pair[1] if pair else {}
        page_code = str(page.get("code") or page.get("name") or "P?")
        module_no = source.get("moduleNo", module.get("no"))
        module_tag = str(module.get("tag") or source.get("moduleTag") or "")
        module_type = str(module.get("type") or source.get("moduleType") or "BLOCK")
        port_index = source.get("portIndex")
        try:
            output_number = int(port_index) + 1 if port_index is not None else None
        except (TypeError, ValueError):
            output_number = None
        port_name = str(source.get("portName") or (module.get("outs", [])[int(port_index)].get("name") if output_number and isinstance(module.get("outs"), list) and len(module.get("outs", [])) >= output_number and isinstance(module.get("outs", [])[int(port_index)], dict) else "OUT"))
        owner = module_tag or (f"{module_type}#{module_no}" if module_no is not None else module_type)
        label = f"{page_code} · {owner} · OUT{output_number if output_number is not None else '?'} ({port_name})"
        return {"page_id": page_id or None, "page_code": page_code, "module_id": module_id or None,
                "module_no": module_no, "module_tag": module_tag or None, "module_type": module_type,
                "output_index": port_index, "output_number": output_number, "output_name": port_name,
                "label": label, "resolved": bool(page and module)}

    def build(self, *, include_archived: bool = False) -> dict[str, Any]:
        records = self.core.repository.list_records()
        runtime_by_id = {}
        try:
            runtime_by_id = {item.point_id: item for item in self.core.point_runtime.snapshot()}
        except Exception:
            # The navigator remains available during a Runtime subsystem fault;
            # values will be marked from their persisted quality below.
            runtime_by_id = {}
        by_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for record in records:
            by_type[record["entity_type"]].append(record)

        stations_by_project: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for station in by_type.get("Station", []):
            payload = station.get("payload", {})
            if include_archived or not payload.get("archived", False):
                stations_by_project[payload.get("project_id", "")].append(station)

        devices_by_station: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for device in by_type.get("Device", []):
            devices_by_station[device.get("payload", {}).get("station_id", "")].append(device)
        points_by_device: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for point in by_type.get("Point", []):
            points_by_device[point.get("payload", {}).get("device_id", "")].append(point)
        networks_by_station: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for network in by_type.get("PhysicalNetwork", []):
            networks_by_station[network.get("payload", {}).get("station_id", "")].append(network)
        channels_by_network: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for channel in by_type.get("ProtocolChannel", []):
            channels_by_network[channel.get("payload", {}).get("network_id", "")].append(channel)

        fbd_by_station: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for document in by_type.get("FBDStudioDocument", []):
            payload = document.get("payload", {})
            data = payload.get("data", {}) if isinstance(payload, dict) else {}
            pages = data.get("pages", []) if isinstance(data, dict) else []
            points = data.get("fbdPoints", []) if isinstance(data, dict) else []
            # Resolve each exported FBD point back to its exact owning block/output.
            # Keep the raw source identity as well: display labels are not identities.
            page_by_id = {str(page.get("id", "")): page for page in pages if isinstance(page, dict)}
            module_by_id = {}
            for page in pages:
                if not isinstance(page, dict):
                    continue
                for module in page.get("modules", []) if isinstance(page.get("modules", []), list) else []:
                    if isinstance(module, dict):
                        module_by_id[str(module.get("id", ""))] = (page, module)
            fbd_by_station[str(payload.get("station_id") or document.get("station_id") or "")].append({
                "id": document["entity_id"], "type": "FBDProject", "name": document["name"],
                "revision": document.get("version", 0), "updated_at": document.get("updated_at"),
                "pages": [{"id": str(page.get("id", "")), "code": str(page.get("code") or f"P{index + 1}"),
                           "name": str(page.get("name") or "Untitled"),
                           "module_count": len(page.get("modules", [])) if isinstance(page.get("modules", []), list) else 0}
                          for index, page in enumerate(pages) if isinstance(page, dict)],
                "points": [{"id": str(point.get("id", "")), "tag": str(point.get("tag") or ""),
                            "name": str(point.get("name") or "Без названия"),
                            "path": str(point.get("path") or ""),
                            "native_identity": str(point.get("native_identity") or ""),
                            "symbolic_address": str(point.get("symbolic_address") or ""),
                            "data_type": str(point.get("dataType") or point.get("data_type") or "analog"),
                            "direction": str(point.get("direction") or "output"),
                            "source": point.get("source") if isinstance(point.get("source"), dict) else {},
                            "provenance": self._fbd_point_provenance(point, page_by_id, module_by_id),
                            "value": (runtime_by_id[str(point.get("id"))].value if str(point.get("id")) in runtime_by_id else None),
                            "unit": str(point.get("unit") or ""),
                            "quality": (runtime_by_id[str(point.get("id"))].quality if str(point.get("id")) in runtime_by_id else "UNCERTAIN"),
                            "timestamp": (runtime_by_id[str(point.get("id"))].timestamp.isoformat() if str(point.get("id")) in runtime_by_id and runtime_by_id[str(point.get("id"))].timestamp else None),
                            "license_status": str((point.get("license") or {}).get("status") or "pending_core_registration")}
                           for point in points if isinstance(point, dict)],
            })

        projects = []
        for project in by_type.get("Project", []):
            if not include_archived and project.get("payload", {}).get("archived", False):
                continue
            station_nodes = []
            for station in sorted(stations_by_project.get(project["entity_id"], []), key=lambda x: x["name"].casefold()):
                station_id = station["entity_id"]
                devices = devices_by_station.get(station_id, [])
                configured = {n["entity_id"]: n for n in networks_by_station.get(station_id, [])}
                # Keep legacy imported devices visible even if they predate persistent network objects.
                for d in devices:
                    network_id = str(d.get("payload", {}).get("network_id") or "unassigned")
                    if network_id not in configured:
                        configured[network_id] = {"entity_id": network_id, "name": network_id,
                            "payload": {"station_id": station_id, "legacy": True}}
                network_nodes = []
                for network_id, network in sorted(configured.items(), key=lambda x: x[1]["name"].casefold()):
                    network_payload = network.get("payload", {})
                    protocol_devices: dict[str, list[dict[str, Any]]] = defaultdict(list)
                    for device in devices:
                        dp = device.get("payload", {})
                        if str(dp.get("network_id") or "unassigned") != network_id:
                            continue
                        protocol = str(dp.get("protocol") or "unknown").lower()
                        point_nodes = []
                        for p in sorted(points_by_device.get(device["entity_id"], []), key=lambda x: x["name"].casefold()):
                            live = runtime_by_id.get(p["entity_id"])
                            pp = p.get("payload", {})
                            point_nodes.append({
                                "id": p["entity_id"], "type": "Point", "name": p["name"],
                                "native_identity": pp.get("native_identity"), "source_ref": pp.get("source_ref"),
                                "object_type": pp.get("object_type"), "data_type": pp.get("data_type"),
                                "direction": getattr(pp.get("direction", "input"), "value", pp.get("direction", "input")),
                                "value": live.value if live else pp.get("value"),
                                "unit": live.unit if live else pp.get("unit", ""),
                                "timestamp": live.timestamp.isoformat() if live and live.timestamp else pp.get("timestamp"),
                                "quality": live.quality if live else getattr(pp.get("quality", "UNCERTAIN"), "value", pp.get("quality", "UNCERTAIN")),
                            })
                        protocol_devices[protocol].append({
                            "id": device["entity_id"], "type": "Device", "name": device["name"],
                            "address": dp.get("address"), "manufacturer": dp.get("manufacturer"),
                            "model": dp.get("model"), "protocol": protocol, "network_id": network_id,
                            "points": [{**point, "protocol": protocol} for point in point_nodes],
                        })
                    configured_channels = channels_by_network.get(network_id, [])
                    protocol_names = set(protocol_devices)
                    protocol_names.update(str(c.get("payload", {}).get("protocol") or "unknown").lower() for c in configured_channels)
                    channel_nodes = []
                    for protocol in sorted(protocol_names):
                        channel_record = next((c for c in configured_channels if str(c.get("payload", {}).get("protocol", "")).lower() == protocol), None)
                        channel_nodes.append({
                            "id": channel_record["entity_id"] if channel_record else f"{station_id}:{network_id}:{protocol}",
                            "type": "ProtocolChannel", "name": protocol.upper(), "protocol": protocol,
                            "configured": channel_record is not None,
                            "devices": sorted(protocol_devices.get(protocol, []), key=lambda x: x["name"].casefold()),
                        })
                    network_nodes.append({
                        "id": network_id, "type": "PhysicalNetwork", "name": network["name"],
                        "configured": not network_payload.get("legacy", False),
                        "interface_id": network_payload.get("interface_id"),
                        "interface_name": network_payload.get("interface_name"),
                        "ipv4": network_payload.get("ipv4"), "subnet_cidr": network_payload.get("subnet_cidr"),
                        "addressing_mode": network_payload.get("addressing_mode", "auto"),
                        "station_ipv4": network_payload.get("station_ipv4") or network_payload.get("ipv4"),
                        "gateway_ipv4": network_payload.get("gateway_ipv4"),
                        "dns_servers": network_payload.get("dns_servers", []),
                        "deployment_binding": "BOUND" if network_payload.get("interface_id") else "PLANNED",
                        "channels": channel_nodes,
                    })
                device_count = len(devices)
                point_count = sum(len(points_by_device.get(d["entity_id"], [])) for d in devices)
                from avic_core.web_pages.models import WebPageNode
                web_nodes = {}
                for web_row in self.core.repository.list_records(entity_type="WebPageNode", station_id=station_id):
                    web_node, web_version = self.core.repository.get(web_row["entity_id"], WebPageNode)
                    web_nodes[web_node.id] = {"id": web_node.id, "type": "WebPageNode", "kind": web_node.node_kind,
                        "name": web_node.name, "slug": web_node.slug, "published": web_node.published,
                        "revision": web_version, "children": []}
                web_roots = []
                for web_row in self.core.repository.list_records(entity_type="WebPageNode", station_id=station_id):
                    web_node = web_nodes[web_row["entity_id"]]
                    parent_id = self.core.repository.get(web_node["id"], WebPageNode)[0].parent_id
                    if parent_id in web_nodes:
                        web_nodes[parent_id]["children"].append(web_node)
                    else:
                        web_roots.append(web_node)
                def sort_web(items):
                    items.sort(key=lambda item: item["name"].casefold())
                    for item in items: sort_web(item["children"])
                sort_web(web_roots)
                station_nodes.append({"id": station_id, "type": "Station", "name": station["name"],
                    "networks": network_nodes, "device_count": device_count, "point_count": point_count,
                    "fbd_projects": sorted(fbd_by_station.get(station_id, []), key=lambda x: x["name"].casefold()),
                    "repository": {"id": "avic.repository", "type": "Repository", "name": "Репозиторий",
                        "parent_type": "Station", "parent_id": station_id,
                        "owns_core_objects": False, "core_authoritative": True,
                        "children": [
                            {"id": "avic.repository.web_application", "type": "WebApplication", "name": "Web Application", "children": web_roots},
                            {"id": "avic.repository.graphics", "type": "GraphicsRepository", "name": "Graphics", "children": [
                                {"id": "avic.repository.graphics.pages", "type": "GraphicsPages", "name": "Pages", "children": []},
                                {"id": "avic.repository.graphics.components", "type": "GraphicsComponents", "name": "Components", "children": []},
                                {"id": "avic.repository.graphics.symbols", "type": "GraphicsSymbols", "name": "Symbols", "children": []},
                                {"id": "avic.repository.graphics.assets", "type": "GraphicsAssets", "name": "Assets", "children": []},
                                {"id": "avic.repository.graphics.templates", "type": "GraphicsTemplates", "name": "Templates", "children": []}
                            ]},
                            {"id": "avic.repository.documentation", "type": "Documentation", "name": "Documentation", "children": []}
                        ]}})
            projects.append({"id": project["entity_id"], "type": "Project", "name": project["name"], "stations": station_nodes})
        projects.sort(key=lambda x: x["name"].casefold())
        return {"schema_version": 1, "read_only": True, "discovery_is_separate": True,
            "projects": projects,
            "counts": {"projects": len(projects), "stations": sum(len(p["stations"]) for p in projects),
                "devices": sum(s["device_count"] for p in projects for s in p["stations"]),
                "points": sum(s["point_count"] for p in projects for s in p["stations"])}}
