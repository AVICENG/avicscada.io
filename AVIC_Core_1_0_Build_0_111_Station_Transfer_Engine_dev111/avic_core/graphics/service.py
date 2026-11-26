from __future__ import annotations
from datetime import datetime, timezone
from avic_core.graphics.models import GraphicDocument, GraphicElement, PointBinding
from avic_core.graphics.svg_library import SVG_SYMBOLS
from avic_core.domain.models import Point
from avic_core.points.runtime import FBDExposedPoint
from avic_core.repository.sqlite_repository import EntityNotFound

class GraphicsService:
    """Persistent, station-scoped graphics authoring. No runtime or field writes."""
    SYMBOLS = {
        key: {
            "label": meta["name"],
            "category": meta["category"],
            "slots": (["value", "feedback", "alarm", "quality"]
                      if key in {"pump", "pump_vertical", "pump_inline", "fan", "valve", "control_valve", "three_way_valve", "damper",
                                 "ahu_section_outdoor_damper", "ahu_section_supply_fan"}
                      else ["value", "alarm", "quality"]),
        }
        for key, meta in SVG_SYMBOLS.items()
    }
    def __init__(self, core): self.core = core
    def _station(self, station_id):
        row = self.core.repository.get_record(station_id)
        if row["entity_type"] != "Station": raise ValueError("Целевой объект не является станцией")
        return row
    def symbol_catalog(self, station_id: str):
        self._station(station_id)
        builtins = [{"id": key, "symbol_key": key, "name": meta["label"], "category": meta["category"],
                     "slots": list(meta["slots"]), "custom": False,
                     "svg_url": f"/api/graphics/library/{key}/svg"} for key, meta in self.SYMBOLS.items()]
        custom = [{**item, "slots": ["value", "feedback", "alarm", "quality"], "custom": True}
                  for item in self.core.custom_svg.list_for_station(station_id)]
        return builtins + custom
    def create(self, station_id: str, name: str, description: str = "", width: int = 1600, height: int = 900):
        self._station(station_id)
        doc = GraphicDocument(name=name, station_id=station_id, description=description, width=width, height=height)
        self.core.repository.save(doc)
        self.core.audit.append(actor_id="local-engineer", action="graphics.document_created", resource_type="graphic_document", resource_id=doc.id, details={"station_id": station_id})
        return self.get(doc.id)
    def list_for_station(self, station_id: str):
        self._station(station_id)
        rows = self.core.repository.list_records(entity_type="GraphicDocument")
        return [{"id":r["entity_id"],"name":r["name"],"revision":r["version"],"description":r["payload"].get("description","")} for r in rows if r["payload"].get("station_id")==station_id]
    def get(self, document_id: str):
        doc, version = self.core.repository.get(document_id, GraphicDocument)
        elements=[]
        bindings_by_element = {}
        for binding_row in self.core.repository.list_records(entity_type="PointBinding"):
            bindings_by_element.setdefault(binding_row["payload"].get("element_id"), []).append(binding_row)
        logic_by_element = {}
        for logic_row in self.core.repository.list_records(entity_type="LogicGraphicsBinding"):
            logic_by_element.setdefault(logic_row["payload"].get("graphic_element_id"), []).append(logic_row)
        for row in self.core.repository.list_records(entity_type="GraphicElement"):
            if row["payload"].get("document_id") == document_id:
                el, ev = self.core.repository.get(row["entity_id"], GraphicElement)
                bindings=[]
                for br in bindings_by_element.get(el.id, []):
                    if br["payload"].get("element_id")==el.id:
                        b,_=self.core.repository.get(br["entity_id"],PointBinding)
                        try:
                            point_row = self.core.repository.get_record(b.point_id)
                            point_name = point_row["name"] if point_row["entity_type"] in {"Point", "FBDExposedPoint"} else "[не точка]"
                        except EntityNotFound: point_name="[точка отсутствует]"
                        bindings.append({"id":b.id,"point_id":b.point_id,"point_name":point_name,"role":b.role,"binding_type":b.binding_type,"target_property":b.target_property,"settings":b.settings})
                logic_bindings=[]
                for lr in logic_by_element.get(el.id, []):
                    if lr["payload"].get("graphic_element_id")==el.id:
                        logic_bindings.append({"id":lr["entity_id"],"graphic_element_id":el.id,"logic_node_id":lr["payload"].get("logic_node_id"),"output_port":lr["payload"].get("output_port","OUT")})
                symbol_name = self.SYMBOLS.get(el.symbol_key, {}).get("label")
                if not symbol_name and el.symbol_key.startswith("custom_"):
                    try:
                        symbol_name = self.core.custom_svg.get(el.symbol_key, station_id=doc.station_id)["name"]
                    except KeyError:
                        symbol_name = "[импортированный SVG отсутствует]"
                elements.append({"id":el.id,"name":el.name,"symbol_key":el.symbol_key,"symbol_name":symbol_name or el.symbol_key,"symbol_version":el.symbol_version,"x":el.x,"y":el.y,"width":el.width,"height":el.height,"rotation":el.rotation,"layer":el.layer,"properties":el.properties,"bindings":bindings,"logic_bindings":logic_bindings})
        return {"id":doc.id,"station_id":doc.station_id,"name":doc.name,"description":doc.description,"width":doc.width,"height":doc.height,"grid_size":doc.grid_size,"revision":version,"elements":elements,"write_enabled":False}
    def points(self, station_id: str):
        self._station(station_id); result=[]
        for row in self.core.repository.list_records(entity_type="Device",station_id=station_id):
            device=row["payload"]
            for pr in self.core.repository.list_records(entity_type="Point"):
                if pr["payload"].get("device_id")==row["entity_id"]:
                    p,_=self.core.repository.get(pr["entity_id"],Point)
                    try:
                        driver=self.core.repository.get_record(device.get("driver_instance_id",""))
                        driver_name=driver["name"]; driver_state=driver["payload"].get("state","UNKNOWN")
                    except (EntityNotFound, ValueError):
                        driver_name="[драйвер не найден]"; driver_state="MISSING"
                    result.append({"id":p.id,"name":p.name,"device":row["name"],"driver":driver_name,"driver_state":driver_state,"address":device.get("address",""),"protocol":device.get("protocol",""),"native_identity":p.native_identity,"data_type":p.data_type,"unit":p.unit,"value":p.value,"timestamp":p.timestamp.isoformat() if p.timestamp else None,"quality":p.quality.value if hasattr(p.quality,"value") else str(p.quality)})
        for row in self.core.repository.list_records(entity_type="FBDExposedPoint", station_id=station_id):
            point, _ = self.core.repository.get(row["entity_id"], FBDExposedPoint)
            try:
                live = self.core.point_runtime.read(point.id)
                value, quality, timestamp = live.value, live.quality, live.timestamp.isoformat() if live.timestamp else None
            except Exception:
                value, quality, timestamp = None, "UNCERTAIN", None
            result.append({"id": point.id, "name": point.name, "device": "FBD Runtime", "driver": "AVIC Core",
                "driver_state": "VIRTUAL", "address": point.native_identity, "protocol": "AVIC FBD",
                "native_identity": point.native_identity, "data_type": point.data_type, "unit": point.unit,
                "value": value, "timestamp": timestamp, "quality": quality, "object_type": "FBDExposedPoint"})
        return result
    def save(self, document_id: str, expected_revision: int, elements: list[dict]):
        """Validate the complete editor payload before changing any persisted row."""
        import math
        import uuid
        doc, version = self.core.repository.get(document_id, GraphicDocument)
        if version != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {version}")
        if not isinstance(elements, list):
            raise ValueError("Список элементов должен быть массивом")
        if len(elements) > 2000:
            raise ValueError("На мнемосхеме допускается не более 2000 элементов")

        existing = {r["entity_id"]: r for r in self.core.repository.list_records(entity_type="GraphicElement")
                    if r["payload"].get("document_id") == document_id}
        all_elements = {r["entity_id"]: r for r in self.core.repository.list_records(entity_type="GraphicElement")}
        prepared = []
        licensed_point_ids = set()
        seen = set()
        for index, raw in enumerate(elements):
            if not isinstance(raw, dict):
                raise ValueError(f"Элемент {index}: ожидался объект")
            eid = str(raw.get("id") or uuid.uuid4())
            try: uuid.UUID(eid)
            except (ValueError, TypeError, AttributeError): raise ValueError(f"Элемент {index}: некорректный идентификатор")
            if eid in seen: raise ValueError(f"Повторный идентификатор элемента: {eid}")
            seen.add(eid)
            if eid in all_elements and eid not in existing:
                raise ValueError("Элемент принадлежит другой мнемосхеме")
            old = self.core.repository.get(eid, GraphicElement)[0] if eid in existing else None
            key = str(raw.get("symbol_key") or (old.symbol_key if old else "sensor"))
            symbol_info = self.SYMBOLS.get(key)
            if symbol_info is None and key.startswith("custom_"):
                try:
                    asset = self.core.custom_svg.get(key, station_id=doc.station_id)
                except KeyError as exc:
                    raise ValueError("Импортированный SVG не найден или принадлежит другой станции") from exc
                symbol_info = {"label": asset["name"], "category": asset["category"],
                               "slots": ["value", "feedback", "alarm", "quality"]}
            if symbol_info is None: raise ValueError(f"Неизвестный тип символа: {key}")
            def number(field, default):
                try: value = float(raw.get(field, getattr(old, field, default)))
                except (TypeError, ValueError): raise ValueError(f"Некорректное числовое поле: {field}")
                if not math.isfinite(value): raise ValueError(f"Поле {field} должно быть конечным числом")
                return value
            x, y = number("x", 0), number("y", 0)
            width, height = number("width", 100), number("height", 80)
            rotation = number("rotation", 0)
            layer = raw.get("layer", getattr(old, "layer", 0))
            if isinstance(layer, bool) or not isinstance(layer, int) or not -1000 <= layer <= 1000:
                raise ValueError("Слой должен быть целым числом от -1000 до 1000")
            if x < 0 or y < 0 or x + width > doc.width or y + height > doc.height:
                raise ValueError("Элемент выходит за границы холста")
            if not (1 <= width <= 2000 and 1 <= height <= 2000): raise ValueError("Размер элемента вне допустимого диапазона")
            if not -360 <= rotation <= 360: raise ValueError("Угол поворота вне допустимого диапазона")
            name = str(raw.get("name") or (old.name if old else symbol_info["label"])).strip()
            if not name or len(name) > 160: raise ValueError("Название элемента должно содержать от 1 до 160 символов")
            bindings = raw.get("bindings", [])
            if not isinstance(bindings, list) or len(bindings) > 32: raise ValueError("Список привязок должен содержать не более 32 записей")
            checked_bindings=[]; binding_targets=set()
            for braw in bindings:
                if not isinstance(braw, dict): raise ValueError("Привязка должна быть объектом")
                role=str(braw.get("role") or "value"); pid=str(braw.get("point_id") or "")
                if role == "command": raise ValueError("Command binding is not enabled: запись в контроллер не разрешена")
                if role not in symbol_info["slots"]: raise ValueError(f"Роль {role} не поддерживается символом {key}")
                from avic_core.graphics.binding_engine import validate_binding_config
                binding_type = str(braw.get("binding_type") or "value")
                target_property = str(braw.get("target_property") or "value")
                settings = validate_binding_config(binding_type, target_property, braw.get("settings") or {})
                binding_target = (role, target_property)
                if binding_target in binding_targets: raise ValueError(f"Для элемента уже задана привязка {role} → {target_property}")
                binding_targets.add(binding_target)
                point_row = self.core.repository.get_record(pid)
                if point_row["entity_type"] == "Point":
                    licensed_point_ids.add(pid)
                    point, _ = self.core.repository.get(pid, Point)
                    device = self.core.repository.get_record(point.device_id)
                    point_station = device["payload"].get("station_id")
                elif point_row["entity_type"] == "FBDExposedPoint":
                    point, _ = self.core.repository.get(pid, FBDExposedPoint)
                    point_station = point.station_id
                else:
                    raise ValueError("Binding target is not a Core point")
                if point_station != doc.station_id:
                    raise ValueError("Point belongs to another station (точка принадлежит другой станции)")
                checked_bindings.append({"point_id": pid, "role": role, "binding_type": binding_type, "target_property": target_property, "settings": settings})
            prepared.append({"id":eid,"name":name,"symbol_key":key,"x":x,"y":y,"width":width,"height":height,
                            "rotation":rotation,"layer":layer,"bindings":checked_bindings})

        # The transaction starts only after every element and binding has passed validation.
        with self.core.repository.transaction() as conn:
            self.core.objects.set_point_usage(f"graphics:{document_id}", licensed_point_ids, connection=conn)
            for item in prepared:
                eid=item["id"]
                if eid in existing:
                    el, ev = self.core.repository.get(eid, GraphicElement)
                    for field in ("name","symbol_key","x","y","width","height","rotation","layer"):
                        setattr(el, field, item[field])
                    el.updated_at=datetime.now(timezone.utc)
                    self.core.repository.save(el, expected_version=ev, connection=conn)
                else:
                    el=GraphicElement(name=item["name"],document_id=document_id,symbol_key=item["symbol_key"],x=item["x"],y=item["y"],
                        width=item["width"],height=item["height"],rotation=item["rotation"],layer=item["layer"],id=eid)
                    self.core.repository.save(el, connection=conn)
                for br in self.core.repository.list_records(entity_type="PointBinding"):
                    if br["payload"].get("element_id") == eid:
                        self.core.repository.delete(br["entity_id"], expected_version=br["version"], connection=conn)
                for binding in item["bindings"]:
                    self.core.repository.save(PointBinding(element_id=eid,point_id=binding["point_id"],role=binding["role"],binding_type=binding["binding_type"],target_property=binding["target_property"],settings=binding["settings"]),connection=conn)
                if item["symbol_key"] not in {"fan", "ahu_section_supply_fan"}:
                    for lr in self.core.repository.list_records(entity_type="LogicGraphicsBinding"):
                        if lr["payload"].get("graphic_element_id") == eid:
                            self.core.repository.delete(lr["entity_id"],expected_version=lr["version"],connection=conn)
            for eid,row in existing.items():
                if eid not in seen:
                    for br in self.core.repository.list_records(entity_type="PointBinding"):
                        if br["payload"].get("element_id")==eid:
                            self.core.repository.delete(br["entity_id"],expected_version=br["version"],connection=conn)
                    for lr in self.core.repository.list_records(entity_type="LogicGraphicsBinding"):
                        if lr["payload"].get("graphic_element_id") == eid:
                            self.core.repository.delete(lr["entity_id"],expected_version=lr["version"],connection=conn)
                    self.core.repository.delete(eid,expected_version=row["version"],connection=conn)
            doc.updated_at=datetime.now(timezone.utc)
            self.core.repository.save(doc,expected_version=version,connection=conn)
        self.core.audit.append(actor_id="local-engineer",action="graphics.document_saved",resource_type="graphic_document",resource_id=document_id,
                               details={"element_count":len(prepared),"revision":version+1})
        return self.get(document_id)


    def evaluate_bindings(self, document_id: str):
        """Evaluate persisted read-only bindings from the authoritative Core Point Runtime."""
        from dataclasses import asdict
        from avic_core.graphics.binding_engine import evaluate_binding
        document = self.get(document_id)
        results = {}
        sample_cache = {}
        for element in document["elements"]:
            for binding in element.get("bindings", []):
                try:
                    point_id = binding["point_id"]
                    if point_id not in sample_cache:
                        sample_cache[point_id] = self.core.point_runtime.read(point_id)
                    sample = sample_cache[point_id]
                    result = evaluate_binding(
                        binding_type=binding.get("binding_type", "value"),
                        target_property=binding.get("target_property", "value"),
                        settings=binding.get("settings", {}),
                        value=sample.value, quality=sample.quality,
                    )
                    row = asdict(result)
                    row.update({"binding_id": binding["id"], "element_id": element["id"],
                                "point_id": sample.point_id, "timestamp": sample.timestamp.isoformat() if sample.timestamp else None,
                                "unit": sample.unit, "source": sample.source, "revision": sample.revision})
                except Exception as exc:
                    row = {"binding_id": binding["id"], "element_id": element["id"],
                           "point_id": binding["point_id"], "binding_type": binding.get("binding_type", "value"),
                           "target_property": binding.get("target_property", "value"), "value": None,
                           "display_text": None, "quality": "NOT_CONNECTED", "degraded": True,
                           "visible": True, "animation_allowed": False, "interaction_allowed": False,
                           "diagnostic": "POINT_RUNTIME_UNAVAILABLE", "error_type": type(exc).__name__}
                results[binding["id"]] = row
        return {"document_id": document_id, "bindings": results}

    def create_fan_demo(self, station_id: str, name: str = "Тестовая приточная установка", point_ids: dict | None = None):
        """Create a practical fan schematic; optional points are bound by semantic role."""
        point_ids = point_ids or {}
        doc = self.create(station_id, name, "Демонстрационная схема вентиляционной установки", 1600, 900)
        fan = {"id": __import__("uuid").uuid4().__str__(), "name": "Вентилятор ПВ-1", "symbol_key": "fan",
               "x": 420, "y": 300, "width": 180, "height": 144, "rotation": 0, "layer": 10, "bindings": []}
        for role in ("value", "feedback", "alarm", "quality"):
            if point_ids.get(role): fan["bindings"].append({"point_id": point_ids[role], "role": role})
        items = [
            {"name":"Заголовок ПВ-1", "symbol_key":"sensor", "x":80,"y":55,"width":180,"height":80,"layer":1,"bindings":[]},
            {"name":"Фильтр", "symbol_key":"damper", "x":180,"y":320,"width":120,"height":96,"layer":2,"bindings":[]},
            fan,
            {"name":"Обратный клапан", "symbol_key":"valve", "x":760,"y":320,"width":120,"height":96,"layer":2,"bindings":[]},
            {"name":"Датчик температуры", "symbol_key":"sensor", "x":980,"y":290,"width":100,"height":80,"layer":3,"bindings":[]},
            {"name":"Теплообменник", "symbol_key":"heat_exchanger", "x":1160,"y":300,"width":150,"height":120,"layer":2,"bindings":[]},
            {"name":"Приточный воздух", "symbol_key":"pipe", "x":1340,"y":340,"width":180,"height":80,"layer":1,"bindings":[]},
        ]
        return self.save(doc["id"], doc["revision"], items)


    def create_modular_ahu_demo(self, station_id: str, name: str = "ПВУ с рекуперацией · модульная секционная схема"):
        """Create seven same-envelope AHU modules in an aligned left-to-right train.

        This is an offline authoring sample: point bindings can be added by the
        engineer. It does not start equipment or write to a controller.
        """
        import uuid
        doc = self.create(station_id, name,
            "Модульная приточная установка: наружная заслонка, фильтры, рекуператор, нагрев, охлаждение, вентилятор, открытый выходной короб.",
            2050, 720)
        keys = [
            ("ahu_section_outdoor_damper", "Заслонка наружного воздуха"),
            ("ahu_section_filter", "Фильтры G4/F7"),
            ("ahu_section_heat_recovery", "Пластинчатый рекуператор"),
            ("ahu_section_heating_coil", "Водяной нагреватель"),
            ("ahu_section_cooling_coil", "Водяной охладитель"),
            ("ahu_section_supply_fan", "Приточный вентилятор"),
            ("ahu_section_open_plenum", "Открытый выходной короб"),
        ]
        items = []
        for index, (key, label) in enumerate(keys):
            items.append({
                "id": str(uuid.uuid4()), "name": label, "symbol_key": key,
                "x": 18 + index * 286, "y": 155,
                "width": 286, "height": 228, "rotation": 0,
                "layer": 10 + index, "bindings": []
            })
        return self.save(doc["id"], doc["revision"], items)
