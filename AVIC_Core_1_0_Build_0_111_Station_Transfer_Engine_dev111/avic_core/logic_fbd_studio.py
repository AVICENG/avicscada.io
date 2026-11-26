"""Server-owned persistence for AVIC FBD Studio authoring documents.

The Studio document preserves the complete editor graph. It is deliberately
separate from executable Core LogicDocument compilation until a validated
compiler adapter has accepted every block and connection.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from avic_core.domain.models import BaseObject
from avic_core.repository.sqlite_repository import EntityNotFound


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class FBDStudioDocument(BaseObject):
    station_id: str = ""
    data: dict[str, Any] = field(default_factory=dict)


class FBDStudioService:
    MAX_BYTES = 8 * 1024 * 1024
    MAX_PAGES = 250
    MAX_MODULES = 5000
    MAX_LINKS = 10000

    def __init__(self, core):
        self.core = core

    @staticmethod
    def _nonnegative_index(value: Any, label: str) -> int:
        if isinstance(value, bool):
            raise ValueError(f"{label} must be a non-negative integer")
        if isinstance(value, int):
            index = value
        elif isinstance(value, str) and value.isdecimal():
            index = int(value)
        else:
            raise ValueError(f"{label} must be a non-negative integer")
        if index < 0:
            raise ValueError(f"{label} must be a non-negative integer")
        return index

    def _station(self, station_id: str):
        row = self.core.repository.get_record(station_id)
        if row["entity_type"] != "Station":
            raise ValueError("FBD Studio document must belong to a Station")
        return row

    @classmethod
    def _validate(cls, data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("FBD Studio data must be an object")
        try:
            encoded = json.dumps(data, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"FBD Studio document is not valid JSON data: {exc}") from exc
        if len(encoded.encode("utf-8")) > cls.MAX_BYTES:
            raise ValueError("FBD Studio document exceeds 8 MiB")
        pages = data.get("pages", [])
        links = data.get("links", [])
        if not isinstance(pages, list) or len(pages) > cls.MAX_PAGES:
            raise ValueError("FBD Studio page count is invalid")
        page_ids: set[str] = set()
        page_names: set[str] = set()
        page_codes: set[str] = set()
        project_module_tags: set[str] = set()
        project_module_ids: set[str] = set()
        for page in pages:
            if not isinstance(page, dict):
                raise ValueError("FBD Studio pages must be objects")
            page_id = str(page.get("id") or "").strip()
            page_name = str(page.get("name") or "").strip().casefold()
            if not page_id or page_id in page_ids:
                raise ValueError("FBD page IDs must be present and unique")
            if not page_name or page_name in page_names:
                raise ValueError("FBD page names must be present and unique within a project")
            page_code = str(page.get("code") or "").strip().casefold()
            if page_code and page_code in page_codes:
                raise ValueError("FBD page codes must be unique within a project")
            page_ids.add(page_id)
            page_names.add(page_name)
            if page_code:
                page_codes.add(page_code)
            modules = page.get("modules", [])
            if not isinstance(modules, list):
                raise ValueError("FBD page modules must be a list")
            module_ids: set[str] = set()
            module_numbers: set[str] = set()
            for module in modules:
                if not isinstance(module, dict):
                    raise ValueError("FBD modules must be objects")
                module_id = str(module.get("id") or "").strip()
                if not module_id or module_id in module_ids or module_id in project_module_ids:
                    raise ValueError("FBD module IDs must be present and unique across the entire project")
                module_ids.add(module_id)
                project_module_ids.add(module_id)
                tag = str(module.get("tag") or "").strip().casefold()
                if tag:
                    if tag in project_module_tags:
                        raise ValueError("FBD module tags must be unique within a project")
                    if not tag.replace("_", "").isalnum():
                        raise ValueError("FBD module tags may contain only letters, digits and underscores")
                    project_module_tags.add(tag)
                number = str(module.get("no") or "").strip()
                if number:
                    if number in module_numbers:
                        raise ValueError("FBD module numbers must be unique within a page")
                    module_numbers.add(number)
                for port_group in ("ins", "outs"):
                    ports = module.get(port_group, [])
                    if not isinstance(ports, list):
                        raise ValueError("FBD module ports must be lists")
                    port_names = [str(port.get("name") or "").strip().casefold()
                                  for port in ports if isinstance(port, dict)]
                    if len(port_names) != len(ports) or any(not name for name in port_names):
                        raise ValueError("FBD ports must have non-empty names")
                    if len(set(port_names)) != len(port_names):
                        raise ValueError("FBD port names must be unique within each direction")
        if not isinstance(links, list) or len(links) > cls.MAX_LINKS:
            raise ValueError("FBD Studio link count is invalid")
        module_count = sum(len(p.get("modules", [])) for p in pages if isinstance(p, dict) and isinstance(p.get("modules", []), list))
        if module_count > cls.MAX_MODULES:
            raise ValueError("FBD Studio module count exceeds limit")

        # Validate every persisted wire on the server, not only when the user compiles.
        page_by_id = {str(page.get("id")): page for page in pages}
        module_index = {
            str(module.get("id")): (str(page.get("id")), module)
            for page in pages for module in page.get("modules", [])
        }
        seen_link_ids: set[str] = set()
        occupied_inputs: set[tuple[str, int]] = set()
        for link_index, link in enumerate(links):
            if not isinstance(link, dict):
                raise ValueError(f"FBD link {link_index} must be an object")
            link_id = str(link.get("id") or "").strip()
            if link_id:
                if link_id in seen_link_ids:
                    raise ValueError("FBD link IDs must be unique within a project")
                seen_link_ids.add(link_id)
            page_id = str(link.get("pageId") or "")
            if page_id not in page_by_id:
                raise ValueError("FBD link must identify an existing page")
            endpoints = []
            for token, direction in ((link.get("from"), "out"), (link.get("to"), "in")):
                parts = str(token or "").split(":")
                if len(parts) != 3 or parts[0] != direction or not parts[1] or not parts[2].isdecimal():
                    raise ValueError("FBD link endpoint has an invalid direction, module UID or port index")
                module_id = parts[1]
                port_index = cls._nonnegative_index(parts[2], "FBD link port index")
                row = module_index.get(module_id)
                if row is None or row[0] != page_id:
                    raise ValueError("FBD link endpoint module must exist on the link page")
                module = row[1]
                if direction == "out":
                    if str(module.get("type") or "") == "TO_CONNECTIVE":
                        raise ValueError("To Connective is a navigation marker and cannot be a wire source")
                    ports = module.get("outs", [])
                else:
                    if str(module.get("type") or "") in {"CONNECTIVE", "TO_CONNECTIVE"}:
                        raise ValueError("FBD wire target must be an executable block input")
                    ports = module.get("ins", [])
                if port_index >= len(ports):
                    raise ValueError("FBD link endpoint port index is outside the module port list")
                endpoints.append((module_id, port_index, ports[port_index]))
            source_module_id, source_port_index, source_port = endpoints[0]
            target_module_id, target_port_index, target_port = endpoints[1]
            target_key = (target_module_id, target_port_index)
            if target_key in occupied_inputs:
                raise ValueError("FBD input port may have only one incoming wire")
            occupied_inputs.add(target_key)
            source_signal = cls._signal_type(source_port.get("type"))
            target_signal = cls._signal_type(target_port.get("type"))
            if source_signal and target_signal and source_signal != "any" and target_signal != "any" and source_signal != target_signal:
                raise ValueError("FBD wire connects incompatible signal types")

        fbd_points = data.get("fbdPoints", [])
        if not isinstance(fbd_points, list):
            raise ValueError("FBD Studio fbdPoints must be a list")
        seen_ids: set[str] = set()
        seen_tags: set[str] = set()
        seen_native: set[str] = set()
        seen_symbols: set[str] = set()
        seen_paths: set[str] = set()
        seen_sources: set[tuple[str, str, str]] = set()
        page_by_id = {str(page.get("id")): page for page in pages}
        for point in fbd_points:
            if not isinstance(point, dict):
                raise ValueError("FBD point must be an object")
            point_id = str(point.get("id") or "").strip()
            if not point_id or point_id in seen_ids:
                raise ValueError("FBD point IDs must be present and unique")
            seen_ids.add(point_id)
            for field, seen, label in (
                ("tag", seen_tags, "FBD point tags"),
                ("native_identity", seen_native, "FBD native identities"),
                ("symbolic_address", seen_symbols, "FBD symbolic addresses"),
                ("path", seen_paths, "FBD point paths"),
            ):
                value = str(point.get(field) or "").strip().casefold()
                if value:
                    if value in seen:
                        raise ValueError(f"{label} must be unique within a project")
                    seen.add(value)
            source = point.get("source") or {}
            if source:
                page_id = str(source.get("pageId") or "")
                module_id = str(source.get("moduleId") or "")
                port_index = cls._nonnegative_index(source.get("portIndex"), "FBD point source portIndex")
                if not page_id or not module_id:
                    raise ValueError("FBD point source must identify page, module and non-negative port index")
                source_page = page_by_id.get(page_id)
                if source_page is None:
                    raise ValueError("FBD point source page does not exist in this project")
                modules = source_page.get("modules", [])
                source_module = next((m for m in modules if isinstance(m, dict) and str(m.get("id")) == module_id), None)
                if source_module is None:
                    raise ValueError("FBD point source module does not exist on the source page")
                outputs = source_module.get("outs", [])
                if not isinstance(outputs, list) or port_index >= len(outputs):
                    raise ValueError("FBD point source output port does not exist")
                port_id = str(source.get("portId") or "")
                if port_id and str(outputs[port_index].get("id") or "") != port_id:
                    raise ValueError("FBD point source port UID does not match its portIndex")
                source_key = (page_id, module_id, port_id or str(port_index))
                if source_key in seen_sources:
                    raise ValueError("Only one exposed FBD point may reference a source output port")
                seen_sources.add(source_key)
        cls._validate_references(data)
        return data

    @staticmethod
    def _signal_type(value: Any) -> str:
        token = str(value or "").strip().casefold()
        return {"num": "float", "analog": "float", "float": "float",
                "digital": "bool", "binary": "bool", "bool": "bool",
                "integer": "int", "int": "int", "string": "string"}.get(token, token)

    @classmethod
    def _validate_references(cls, data: dict[str, Any]) -> None:
        references = data.get("references", [])
        if not isinstance(references, list) or len(references) > cls.MAX_LINKS:
            raise ValueError("FBD Studio references must be a list within the project limit")
        pages = {str(page.get("id")): page for page in data.get("pages", [])}
        modules: dict[str, tuple[str, dict[str, Any]]] = {}
        for page_id, page in pages.items():
            for module in page.get("modules", []):
                modules[str(module.get("id"))] = (page_id, module)

        markers_by_reference: dict[str, list[tuple[str, str, dict[str, Any]]]] = {}
        for module_id, (page_id, module) in modules.items():
            if str(module.get("type") or "") == "TO_CONNECTIVE":
                marker_params = module.get("params") if isinstance(module.get("params"), dict) else {}
                marker_reference_id = str(marker_params.get("referenceId") or "").strip()
                if not marker_reference_id:
                    raise ValueError("FBD To Connective marker must reference a Page Reference")
                markers_by_reference.setdefault(marker_reference_id, []).append((module_id, page_id, module))

        seen_ids: set[str] = set()
        seen_proxies: set[str] = set()
        seen_markers: set[str] = set()
        seen_endpoints: set[tuple[str, str, int, str]] = set()
        for reference in references:
            if not isinstance(reference, dict):
                raise ValueError("FBD references must be objects")
            reference_id = str(reference.get("id") or "").strip()
            source_page_id = str(reference.get("sourcePageId") or "")
            source_module_id = str(reference.get("sourceModuleId") or "")
            target_page_id = str(reference.get("targetPageId") or "")
            proxy_module_id = str(reference.get("proxyModuleId") or "")
            if not reference_id or reference_id in seen_ids:
                raise ValueError("FBD reference IDs must be present and unique")
            seen_ids.add(reference_id)
            if source_page_id not in pages or target_page_id not in pages or source_page_id == target_page_id:
                raise ValueError("FBD reference must connect two different pages in the same project")
            source_row = modules.get(source_module_id)
            proxy_row = modules.get(proxy_module_id)
            if source_row is None or source_row[0] != source_page_id:
                raise ValueError("FBD reference source module does not exist on its source page")
            if proxy_row is None or proxy_row[0] != target_page_id:
                raise ValueError("FBD reference proxy does not exist on its target page")
            source = source_row[1]
            proxy = proxy_row[1]
            if str(source.get("type") or "") in {"CONNECTIVE", "TO_CONNECTIVE"}:
                raise ValueError("FBD reference source must be a real logic block, not a navigation proxy")
            if str(proxy.get("type") or "") != "CONNECTIVE":
                raise ValueError("FBD reference target module must be a CONNECTIVE proxy")
            source_port_index = cls._nonnegative_index(reference.get("sourcePort"), "FBD reference sourcePort")
            source_outputs = source.get("outs", [])
            proxy_outputs = proxy.get("outs", [])
            if source_port_index >= len(source_outputs):
                raise ValueError("FBD reference source output port does not exist")
            if not isinstance(proxy_outputs, list) or len(proxy_outputs) != 1:
                raise ValueError("FBD CONNECTIVE proxy must expose exactly one output")
            source_output = source_outputs[source_port_index]
            proxy_output = proxy_outputs[0]
            source_signal = cls._signal_type(source_output.get("type"))
            proxy_signal = cls._signal_type(proxy_output.get("type"))
            if not source_signal or source_signal != proxy_signal:
                raise ValueError("FBD CONNECTIVE proxy signal type differs from its source output")
            if str(source_output.get("name") or "") != str(proxy_output.get("name") or ""):
                raise ValueError("FBD CONNECTIVE proxy output name differs from its source output")
            proxy_params = proxy.get("params") if isinstance(proxy.get("params"), dict) else {}
            if str(proxy_params.get("referenceId") or "") != reference_id:
                raise ValueError("FBD CONNECTIVE proxy referenceId does not match its reference")
            if proxy.get("ins", []):
                raise ValueError("FBD CONNECTIVE proxy must not expose input ports")
            if proxy_module_id in seen_proxies:
                raise ValueError("Only one FBD reference may own a CONNECTIVE proxy")
            seen_proxies.add(proxy_module_id)
            endpoint = (source_page_id, source_module_id, source_port_index, target_page_id)
            if endpoint in seen_endpoints:
                raise ValueError("Duplicate FBD reference for the same source output and target page")
            seen_endpoints.add(endpoint)

            marker_id = str(reference.get("toModuleId") or "")
            matching_markers = markers_by_reference.get(reference_id, [])
            if len(matching_markers) > 1:
                raise ValueError("FBD reference has more than one To Connective marker")
            if matching_markers:
                actual_marker_id, marker_page_id, marker = matching_markers[0]
                if marker_page_id != source_page_id:
                    raise ValueError("FBD To Connective marker must be on the source page")
                if not marker_id or marker_id != actual_marker_id:
                    raise ValueError("FBD reference toModuleId must identify its To Connective marker")
                marker_inputs = marker.get("ins", [])
                if len(marker_inputs) != 1 or cls._signal_type(marker_inputs[0].get("type")) != source_signal:
                    raise ValueError("FBD To Connective marker input does not match its source signal")
                if marker.get("outs", []):
                    raise ValueError("FBD To Connective marker must not expose output ports")
                seen_markers.add(actual_marker_id)
            elif marker_id:
                raise ValueError("FBD To Connective marker does not exist or does not reference this Page Reference")

        for module_id, (_page_id, module) in modules.items():
            module_type = str(module.get("type") or "")
            if module_type == "CONNECTIVE" and module_id not in seen_proxies:
                raise ValueError("FBD CONNECTIVE proxy has no owning Page Reference")
            if module_type == "TO_CONNECTIVE" and module_id not in seen_markers:
                raise ValueError("FBD To Connective marker has no matching Page Reference")

    @staticmethod
    def _view(doc: FBDStudioDocument, revision: int) -> dict[str, Any]:
        return {"id": doc.id, "name": doc.name, "station_id": doc.station_id,
                "revision": revision, "data": doc.data, "updated_at": doc.updated_at.isoformat(),
                "document_kind": "authoring-only", "runtime_compiled": False}

    def list_for_station(self, station_id: str) -> dict[str, Any]:
        self._station(station_id)
        rows = self.core.repository.list_records(entity_type="FBDStudioDocument", station_id=station_id)
        return {"documents": [{"id": r["entity_id"], "name": r["name"], "revision": r["version"],
                               "updated_at": r["updated_at"]} for r in rows]}

    def create(self, station_id: str, name: str, data: dict[str, Any]) -> dict[str, Any]:
        self._station(station_id)
        clean = self._validate(data)
        clean_name = str(name or "FBD Project").strip()
        if not clean_name or len(clean_name) > 160:
            raise ValueError("FBD Studio project name must contain 1–160 characters")
        existing = self.core.repository.list_records(entity_type="FBDStudioDocument", station_id=station_id)
        if any(str(row.get("name", "")).strip().casefold() == clean_name.casefold() for row in existing):
            raise ValueError("FBD Studio project with this name already exists in the station")
        doc = FBDStudioDocument(name=clean_name, station_id=station_id, data=clean)
        revision = self.core.repository.save(doc)
        self.core.audit.append(actor_id="local-engineer", action="fbd_studio.document_created",
            resource_type="fbd_studio_document", resource_id=doc.id, details={"station_id": station_id})
        return self._view(doc, revision)

    def get(self, document_id: str) -> dict[str, Any]:
        doc, revision = self.core.repository.get(document_id, FBDStudioDocument)
        return self._view(doc, revision)

    def save(self, document_id: str, expected_revision: int, data: dict[str, Any], name: str | None = None) -> dict[str, Any]:
        doc, revision = self.core.repository.get(document_id, FBDStudioDocument)
        if revision != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {revision}")
        doc.data = self._validate(data)
        if name is not None:
            clean_name = str(name).strip()
            if not clean_name or len(clean_name) > 160:
                raise ValueError("FBD Studio project name must contain 1–160 characters")
            siblings = self.core.repository.list_records(entity_type="FBDStudioDocument", station_id=doc.station_id)
            if any(row["entity_id"] != document_id and str(row.get("name", "")).strip().casefold() == clean_name.casefold() for row in siblings):
                raise ValueError("FBD Studio project with this name already exists in the station")
            doc.name = clean_name
        doc.updated_at = _now()
        new_revision = self.core.repository.save(doc, expected_version=revision)
        self.core.audit.append(actor_id="local-engineer", action="fbd_studio.document_saved",
            resource_type="fbd_studio_document", resource_id=doc.id,
            details={"revision": new_revision, "pages": len(doc.data.get("pages", []))})
        return self._view(doc, new_revision)


    # The first compiler intentionally supports only blocks whose execution
    # semantics and port contracts already exist in Core FBD.
    _COMPILER_BLOCKS = {
        "BOOL_INPUT": "BOOL_INPUT", "FLOAT_INPUT": "FLOAT_INPUT",
        "KNOB": "KNOB", "CONSTANT": "CONSTANT",
        "ANALOG_INPUT": "ANALOG_INPUT", "EXTERNAL_SENSOR": "EXTERNAL_SENSOR",
        "POINT_INPUT": "POINT_INPUT", "SCHEDULE": "SCHEDULE",
        "AND": "AND", "OR": "OR", "NOT": "NOT", "COMBINATION": "COMBINATION", "ADD": "ADD",
        "SUB": "SUB", "MUL": "MUL", "DIV": "DIV", "SELECT": "SELECT",
        "COMPARE_GT": "COMPARE_GT", "COMPARE_LT": "COMPARE_LT",
        "LIMIT": "LIMIT", "SCALE": "SCALE", "HYSTERESIS": "HYSTERESIS",
        "DELAY": "DELAY", "LATCH": "LATCH", "PID_LOOP": "PID_LOOP",
        "SWITCH": "SWITCH", "TIME": "TIME", "BOOL_OUTPUT": "BOOL_OUTPUT",
        "FLOAT_OUTPUT": "FLOAT_OUTPUT",
    }

    @staticmethod
    def _port_token(token: Any) -> tuple[str, str, int]:
        parts = str(token or "").split(":")
        if len(parts) != 3 or parts[0] not in {"in", "out"} or not parts[1] or not parts[2].isdigit():
            raise ValueError(f"Некорректная ссылка на порт FBD: {token!r}")
        return parts[0], parts[1], int(parts[2])

    def compile_preview(self, document_id: str, expected_revision: int | None = None) -> dict[str, Any]:
        """Validate whether the authoring graph can be compiled without mutation."""
        from avic_core.logic_fbd import FBDService
        doc, revision = self.core.repository.get(document_id, FBDStudioDocument)
        if expected_revision is not None and revision != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {revision}")
        data = self._validate(doc.data)
        pages = data.get("pages", [])
        if not pages:
            raise ValueError("В FBD-проекте должна быть хотя бы одна страница")
        core = FBDService(self.core)

        def resolved_output_signal(module: dict[str, Any], block_type: str, port_name: str) -> str | None:
            """Resolve dynamic Core output contracts before validating Studio links."""
            signal = core.BLOCKS[block_type]["outputs"].get(port_name)
            if signal != "any":
                return signal
            params = module.get("params") if isinstance(module.get("params"), dict) else {}
            if block_type == "POINT_INPUT":
                point_id = ((params.get("pointRef") or {}).get("id")
                            or (params.get("externalPointBinding") or {}).get("pointId")
                            or params.get("point_id"))
                if not point_id:
                    return None
                from avic_core.domain.models import Point
                point, _ = self.core.repository.get(str(point_id), Point)
                device = self.core.repository.get_record(point.device_id)
                if device["entity_type"] != "Device" or device["payload"].get("station_id") != doc.station_id:
                    raise ValueError("точка POINT_INPUT принадлежит другой станции")
                return core._point_signal_type(point.data_type)
            if block_type == "SCHEDULE":
                schedule_id = params.get("schedule_id") or (params.get("schedule") or {}).get("schedule_id")
                if not schedule_id:
                    return None
                schedule = self.core.schedules.get(str(schedule_id))
                if schedule["station_id"] != doc.station_id:
                    raise ValueError("расписание SCHEDULE принадлежит другой станции")
                return {"BOOLEAN": "bool", "NUMERIC": "float", "STRING": "string", "ENUM": "any"}.get(
                    str(schedule.get("value_type") or "").upper()
                )
            return signal

        page_by_id = {str(page["id"]): page for page in pages}
        modules: dict[str, dict[str, Any]] = {}
        page_for_module: dict[str, str] = {}
        issues: list[str] = []
        for page in pages:
            for module in page.get("modules", []):
                mid = str(module.get("id") or "")
                modules[mid] = module
                page_for_module[mid] = str(page["id"])
                typ = str(module.get("type") or "")
                if typ in {"CONNECTIVE", "TO_CONNECTIVE"}:
                    continue
                if typ not in self._COMPILER_BLOCKS:
                    issues.append(f"Страница «{page.get('name','')}», блок «{module.get('name') or typ}»: тип {typ or 'не указан'} пока не поддержан компилятором")
                    continue
                mapped = self._COMPILER_BLOCKS[typ]
                spec = core.BLOCKS[mapped]
                ins = [str(x.get("name") or "") for x in module.get("ins", [])]
                outs = [str(x.get("name") or "") for x in module.get("outs", [])]
                expected_inputs = ["IN"] if typ == "SCALE" else list(spec["inputs"])
                if set(ins) != set(expected_inputs) or len(ins) != len(expected_inputs):
                    issues.append(f"Блок «{module.get('name') or typ}»: входы редактора {ins} не совпадают с контрактом {expected_inputs}")
                if set(outs) != set(spec["outputs"]) or len(outs) != len(spec["outputs"]):
                    issues.append(f"Блок «{module.get('name') or typ}»: выходы редактора {outs} не совпадают с контрактом Core {list(spec['outputs'])}")
                params = module.get("params") or {}
                if typ == "BOOL_INPUT":
                    value = params.get("value", False)
                    if not isinstance(value, bool) and str(value).strip().casefold() not in {"true", "false", "да", "нет", "1", "0"}:
                        issues.append(f"Блок «{module.get('name') or typ}»: значение BOOL_INPUT должно быть Да или Нет")
                if typ in {"FLOAT_INPUT", "KNOB", "CONSTANT"}:
                    value = params.get("value", core.BLOCKS[mapped]["defaults"].get("value", 0.0))
                    try:
                        import math
                        if isinstance(value, bool) or not math.isfinite(float(value)):
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: {typ} должен содержать конечное число")
                if typ in {"ANALOG_INPUT", "EXTERNAL_SENSOR"}:
                    raw_value = params.get("rawValue", params.get("value", 0.0))
                    try:
                        import math
                        if isinstance(raw_value, bool) or not math.isfinite(float(raw_value)):
                            raise ValueError
                        points = params.get("scalingPoints") or []
                        if not isinstance(points, list) or len(points) > 20:
                            raise ValueError
                        xs = []
                        for pair in points:
                            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                                raise ValueError
                            x, y = pair
                            if any(isinstance(v, bool) or not math.isfinite(float(v)) for v in (x, y)):
                                raise ValueError
                            xs.append(float(x))
                        if len(xs) != len(set(xs)):
                            raise ValueError
                        if params.get("sensorType") is not None and len(points) < 2:
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: {typ} требует конечный rawValue и корректную таблицу scalingPoints")
                if typ == "DELAY":
                    cfg = params.get("delay") or {}
                    try:
                        import math
                        on_delay, off_delay = float(cfg.get("onDelay", 5.0)), float(cfg.get("offDelay", 0.0))
                        if not math.isfinite(on_delay) or not math.isfinite(off_delay) or on_delay < 0 or off_delay < 0:
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: DELAY требует конечные неотрицательные onDelay/offDelay")
                if typ == "SWITCH":
                    value = params.get("value", False)
                    level = params.get("user_level", 0)
                    if not isinstance(value, bool) or isinstance(level, bool) or not isinstance(level, int) or not 0 <= level <= 99:
                        issues.append(f"Блок «{module.get('name') or typ}»: SWITCH требует bool Status и PIN level 0..99")
                if typ == "PID_LOOP":
                    try:
                        core._normalize_pid_config(params.get("pid"))
                    except ValueError as exc:
                        issues.append(f"Блок «{module.get('name') or typ}»: {exc}")
                if typ == "LATCH":
                    cfg = params.get("latch") or {}
                    if not isinstance(cfg.get("resetPriority", True), bool):
                        issues.append(f"Блок «{module.get('name') or typ}»: LATCH.resetPriority должен быть bool")
                    initial = cfg.get("initial", 0)
                    if initial not in (0, 1, False, True):
                        issues.append(f"Блок «{module.get('name') or typ}»: LATCH.initial должен быть 0/1")
                if typ == "COMBINATION":
                    rows = params.get("comboRows", core.BLOCKS[mapped]["defaults"]["comboRows"])
                    valid = isinstance(rows, list) and len(rows) == 4
                    if valid:
                        allowed = {"", "E", "e", "F", "f", "G", "g", "H", "h"}
                        valid = all(isinstance(row, dict) and isinstance(row.get("enabled"), bool)
                                    and isinstance(row.get("cells"), list) and len(row["cells"]) == 4
                                    and all(isinstance(cell, str) and cell in allowed for cell in row["cells"])
                                    for row in rows)
                    if not valid:
                        issues.append(f"Блок «{module.get('name') or typ}»: COMBINATION должен содержать четыре корректные строки условий E/F/G/H")
                if typ == "SCALE":
                    scale = params.get("scale") or {}
                    try:
                        import math
                        values = [float(scale.get("inputLow", 0.0)), float(scale.get("inputHigh", 100.0)),
                                  float(scale.get("outputLow", 0.0)), float(scale.get("outputHigh", 100.0))]
                        if not all(math.isfinite(v) for v in values) or values[0] == values[1]:
                            raise ValueError
                        if not isinstance(scale.get("clampOutput", True), bool):
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: параметры SCALE должны быть конечными числами, а входной диапазон не должен быть нулевым")
                    if ins != ["IN"] or outs != ["OUT"]:
                        issues.append(f"Блок «{module.get('name') or typ}»: SCALE в Studio должен иметь вход IN и выход OUT")
                elif typ == "HYSTERESIS":
                    cfg = params.get("hysteresis") or {}
                    try:
                        import math
                        low, high = float(cfg.get("low", 18.0)), float(cfg.get("high", 22.0))
                        if not math.isfinite(low) or not math.isfinite(high) or low >= high:
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: для HYSTERESIS требуется LOW < HIGH и конечные числовые пороги")
                if typ == "POINT_INPUT":
                    point_id = (params.get("pointRef") or {}).get("id") or (params.get("externalPointBinding") or {}).get("pointId") or params.get("point_id")
                    if not point_id:
                        issues.append(f"Блок «{module.get('name') or typ}»: не выбрана реальная точка станции")
                    else:
                        try:
                            from avic_core.domain.models import Point
                            point, _ = self.core.repository.get(str(point_id), Point)
                            device = self.core.repository.get_record(point.device_id)
                            if device["entity_type"] != "Device" or device["payload"].get("station_id") != doc.station_id:
                                issues.append(f"Блок «{module.get('name') or typ}»: точка принадлежит другой станции")
                            elif core._point_signal_type(point.data_type) is None:
                                issues.append(f"Блок «{module.get('name') or typ}»: неподдерживаемый тип точки {point.data_type}")
                        except Exception:
                            issues.append(f"Блок «{module.get('name') or typ}»: выбранная точка не найдена в Core")
                elif typ == "SCHEDULE":
                    schedule_id = params.get("schedule_id") or (params.get("schedule") or {}).get("schedule_id")
                    if not schedule_id:
                        issues.append(f"Блок «{module.get('name') or typ}»: локальное расписание редактора ещё не связано с расписанием Scheduler Manager")
                    else:
                        try:
                            schedule = self.core.schedules.get(str(schedule_id))
                            if schedule["station_id"] != doc.station_id:
                                issues.append(f"Блок «{module.get('name') or typ}»: расписание принадлежит другой станции")
                        except Exception:
                            issues.append(f"Блок «{module.get('name') or typ}»: расписание Core не найдено")

        references = data.get("references", [])
        reference_by_proxy = {str(ref["proxyModuleId"]): ref for ref in references}
        reference_ids = {str(ref["id"]) for ref in references}
        executable_module_ids = {mid for mid, module in modules.items()
                                 if str(module.get("type") or "") not in {"CONNECTIVE", "TO_CONNECTIVE"}}
        for mid, module in modules.items():
            typ = str(module.get("type") or "")
            params = module.get("params") if isinstance(module.get("params"), dict) else {}
            if typ == "CONNECTIVE" and mid not in reference_by_proxy:
                issues.append(f"Страница «{page_by_id[page_for_module[mid]].get('name','')}»: CONNECTIVE {module.get('name') or mid} не имеет Page Reference")
            elif typ == "TO_CONNECTIVE" and str(params.get("referenceId") or "") not in reference_ids:
                issues.append(f"Страница «{page_by_id[page_for_module[mid]].get('name','')}»: TO_CONNECTIVE {module.get('name') or mid} ссылается на отсутствующий Page Reference")

        link_count = 0
        graph_edges: list[tuple[str, str]] = []
        occupied_inputs: set[tuple[str, str]] = set()
        for link in data.get("links", []):
            if not isinstance(link, dict):
                issues.append("Обнаружена связь некорректного формата")
                continue
            try:
                direction_a, source_id, source_index = self._port_token(link.get("from"))
                direction_b, target_id, target_index = self._port_token(link.get("to"))
                if direction_a != "out" or direction_b != "in":
                    raise ValueError("связь должна идти от выхода к входу")
                source = modules.get(source_id)
                target = modules.get(target_id)
                if source is None or target is None:
                    raise ValueError("блок-источник или блок-приёмник не найден")
                source_type = str(source.get("type") or "")
                target_type = str(target.get("type") or "")
                if target_type in {"CONNECTIVE", "TO_CONNECTIVE"}:
                    raise ValueError("нельзя подключать сигнал к навигационному proxy/marker")
                if target_type not in self._COMPILER_BLOCKS:
                    raise ValueError(f"тип блока-приёмника {target_type or 'не указан'} не поддерживается")
                if target_index >= len(target.get("ins", [])):
                    raise ValueError("индекс входного порта вне диапазона")
                target_port_name = str(target["ins"][target_index].get("name") or "")
                target_core_type = self._COMPILER_BLOCKS[target_type]
                target_signal = core.BLOCKS[target_core_type]["inputs"].get(target_port_name)
                if target_signal is None:
                    raise ValueError(f"входной порт {target_port_name} отсутствует в контракте Core")

                if source_type == "CONNECTIVE":
                    reference = reference_by_proxy.get(source_id)
                    if reference is None:
                        raise ValueError("CONNECTIVE proxy не имеет действующей Page Reference")
                    if source_index != 0 or source_index >= len(source.get("outs", [])):
                        raise ValueError("CONNECTIVE proxy должен использовать свой единственный выход")
                    if page_for_module[target_id] != str(reference["targetPageId"]) or str(link.get("pageId")) != str(reference["targetPageId"]):
                        raise ValueError("потребитель Connective должен находиться на странице назначения")
                    source_module_id = str(reference["sourceModuleId"])
                    source_module = modules.get(source_module_id)
                    if source_module is None or page_for_module.get(source_module_id) != str(reference["sourcePageId"]):
                        raise ValueError("исходный блок Connective не найден на исходной странице")
                    source_type_real = str(source_module.get("type") or "")
                    if source_type_real not in self._COMPILER_BLOCKS:
                        raise ValueError(f"тип исходного блока Connective {source_type_real or 'не указан'} не поддерживается")
                    source_port_index = int(reference["sourcePort"])
                    source_outputs = source_module.get("outs", [])
                    if source_port_index >= len(source_outputs):
                        raise ValueError("исходный выход Connective не найден")
                    source_port_name = str(source_outputs[source_port_index].get("name") or "")
                    source_core_type = self._COMPILER_BLOCKS[source_type_real]
                    source_signal = resolved_output_signal(source_module, source_core_type, source_port_name)
                    if source_signal is None or source_signal != target_signal:
                        raise ValueError("несовместимые типы исходного и целевого портов Connective")
                    target_key = (target_id, target_port_name)
                    if target_key in occupied_inputs:
                        raise ValueError("входной порт уже занят другой связью")
                    occupied_inputs.add(target_key)
                    graph_edges.append((source_module_id, target_id))
                else:
                    if source_type in {"TO_CONNECTIVE"} or source_type not in self._COMPILER_BLOCKS:
                        raise ValueError(f"источник связи {source_type or 'не указан'} не является поддерживаемым вычислительным блоком")
                    if page_for_module[source_id] != page_for_module[target_id] or str(link.get("pageId")) != page_for_module[source_id]:
                        raise ValueError("обычная связь должна находиться внутри одной страницы")
                    if source_index >= len(source.get("outs", [])):
                        raise ValueError("индекс выходного порта вне диапазона")
                    source_port_name = str(source["outs"][source_index].get("name") or "")
                    source_core_type = self._COMPILER_BLOCKS[source_type]
                    source_signal = resolved_output_signal(source, source_core_type, source_port_name)
                    if source_signal is None or source_signal != target_signal:
                        raise ValueError("несовместимые типы выходного и входного портов")
                    target_key = (target_id, target_port_name)
                    if target_key in occupied_inputs:
                        raise ValueError("входной порт уже занят другой связью")
                    occupied_inputs.add(target_key)
                    graph_edges.append((source_id, target_id))
                link_count += 1
            except (KeyError, TypeError, ValueError) as exc:
                issues.append(f"Связь {link.get('id') or link_count + 1}: {exc}")

        # Validate the complete graph after expanding Connective aliases.
        adjacency = {mid: set() for mid in executable_module_ids}
        indegree = {mid: 0 for mid in executable_module_ids}
        for source_id, target_id in graph_edges:
            if source_id in adjacency and target_id in adjacency and target_id not in adjacency[source_id]:
                adjacency[source_id].add(target_id)
                indegree[target_id] += 1
        ready = [mid for mid, degree in indegree.items() if degree == 0]
        processed = 0
        while ready:
            current = ready.pop()
            processed += 1
            for target_id in adjacency[current]:
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    ready.append(target_id)
        if processed != len(executable_module_ids):
            issues.append("После раскрытия межстраничных Connective стратегия содержит циклическую зависимость")

        if issues:
            return {"document_id": document_id, "revision": revision, "compilable": False,
                    "source_pages": len(pages), "source_blocks": len(executable_module_ids), "source_links": link_count,
                    "supported_block_types": sorted(self._COMPILER_BLOCKS), "issues": issues,
                    "field_writes_enabled": False, "runtime_published": False}
        return {"document_id": document_id, "revision": revision, "compilable": True,
                "source_pages": len(pages), "source_blocks": len(executable_module_ids), "source_links": link_count,
                "supported_block_types": sorted(self._COMPILER_BLOCKS), "issues": [],
                "field_writes_enabled": False, "runtime_published": False,
                "message": "Все блоки, локальные связи и межстраничные Connective прошли проверку. Можно создать исполняемую Core FBD-стратегию без записи в оборудование."}

    def _register_exposed_points(self, source: FBDStudioDocument, core_document_id: str) -> int:
        """Upsert stable virtual points for exposed Studio output ports."""
        from uuid import UUID
        from avic_core.points.runtime import FBDExposedPoint
        from avic_core.logic_fbd import FBDService
        core_graph = FBDService(self.core).get(core_document_id)
        compiled_modules = {str(n.get("params", {}).get("_studio_module_id")): n for n in core_graph.get("nodes", [])}
        count = 0
        for raw in source.data.get("fbdPoints", []):
            point_id = str(raw.get("id") or "")
            UUID(point_id)
            source_ref = raw.get("source") if isinstance(raw.get("source"), dict) else {}
            module_id = str(source_ref.get("moduleId") or "")
            port_index = int(source_ref.get("portIndex", 0))
            if not module_id or port_index != 0 or module_id not in compiled_modules:
                raise ValueError("FBD exposed point source must reference an existing supported Core OUT port")
            name = str(raw.get("name") or raw.get("tag") or "FBD Output")[:160]
            declared_type = str(raw.get("dataType") or raw.get("data_type") or "analog").casefold()
            data_type = "bool" if declared_type in {"digital", "bool", "boolean", "binary"} else "float"
            node_type = compiled_modules[module_id]["type"]
            output_type = FBDService.BLOCKS[node_type]["outputs"].get("OUT")
            if output_type not in {"bool", "float"} or output_type != data_type:
                raise ValueError(f"FBD exposed point type {data_type} does not match source block {node_type} output {output_type}")
            native = str(raw.get("native_identity") or f"fbd://{core_document_id}/{module_id}/OUT")
            try:
                point, version = self.core.repository.get(point_id, FBDExposedPoint)
                point.name = name; point.station_id = source.station_id
                point.fbd_document_id = core_document_id; point.studio_document_id = source.id
                point.source_module_id = module_id; point.source_port = "OUT"
                point.data_type = data_type; point.unit = str(raw.get("unit") or "")
                point.native_identity = native; point.source_ref = f"{source.name} / {name}"
                self.core.repository.save(point, expected_version=version)
            except Exception as exc:
                from avic_core.repository.sqlite_repository import EntityNotFound
                if not isinstance(exc, EntityNotFound):
                    raise
                point = FBDExposedPoint(name=name, id=point_id, station_id=source.station_id,
                    fbd_document_id=core_document_id, studio_document_id=source.id,
                    source_module_id=module_id, source_port="OUT", data_type=data_type,
                    unit=str(raw.get("unit") or ""), native_identity=native,
                    source_ref=f"{source.name} / {name}")
                self.core.repository.save(point)
            count += 1
        return count

    def compile_to_core(self, document_id: str, expected_revision: int) -> dict[str, Any]:
        """Create a separate executable Core FBD strategy from a validated Studio graph."""
        from uuid import uuid4
        from avic_core.logic_fbd import FBDService
        preview = self.compile_preview(document_id, expected_revision)
        if not preview["compilable"]:
            raise ValueError("Компиляция остановлена: " + " | ".join(preview["issues"]))
        source, revision = self.core.repository.get(document_id, FBDStudioDocument)
        if revision != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {revision}")
        data = source.data
        core_fbd = FBDService(self.core)
        compile_marker = f"AVIC_FBD_STUDIO_SOURCE={document_id};REV={revision};COMPILER=2"
        existing = next((row for row in self.core.repository.list_records(entity_type="LogicDocument")
                         if row["payload"].get("station_id") == source.station_id
                         and row["payload"].get("description") == compile_marker), None)
        if existing:
            existing_graph = core_fbd.get(existing["entity_id"])
            registered_points = self._register_exposed_points(source, existing["entity_id"])
            return {"source_document_id": document_id, "source_revision": revision,
                    "core_document": existing_graph, "compiled_blocks": len(existing_graph["nodes"]),
                    "compiled_links": len(existing_graph["links"]) + len(existing_graph.get("connectives", [])), "already_compiled": True,
                    "registered_fbd_points": registered_points, "runtime_published": False, "field_writes_enabled": False,
                    "message": "Эта ревизия уже скомпилирована. Возвращена существующая Core FBD-стратегия; виртуальные точки синхронизированы без дубликатов."}
        created = core_fbd.create(source.station_id, source.name + " · Core", compile_marker)
        core_id = created["id"]
        try:
            # Studio stores page order in the pages array; preserve it exactly.
            pages = list(data.get("pages", []))
            core_pages = [created["pages"][0]["id"]] if created.get("pages") else [core_fbd.get(core_id)["pages"][0]["id"]]
            # The Core FBD create operation seeds one default page; rename it
            # to the first Studio page so page order and labels are preserved.
            core_fbd.rename_page(core_id, core_pages[0], str(pages[0].get("name") or "Страница 1"))
            for page in pages[1:]:
                current = core_fbd.add_page(core_id, str(page.get("name") or "Страница"))
                core_pages.append(next(p["id"] for p in current["pages"] if p["name"] == str(page.get("name") or "Страница")))
            page_map = {str(page["id"]): core_pages[i] for i, page in enumerate(pages)}
            studio_modules = {str(m["id"]): m for page in pages for m in page.get("modules", [])}
            reference_by_proxy = {str(ref["proxyModuleId"]): ref for ref in data.get("references", [])}
            module_map = {mid: str(uuid4()) for mid, m in studio_modules.items() if str(m.get("type") or "") not in {"CONNECTIVE", "TO_CONNECTIVE"}}
            nodes = []
            for page in pages:
                for module in page.get("modules", []):
                    if str(module.get("type") or "") in {"CONNECTIVE", "TO_CONNECTIVE"}:
                        continue
                    typ = self._COMPILER_BLOCKS[module["type"]]
                    params = dict(module.get("params") or {})
                    if typ == "POINT_INPUT":
                        params = {"point_id": (params.get("pointRef") or {}).get("id") or (params.get("externalPointBinding") or {}).get("pointId") or params.get("point_id")}
                    elif typ == "SCHEDULE":
                        params = {"schedule_id": params.get("schedule_id") or (params.get("schedule") or {}).get("schedule_id")}
                    elif typ == "BOOL_INPUT":
                        raw_value = params.get("value", False)
                        if isinstance(raw_value, str):
                            params = {"value": raw_value.strip().casefold() in {"true", "да", "1"}}
                        else:
                            params = {"value": bool(raw_value)}
                    elif typ in {"FLOAT_INPUT", "KNOB", "CONSTANT"}:
                        params = {"value": float(params.get("value", core_fbd.BLOCKS[typ]["defaults"].get("value", 0.0)))}
                    elif typ in {"ANALOG_INPUT", "EXTERNAL_SENSOR"}:
                        params = {key: params[key] for key in ("rawValue", "value", "sensorType", "sensorPart",
                                  "scalingRange", "scalingMode", "scalingInput", "scalingPoints") if key in params}
                    elif typ == "SWITCH":
                        params = {"value": bool(params.get("value", False)),
                                  "user_level": int(params.get("user_level", 0))}
                    elif typ == "PID_LOOP":
                        params = {"pid": core_fbd._normalize_pid_config(params.get("pid"))}
                    elif typ == "DELAY":
                        cfg = params.get("delay") or {}
                        params = {"on_delay": float(cfg.get("onDelay", 5.0)),
                                  "off_delay": float(cfg.get("offDelay", 0.0)),
                                  "initial_state": bool(cfg.get("initial", False))}
                    elif typ == "LATCH":
                        cfg = params.get("latch") or {}
                        initial = cfg.get("initial", 0)
                        params = {"initial_state": initial is True or initial == 1,
                                  "reset_priority": cfg.get("resetPriority", True)}
                    elif typ == "HYSTERESIS":
                        cfg = params.get("hysteresis") or {}
                        initial = cfg.get("initial", False)
                        if isinstance(initial, str):
                            initial = initial.strip().casefold() in {"true", "1", "да", "on"}
                        params = {"initial_state": initial is True or initial == 1}
                    elif typ == "SCALE":
                        cfg = params.get("scale") or {}
                        params = {"clamp_output": cfg.get("clampOutput", True)}
                    params["_studio_module_id"] = str(module["id"])
                    nodes.append({"id": module_map[str(module["id"])], "type": typ,
                                  "name": str(module.get("name") or module["type"]),
                                  "x": float(module.get("x", 40)), "y": float(module.get("y", 40)),
                                  "page_id": page_map[str(page["id"])], "params": params})
            links = []
            # Studio SCALE exposes one signal input; four range bounds are parameters.
            # Materialize bounds as Core FLOAT_INPUT nodes to preserve a single canonical Core contract.
            linked_targets = set()
            for source_link in data.get("links", []):
                _, target_mid, target_index = self._port_token(source_link.get("to"))
                target_module = next((m for pg in pages for m in pg.get("modules", []) if str(m["id"]) == target_mid), None)
                if target_module and target_index < len(target_module.get("ins", [])):
                    linked_targets.add((target_mid, str(target_module["ins"][target_index]["name"])))
            for page in pages:
                for module in page.get("modules", []):
                    typ = module.get("type")
                    cfg_all = module.get("params") or {}
                    if typ == "SCALE":
                        cfg = cfg_all.get("scale") or {}
                        generated_bounds = [("IN_MIN", float(cfg.get("inputLow", 0.0))),
                                            ("IN_MAX", float(cfg.get("inputHigh", 100.0))),
                                            ("OUT_MIN", float(cfg.get("outputLow", 0.0))),
                                            ("OUT_MAX", float(cfg.get("outputHigh", 100.0)))]
                    elif typ == "HYSTERESIS":
                        cfg = cfg_all.get("hysteresis") or {}
                        generated_bounds = [("LOW", float(cfg.get("low", 18.0))),
                                            ("HIGH", float(cfg.get("high", 22.0)))]
                    else:
                        continue
                    target_node_id = module_map[str(module["id"])]
                    for index, (port_name, value) in enumerate(generated_bounds):
                        # Explicit links always win over block parameter defaults.
                        if (str(module["id"]), port_name) in linked_targets:
                            continue
                        constant_id = str(uuid4())
                        nodes.append({"id": constant_id, "type": "FLOAT_INPUT",
                                      "name": f"{module.get('name') or typ} · {port_name}",
                                      "x": float(module.get("x", 40)) + 180,
                                      "y": float(module.get("y", 40)) + 70 + 42 * index,
                                      "page_id": page_map[str(page["id"])], "params": {"value": value}})
                        links.append({"id": str(uuid4()), "source_node_id": constant_id,
                                      "source_port": "OUT", "target_node_id": target_node_id,
                                      "target_port": port_name})
            cross_connectives = []
            for link in data.get("links", []):
                _, source_id, source_index = self._port_token(link["from"])
                _, target_id, target_index = self._port_token(link["to"])
                source_module = studio_modules[source_id]
                target_module = studio_modules[target_id]
                if str(source_module.get("type") or "") == "CONNECTIVE":
                    reference = reference_by_proxy[source_id]
                    real_source = studio_modules[str(reference["sourceModuleId"])]
                    source_port_name = str(real_source["outs"][int(reference["sourcePort"])]["name"])
                    target_port_name = str(target_module["ins"][target_index]["name"])
                    cross_connectives.append({
                        "name": str((source_module.get("params") or {}).get("label") or source_module.get("name") or "Connective"),
                        "source_page_id": page_map[str(reference["sourcePageId"])],
                        "source_node_id": module_map[str(reference["sourceModuleId"])],
                        "source_port": source_port_name,
                        "target_page_id": page_map[str(reference["targetPageId"])],
                        "target_node_id": module_map[target_id],
                        "target_port": target_port_name,
                    })
                    continue
                links.append({"id": str(uuid4()), "source_node_id": module_map[source_id],
                              "source_port": str(source_module["outs"][source_index]["name"]),
                              "target_node_id": module_map[target_id],
                              "target_port": str(target_module["ins"][target_index]["name"])})
            # add_page() advances the Core document revision; read the latest
            # revision after page creation rather than using the initial one.
            latest_revision = core_fbd.get(core_id)["revision"]
            saved = core_fbd.save(core_id, latest_revision, nodes, links)
            for connective in cross_connectives:
                core_fbd.create_connective(core_id, connective)
            saved = core_fbd.get(core_id)
            registered_points = self._register_exposed_points(source, core_id)
            self.core.audit.append(actor_id="local-engineer", action="fbd_studio.compiled_to_core",
                resource_type="fbd_studio_document", resource_id=document_id,
                details={"source_revision": revision, "core_document_id": core_id,
                         "blocks": len(nodes), "links": len(links) + len(cross_connectives)})
            return {"source_document_id": document_id, "source_revision": revision,
                    "core_document": saved, "compiled_blocks": len(nodes), "compiled_links": len(links) + len(cross_connectives),
                    "registered_fbd_points": registered_points, "runtime_published": False, "field_writes_enabled": False,
                    "message": "Создана отдельная Core FBD-стратегия. Исходный проект Studio не изменён. Запись в оборудование отключена."}
        except Exception:
            # Best-effort cleanup: a failed compile must not leave a partial strategy.
            try:
                for row in self.core.repository.list_records(entity_type="StrategyConnective"):
                    if row["payload"].get("document_id") == core_id:
                        self.core.repository.delete(row["entity_id"], expected_version=row["version"])
                for entity_type in ("LogicLink", "LogicNode", "StrategyPage"):
                    for row in self.core.repository.list_records(entity_type=entity_type):
                        if row["payload"].get("document_id") == core_id:
                            self.core.repository.delete(row["entity_id"], expected_version=row["version"])
                for row in self.core.repository.list_records(entity_type="FBDExposedPoint"):
                    if row["payload"].get("fbd_document_id") == core_id:
                        self.core.repository.delete(row["entity_id"], expected_version=row["version"])
                row = self.core.repository.get_record(core_id)
                self.core.repository.delete(core_id, expected_version=row["version"])
            except Exception:
                pass
            raise

    def delete(self, document_id: str, expected_revision: int) -> None:
        doc, revision = self.core.repository.get(document_id, FBDStudioDocument)
        if revision != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {revision}")
        self.core.repository.delete(document_id, expected_version=revision)
        self.core.audit.append(actor_id="local-engineer", action="fbd_studio.document_deleted",
            resource_type="fbd_studio_document", resource_id=document_id,
            details={"station_id": doc.station_id, "name": doc.name})
