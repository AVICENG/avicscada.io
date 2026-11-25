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
                if not module_id or module_id in module_ids:
                    raise ValueError("FBD module IDs must be present and unique within a page")
                module_ids.add(module_id)
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
                try:
                    port_index = int(source.get("portIndex"))
                except (TypeError, ValueError):
                    raise ValueError("FBD point source portIndex must be an integer")
                if not page_id or not module_id or port_index < 0:
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
                if port_id and not any(isinstance(port, dict) and str(port.get("id") or "") == port_id for port in outputs):
                    raise ValueError("FBD point source port UID does not exist on the source module")
                source_key = (page_id, module_id, port_id or str(port_index))
                if source_key in seen_sources:
                    raise ValueError("Only one exposed FBD point may reference a source output port")
                seen_sources.add(source_key)
        return data

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
        "POINT_INPUT": "POINT_INPUT", "SCHEDULE": "SCHEDULE",
        "AND": "AND", "OR": "OR", "NOT": "NOT", "ADD": "ADD",
        "SUB": "SUB", "MUL": "MUL", "DIV": "DIV", "SELECT": "SELECT",
        "COMPARE_GT": "COMPARE_GT", "COMPARE_LT": "COMPARE_LT",
        "LIMIT": "LIMIT", "SCALE": "SCALE", "HYSTERESIS": "HYSTERESIS", "BOOL_OUTPUT": "BOOL_OUTPUT",
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
        if data.get("references"):
            raise ValueError("Межстраничные Connective пока не компилируются. Уберите их или дождитесь поддержки межстраничных связей.")
        core = FBDService(self.core)
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
                if typ == "FLOAT_INPUT":
                    value = params.get("value", 0.0)
                    try:
                        import math
                        if isinstance(value, bool) or not math.isfinite(float(value)):
                            raise ValueError
                    except (TypeError, ValueError, OverflowError):
                        issues.append(f"Блок «{module.get('name') or typ}»: FLOAT_INPUT должен содержать конечное число")
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

        link_count = 0
        for link in data.get("links", []):
            if not isinstance(link, dict):
                issues.append("Обнаружена связь некорректного формата")
                continue
            try:
                direction_a, source_id, source_index = self._port_token(link.get("from"))
                direction_b, target_id, target_index = self._port_token(link.get("to"))
                if direction_a != "out" or direction_b != "in":
                    raise ValueError("связь должна идти от выхода к входу")
                source = modules.get(source_id); target = modules.get(target_id)
                if source is None or target is None:
                    raise ValueError("блок-источник или блок-приёмник не найден")
                if page_for_module[source_id] != page_for_module[target_id] or str(link.get("pageId")) != page_for_module[source_id]:
                    raise ValueError("межстраничные связи пока не поддерживаются компилятором")
                if source_index >= len(source.get("outs", [])) or target_index >= len(target.get("ins", [])):
                    raise ValueError("индекс порта вне диапазона")
                link_count += 1
            except ValueError as exc:
                issues.append(f"Связь {link.get('id') or link_count + 1}: {exc}")

        if issues:
            return {"document_id": document_id, "revision": revision, "compilable": False,
                    "source_pages": len(pages), "source_blocks": len(modules), "source_links": len(data.get("links", [])),
                    "supported_block_types": sorted(self._COMPILER_BLOCKS), "issues": issues,
                    "field_writes_enabled": False, "runtime_published": False}
        return {"document_id": document_id, "revision": revision, "compilable": True,
                "source_pages": len(pages), "source_blocks": len(modules), "source_links": link_count,
                "supported_block_types": sorted(self._COMPILER_BLOCKS), "issues": [],
                "field_writes_enabled": False, "runtime_published": False,
                "message": "Все блоки и связи прошли проверку контракта. Можно создать исполняемую Core FBD-стратегию в режиме без записи в оборудование."}

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
        compile_marker = f"AVIC_FBD_STUDIO_SOURCE={document_id};REV={revision}"
        existing = next((row for row in self.core.repository.list_records(entity_type="LogicDocument")
                         if row["payload"].get("station_id") == source.station_id
                         and row["payload"].get("description") == compile_marker), None)
        if existing:
            existing_graph = core_fbd.get(existing["entity_id"])
            registered_points = self._register_exposed_points(source, existing["entity_id"])
            return {"source_document_id": document_id, "source_revision": revision,
                    "core_document": existing_graph, "compiled_blocks": len(existing_graph["nodes"]),
                    "compiled_links": len(existing_graph["links"]), "already_compiled": True,
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
            module_map = {str(m["id"]): str(uuid4()) for page in pages for m in page.get("modules", [])}
            nodes = []
            for page in pages:
                for module in page.get("modules", []):
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
                    elif typ == "FLOAT_INPUT":
                        params = {"value": float(params.get("value", 0.0))}
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
            for link in data.get("links", []):
                _, source_id, source_index = self._port_token(link["from"])
                _, target_id, target_index = self._port_token(link["to"])
                source_module = next(m for p in pages for m in p.get("modules", []) if str(m["id"]) == source_id)
                target_module = next(m for p in pages for m in p.get("modules", []) if str(m["id"]) == target_id)
                links.append({"id": str(uuid4()), "source_node_id": module_map[source_id],
                              "source_port": str(source_module["outs"][source_index]["name"]),
                              "target_node_id": module_map[target_id],
                              "target_port": str(target_module["ins"][target_index]["name"])})
            # add_page() advances the Core document revision; read the latest
            # revision after page creation rather than using the initial one.
            latest_revision = core_fbd.get(core_id)["revision"]
            saved = core_fbd.save(core_id, latest_revision, nodes, links)
            registered_points = self._register_exposed_points(source, core_id)
            self.core.audit.append(actor_id="local-engineer", action="fbd_studio.compiled_to_core",
                resource_type="fbd_studio_document", resource_id=document_id,
                details={"source_revision": revision, "core_document_id": core_id,
                         "blocks": len(nodes), "links": len(links)})
            return {"source_document_id": document_id, "source_revision": revision,
                    "core_document": saved, "compiled_blocks": len(nodes), "compiled_links": len(links),
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
