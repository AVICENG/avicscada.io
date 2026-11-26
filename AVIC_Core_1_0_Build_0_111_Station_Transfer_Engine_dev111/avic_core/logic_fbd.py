from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4, UUID


def _id(): return str(uuid4())
def _now(): return datetime.now(timezone.utc)

@dataclass(slots=True)
class LogicDocument:
    name: str
    station_id: str
    id: str = field(default_factory=_id)
    description: str = ""
    revision: int = 0
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        UUID(self.id); UUID(self.station_id)
        if not self.name.strip(): raise ValueError("Имя FBD-схемы не может быть пустым")

@dataclass(slots=True)
class LogicNode:
    document_id: str
    block_type: str
    name: str
    x: float = 40
    y: float = 40
    params: dict = field(default_factory=dict)
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    page_id: str | None = None
    def __post_init__(self):
        UUID(self.id); UUID(self.document_id)
        if self.page_id is not None: UUID(self.page_id)
        if not self.name.strip(): raise ValueError("Имя FBD-блока не может быть пустым")
        if self.block_type not in FBDService.BLOCKS: raise ValueError("Неизвестный тип FBD-блока")
        if not (0 <= self.x <= 10000 and 0 <= self.y <= 10000): raise ValueError("Координаты FBD-блока вне диапазона")

@dataclass(slots=True)
class LogicLink:
    document_id: str
    source_node_id: str
    source_port: str
    target_node_id: str
    target_port: str
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    @property
    def name(self): return f"{self.source_node_id}:{self.source_port} -> {self.target_node_id}:{self.target_port}"
    def __post_init__(self):
        for value in (self.id,self.document_id,self.source_node_id,self.target_node_id): UUID(value)
        if not self.source_port or not self.target_port: raise ValueError("Порт связи не может быть пустым")

@dataclass(slots=True)
class LogicGraphicsBinding:
    graphic_element_id: str
    logic_node_id: str
    output_port: str = "OUT"
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    @property
    def name(self): return f"{self.graphic_element_id} <- {self.logic_node_id}:{self.output_port}"
    def __post_init__(self):
        for value in (self.id,self.graphic_element_id,self.logic_node_id): UUID(value)
        if not self.output_port: raise ValueError("Выходной порт обязателен")

@dataclass(slots=True)
class StrategyPage:
    document_id: str
    name: str
    order: int = 0
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        UUID(self.id); UUID(self.document_id)
        if not self.name.strip() or len(self.name) > 120: raise ValueError("Имя страницы должно содержать 1–120 символов")
        if self.order < 0: raise ValueError("Порядок страницы не может быть отрицательным")


@dataclass(slots=True)
class StrategyConnective:
    document_id: str
    name: str
    source_page_id: str
    source_node_id: str
    source_port: str
    target_page_id: str
    target_node_id: str
    target_port: str
    signal_type: str
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        for value in (self.id, self.document_id, self.source_page_id, self.source_node_id,
                      self.target_page_id, self.target_node_id): UUID(value)
        if not self.name.strip(): raise ValueError("Имя Connective обязательно")


class FBDService:
    """Persistent typed FBD editor and deterministic simulation; no field writes."""
    BLOCKS = {
      "BOOL_INPUT":{"category":"Digital","label":"Булевый вход","inputs":{},"outputs":{"OUT":"bool"},"defaults":{"value":False}},
      "FLOAT_INPUT":{"category":"Analog","label":"Аналоговый вход","inputs":{},"outputs":{"OUT":"float"},"defaults":{"value":0.0}},
      "POINT_INPUT":{"category":"Points","label":"Точка станции","inputs":{},"outputs":{"OUT":"any"},"defaults":{}},
      "SCHEDULE":{"category":"Schedule","label":"Расписание станции","inputs":{},"outputs":{"OUT":"any"},"defaults":{"schedule_id":""}},
      "AND":{"category":"Logic","label":"И (AND)","inputs":{"A":"bool","B":"bool"},"outputs":{"OUT":"bool"},"defaults":{}},
      "OR":{"category":"Logic","label":"ИЛИ (OR)","inputs":{"A":"bool","B":"bool"},"outputs":{"OUT":"bool"},"defaults":{}},
      "NOT":{"category":"Logic","label":"НЕ (NOT)","inputs":{"IN":"bool"},"outputs":{"OUT":"bool"},"defaults":{}},
      "ADD":{"category":"Math","label":"Сложение","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "SUB":{"category":"Math","label":"Вычитание","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "MUL":{"category":"Math","label":"Умножение","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "DIV":{"category":"Math","label":"Деление","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "SELECT":{"category":"Logic","label":"Выбор значения","inputs":{"SEL":"bool","A":"float","B":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "COMPARE_GT":{"category":"Compare","label":"Больше (>)","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"bool"},"defaults":{}},
      "COMPARE_LT":{"category":"Compare","label":"Меньше (<)","inputs":{"A":"float","B":"float"},"outputs":{"OUT":"bool"},"defaults":{}},
      "LIMIT":{"category":"Analog","label":"Ограничитель диапазона","inputs":{"IN":"float","LOW":"float","HIGH":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "SCALE":{"category":"Analog","label":"Масштабирование","inputs":{"IN":"float","IN_MIN":"float","IN_MAX":"float","OUT_MIN":"float","OUT_MAX":"float"},"outputs":{"OUT":"float"},"defaults":{}},
      "HYSTERESIS":{"category":"Logic","label":"Гистерезис","inputs":{"IN":"float","LOW":"float","HIGH":"float"},"outputs":{"OUT":"bool"},"defaults":{"initial_state":False}},
      "BOOL_OUTPUT":{"category":"Data","label":"Булевый выход","inputs":{"IN":"bool"},"outputs":{},"defaults":{}},
      "FLOAT_OUTPUT":{"category":"Data","label":"Аналоговый выход","inputs":{"IN":"float"},"outputs":{},"defaults":{}},
    }
    def __init__(self, core):
        self.core=core
        self._graphic_runtime_states = {}
    def _touch_document(self, document_id):
        doc, rev = self.core.repository.get(document_id, LogicDocument)
        doc.updated_at = _now()
        self.core.repository.save(doc, expected_version=rev)
    def _station(self, station_id):
        row=self.core.repository.get_record(station_id)
        if row["entity_type"]!="Station": raise ValueError("Целевой объект не является станцией")
        return row
    def library(self):
        return [{"type":k,**v} for k,v in self.BLOCKS.items()]
    def create(self, station_id, name, description=""):
        self._station(station_id); doc=LogicDocument(name,station_id,description=description)
        self.core.repository.save(doc)
        self.core.repository.save(StrategyPage(doc.id, "Страница 1", order=0))
        self.core.audit.append(actor_id="local-engineer",action="fbd.document_created",resource_type="logic_document",resource_id=doc.id,details={"station_id":station_id})
        return self.get(doc.id)
    def list_for_station(self, station_id):
        self._station(station_id)
        return [{"id":r["entity_id"],"name":r["name"],"revision":r["version"],"description":r["payload"].get("description","")} for r in self.core.repository.list_records(entity_type="LogicDocument") if r["payload"].get("station_id")==station_id]
    def get(self, document_id):
        doc,rev=self.core.repository.get(document_id,LogicDocument)
        nodes=[]; links=[]
        for r in self.core.repository.list_records(entity_type="LogicNode"):
            if r["payload"].get("document_id")==document_id:
                n,_=self.core.repository.get(r["entity_id"],LogicNode); nodes.append({"id":n.id,"type":n.block_type,"name":n.name,"x":n.x,"y":n.y,"params":n.params,"page_id":n.page_id,"ports":self.BLOCKS[n.block_type]})
        for r in self.core.repository.list_records(entity_type="LogicLink"):
            if r["payload"].get("document_id")==document_id:
                l,_=self.core.repository.get(r["entity_id"],LogicLink); links.append({"id":l.id,"source_node_id":l.source_node_id,"source_port":l.source_port,"target_node_id":l.target_node_id,"target_port":l.target_port})
        pages = sorted([{"id":r["entity_id"], "name":r["name"], "order":r["payload"].get("order",0)}
                        for r in self.core.repository.list_records(entity_type="StrategyPage")
                        if r["payload"].get("document_id")==document_id], key=lambda x:(x["order"],x["name"]))
        if not pages:
            page=StrategyPage(document_id, "Страница 1", order=0); self.core.repository.save(page)
            pages=[{"id":page.id,"name":page.name,"order":page.order}]
        page_ids={p["id"] for p in pages}
        connectives=[]
        for r in self.core.repository.list_records(entity_type="StrategyConnective"):
            if r["payload"].get("document_id")==document_id:
                c,_=self.core.repository.get(r["entity_id"],StrategyConnective)
                connectives.append({"id":c.id,"name":c.name,"source_page_id":c.source_page_id,
                    "source_node_id":c.source_node_id,"source_port":c.source_port,
                    "target_page_id":c.target_page_id,"target_node_id":c.target_node_id,
                    "target_port":c.target_port,"signal_type":c.signal_type})
        return {"id":doc.id,"station_id":doc.station_id,"name":doc.name,"description":doc.description,
                "revision":rev,"pages":pages,"connectives":connectives,"nodes":nodes,"links":links,
                "execution_mode":"SIMULATION_ONLY","field_writes_enabled":False}
    def save(self, document_id, expected_revision, nodes, links):
        import math
        doc,rev=self.core.repository.get(document_id,LogicDocument)
        if rev!=expected_revision: raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {rev}")
        if not isinstance(nodes,list) or not isinstance(links,list) or len(nodes)>1000 or len(links)>5000: raise ValueError("Недопустимый размер FBD-графа")
        old_nodes={r["entity_id"]:r for r in self.core.repository.list_records(entity_type="LogicNode") if r["payload"].get("document_id")==document_id}
        old_links={r["entity_id"]:r for r in self.core.repository.list_records(entity_type="LogicLink") if r["payload"].get("document_id")==document_id}
        prepared=[]; seen=set(); port_types={}; node_types={}
        for i,raw in enumerate(nodes):
            if not isinstance(raw,dict): raise ValueError(f"Узел {i}: ожидался объект")
            nid=str(raw.get("id") or uuid4()); UUID(nid)
            if nid in seen: raise ValueError("Повторный идентификатор FBD-блока")
            seen.add(nid)
            if nid in {r["entity_id"] for r in self.core.repository.list_records(entity_type="LogicNode")} and nid not in old_nodes: raise ValueError("FBD-блок принадлежит другой схеме")
            typ=str(raw.get("type") or raw.get("block_type") or ""); spec=self.BLOCKS.get(typ)
            if not spec: raise ValueError(f"Неизвестный тип FBD-блока: {typ}")
            def coord(k):
                v=float(raw.get(k,40))
                if not math.isfinite(v) or not 0<=v<=10000: raise ValueError(f"Координата {k} вне диапазона")
                return v
            params=raw.get("params") or {}
            if not isinstance(params,dict): raise ValueError("Параметры FBD-блока должны быть объектом")
            if typ=="BOOL_INPUT" and not isinstance(params.get("value",False),bool): raise ValueError("BOOL_INPUT.value должен быть bool")
            if typ=="FLOAT_INPUT":
                val=params.get("value",0.0)
                if isinstance(val,bool) or not isinstance(val,(int,float)) or not math.isfinite(float(val)): raise ValueError("FLOAT_INPUT.value должен быть конечным числом")
                params={"value":float(val)}
            studio_module_id = (raw.get("params") or {}).get("_studio_module_id")
            if studio_module_id:
                params["_studio_module_id"] = str(studio_module_id)
            if typ=="SCHEDULE":
                schedule_id=str(params.get("schedule_id") or "").strip()
                if not schedule_id: raise ValueError("Для блока «Расписание станции» выберите сохранённое расписание")
                schedule=self.core.schedules.get(schedule_id)
                if schedule["station_id"] != doc.station_id:
                    raise ValueError("Расписание принадлежит другой станции; межстанционная связь не разрешена")
                params={"schedule_id":schedule_id}
            name=str(raw.get("name") or spec["label"]).strip()
            if not name or len(name)>120: raise ValueError("Имя FBD-блока должно содержать 1–120 символов")
            pages_for_doc=[r for r in self.core.repository.list_records(entity_type="StrategyPage") if r["payload"].get("document_id")==document_id]
            default_page=sorted(pages_for_doc,key=lambda r:r["payload"].get("order",0))[0]["entity_id"] if pages_for_doc else None
            page_id=raw.get("page_id") or default_page
            if page_id and not any(r["entity_id"]==page_id and r["payload"].get("document_id")==document_id for r in pages_for_doc):
                raise ValueError("FBD-блок ссылается на страницу другой стратегии или отсутствующую страницу")
            prepared.append({"id":nid,"type":typ,"name":name,"x":coord("x"),"y":coord("y"),"params":params,"page_id":page_id})
            node_types[nid]=typ
            for p,t in spec["inputs"].items(): port_types[(nid,"in",p)]=t
            for p,t in spec["outputs"].items():
                if typ == "POINT_INPUT":
                    point_id = str(params.get("point_id") or "")
                    from avic_core.domain.models import Point
                    point, _ = self.core.repository.get(point_id, Point)
                    device_row = self.core.repository.get_record(point.device_id)
                    if device_row["entity_type"] != "Device" or device_row["payload"].get("station_id") != doc.station_id:
                        raise ValueError("Точка FBD принадлежит другой станции")
                    resolved = self._point_signal_type(point.data_type)
                    if not resolved:
                        raise ValueError(f"Неподдерживаемый тип точки для FBD: {point.data_type}")
                    params = {**params, "data_type": resolved, "source_name": point.name, "unit": point.unit,
                              "native_identity": point.native_identity}
                    port_types[(nid,"out",p)] = resolved
                elif typ == "SCHEDULE":
                    schedule = self.core.schedules.get(params["schedule_id"])
                    schedule_type = schedule["value_type"]
                    port_types[(nid,"out",p)] = {"BOOLEAN":"bool", "NUMERIC":"float", "STRING":"string", "ENUM":"any"}[schedule_type]
                else:
                    port_types[(nid,"out",p)] = t
            # POINT_INPUT resolves its declared signal type after the node draft
            # was first assembled. Persist the resolved metadata with that draft.
            prepared[-1]["params"] = params
        links_prepared=[]; link_ids=set(); occupied=set(); adjacency={n:set() for n in node_types}
        connective_rows=[r for r in self.core.repository.list_records(entity_type="StrategyConnective") if r["payload"].get("document_id")==document_id]
        connective_occupied={(r["payload"].get("target_node_id"),r["payload"].get("target_port")) for r in connective_rows}
        referenced_nodes={r["payload"].get("source_node_id") for r in connective_rows}|{r["payload"].get("target_node_id") for r in connective_rows}
        if not referenced_nodes.issubset(seen):
            raise ValueError("Нельзя удалить блок, используемый межстраничным Connective")
        for row in connective_rows:
            if row["payload"].get("source_node_id") in node_types and row["payload"].get("target_node_id") in node_types:
                src_page=next((n["page_id"] for n in prepared if n["id"]==row["payload"].get("source_node_id")),None)
                dst_page=next((n["page_id"] for n in prepared if n["id"]==row["payload"].get("target_node_id")),None)
                if src_page!=row["payload"].get("source_page_id") or dst_page!=row["payload"].get("target_page_id"):
                    raise ValueError("Нельзя переместить блок, используемый межстраничным Connective, без перенастройки связи")
        all_link_ids={r["entity_id"] for r in self.core.repository.list_records(entity_type="LogicLink")}
        for i,raw in enumerate(links):
            if not isinstance(raw,dict): raise ValueError(f"Связь {i}: ожидался объект")
            lid=str(raw.get("id") or uuid4()); UUID(lid)
            if lid in link_ids: raise ValueError("Повторный идентификатор FBD-связи")
            link_ids.add(lid)
            if lid in all_link_ids and lid not in old_links: raise ValueError("FBD-связь принадлежит другой схеме")
            sn=str(raw.get("source_node_id") or ""); tn=str(raw.get("target_node_id") or "")
            sp=str(raw.get("source_port") or "OUT"); tp=str(raw.get("target_port") or "")
            if sn not in node_types or tn not in node_types: raise ValueError("Связь ссылается на отсутствующий блок")
            st=port_types.get((sn,"out",sp)); tt=port_types.get((tn,"in",tp))
            if st is None or tt is None: raise ValueError("Связь ссылается на отсутствующий порт или неверное направление")
            if st!=tt and st!="any" and tt!="any": raise ValueError(f"Несовместимые типы портов: {st} → {tt}")
            if (tn,tp) in occupied or (tn,tp) in connective_occupied: raise ValueError("Входной порт уже занят")
            occupied.add((tn,tp)); adjacency[sn].add(tn)
            links_prepared.append({"id":lid,"source_node_id":sn,"source_port":sp,"target_node_id":tn,"target_port":tp})
        # Include cross-page Connectives in cycle detection, then use iterative
        # Kahn traversal. Recursive DFS fails on valid long chains near the 1000-node limit.
        for row in connective_rows:
            source_id = row["payload"].get("source_node_id")
            target_id = row["payload"].get("target_node_id")
            if source_id in adjacency and target_id in adjacency:
                adjacency[source_id].add(target_id)
        from collections import deque
        indegree = {node_id: 0 for node_id in adjacency}
        for source_id, targets in adjacency.items():
            for target_id in targets:
                indegree[target_id] += 1
        ready = deque(node_id for node_id in adjacency if indegree[node_id] == 0)
        visited_count = 0
        while ready:
            node_id = ready.popleft()
            visited_count += 1
            for target_id in adjacency[node_id]:
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    ready.append(target_id)
        if visited_count != len(adjacency):
            raise ValueError("Циклическая зависимость в FBD-схеме")
        with self.core.repository.transaction() as conn:
            for item in prepared:
                if item["id"] in old_nodes:
                    obj,ov=self.core.repository.get(item["id"],LogicNode)
                    for k in ("block_type","name","x","y","params","page_id"): setattr(obj,k,item["type"] if k=="block_type" else item[k])
                    obj.updated_at=_now(); self.core.repository.save(obj,expected_version=ov,connection=conn)
                else:self.core.repository.save(LogicNode(document_id, item["type"],item["name"],item["x"],item["y"],item["params"],id=item["id"],page_id=item["page_id"]),connection=conn)
            for nid,row in old_nodes.items():
                if nid not in seen:self.core.repository.delete(nid,expected_version=row["version"],connection=conn)
            for lid,row in old_links.items():self.core.repository.delete(lid,expected_version=row["version"],connection=conn)
            for l in links_prepared:self.core.repository.save(LogicLink(document_id,l["source_node_id"],l["source_port"],l["target_node_id"],l["target_port"],id=l["id"]),connection=conn)
            doc.updated_at=_now();self.core.repository.save(doc,expected_version=rev,connection=conn)
        self.core.audit.append(actor_id="local-engineer",action="fbd.document_saved",resource_type="logic_document",resource_id=document_id,details={"nodes":len(prepared),"links":len(links_prepared),"revision":rev+1})
        return self.get(document_id)
    @staticmethod
    def _point_signal_type(data_type):
        value = str(data_type or "").strip().casefold()
        if value in {"bool", "boolean", "binary", "digital", "digital input", "digital output"} or value.startswith(("binary-", "digital-")):
            return "bool"
        if value in {"int", "integer", "uint", "counter", "long"} or value.startswith(("multi-state", "integer-")):
            return "int"
        if value in {"float", "double", "real", "analog", "numeric", "number"} or value.startswith(("analog-", "real-")):
            return "float"
        if value in {"string", "text", "char"}:
            return "string"
        return None

    def add_point_node(self, document_id, point_id, *, page_id=None, x=40, y=40):
        """Place a real station point as a read-only FBD source block."""
        from avic_core.domain.models import Point
        doc, rev = self.core.repository.get(document_id, LogicDocument)
        point, _ = self.core.repository.get(point_id, Point)
        device_row = self.core.repository.get_record(point.device_id)
        if device_row["entity_type"] != "Device" or device_row["payload"].get("station_id") != doc.station_id:
            raise ValueError("Точка не принадлежит станции этой FBD-стратегии")
        signal_type = self._point_signal_type(point.data_type)
        if signal_type is None:
            raise ValueError(f"Неподдерживаемый тип точки для FBD: {point.data_type}")
        graph = self.get(document_id)
        selected_page = page_id or (graph["pages"][0]["id"] if graph["pages"] else None)
        if selected_page not in {p["id"] for p in graph["pages"]}:
            raise ValueError("Целевая страница не принадлежит стратегии")
        node = {"id": _id(), "type": "POINT_INPUT", "name": point.name,
                "x": float(x), "y": float(y), "page_id": selected_page,
                "params": {"point_id": point.id, "data_type": signal_type, "source_name": point.name,
                           "unit": point.unit, "native_identity": point.native_identity}}
        return self.save(document_id, rev, graph["nodes"] + [node], graph["links"])

    def add_page(self, document_id, name):
        doc,_=self.core.repository.get(document_id,LogicDocument)
        pages=[r for r in self.core.repository.list_records(entity_type="StrategyPage") if r["payload"].get("document_id")==document_id]
        if len(pages)>=256: raise ValueError("Достигнут лимит 256 страниц стратегии")
        if any(r["name"].casefold()==name.strip().casefold() for r in pages): raise ValueError("Страница с таким именем уже существует")
        page=StrategyPage(document_id,name,order=len(pages)); self.core.repository.save(page)
        self._touch_document(document_id)
        self.core.audit.append(actor_id="local-engineer",action="fbd.page_created",resource_type="fbd_page",resource_id=page.id,details={"document_id":document_id})
        return self.get(document_id)

    def rename_page(self, document_id, page_id, name):
        page,rev=self.core.repository.get(page_id,StrategyPage)
        if page.document_id!=document_id: raise ValueError("Страница принадлежит другой стратегии")
        clean_name=name.strip()
        if not clean_name or len(clean_name)>120: raise ValueError("Имя страницы должно содержать 1–120 символов")
        if any(r["entity_id"]!=page_id and r["name"].casefold()==clean_name.casefold()
               for r in self.core.repository.list_records(entity_type="StrategyPage")
               if r["payload"].get("document_id")==document_id):
            raise ValueError("Страница с таким именем уже существует")
        page.name=clean_name; page.updated_at=_now()
        self.core.repository.save(page,expected_version=rev)
        self._touch_document(document_id)
        return self.get(document_id)

    def delete_page(self, document_id, page_id):
        pages=[r for r in self.core.repository.list_records(entity_type="StrategyPage") if r["payload"].get("document_id")==document_id]
        page,rev=self.core.repository.get(page_id,StrategyPage)
        if page.document_id!=document_id: raise ValueError("Страница принадлежит другой стратегии")
        if len(pages)<=1: raise ValueError("Нельзя удалить последнюю страницу стратегии")
        if any(r["payload"].get("document_id")==document_id and r["payload"].get("page_id")==page_id for r in self.core.repository.list_records(entity_type="LogicNode")):
            raise ValueError("Нельзя удалить страницу, на которой размещены блоки")
        if any(page_id in (r["payload"].get("source_page_id"),r["payload"].get("target_page_id")) for r in self.core.repository.list_records(entity_type="StrategyConnective") if r["payload"].get("document_id")==document_id):
            raise ValueError("Сначала удалите межстраничные Connective")
        self.core.repository.delete(page_id,expected_version=rev)
        self._touch_document(document_id)
        return self.get(document_id)

    def create_connective(self, document_id, payload):
        graph=self.get(document_id)
        pages={p["id"] for p in graph["pages"]}
        sp,tp=payload.get("source_page_id"),payload.get("target_page_id")
        sn,tn=payload.get("source_node_id"),payload.get("target_node_id")
        source=next((n for n in graph["nodes"] if n["id"]==sn),None)
        target=next((n for n in graph["nodes"] if n["id"]==tn),None)
        if sp not in pages or tp not in pages or sp==tp: raise ValueError("Connective должен связывать две разные страницы одной стратегии")
        if not source or not target: raise ValueError("Connective ссылается на отсутствующий блок")
        spec_s=self.BLOCKS[source["type"]]; spec_t=self.BLOCKS[target["type"]]
        sport=payload.get("source_port","OUT"); tport=payload.get("target_port")
        st=spec_s["outputs"].get(sport); tt=spec_t["inputs"].get(tport)
        if st == "any" and source["type"] == "POINT_INPUT":
            source_params = source.get("params") if isinstance(source.get("params"), dict) else {}
            st = source_params.get("data_type")
            if not st:
                from avic_core.domain.models import Point
                point, _ = self.core.repository.get(str(source_params.get("point_id") or ""), Point)
                st = self._point_signal_type(point.data_type)
        elif st == "any" and source["type"] == "SCHEDULE":
            source_params = source.get("params") if isinstance(source.get("params"), dict) else {}
            schedule_id = str(source_params.get("schedule_id") or "")
            schedule = self.core.schedules.get(schedule_id)
            if schedule["station_id"] != graph["station_id"]:
                raise ValueError("Расписание Connective принадлежит другой станции")
            st = {"BOOLEAN":"bool", "NUMERIC":"float", "STRING":"string", "ENUM":"any"}.get(schedule["value_type"])
        if not st or st!=tt: raise ValueError("Несовместимые типы портов Connective")
        if source.get("page_id") not in (None,sp) or target.get("page_id") not in (None,tp):
            raise ValueError("Блоки Connective должны находиться на указанных страницах")
        if any(l["target_node_id"]==tn and l["target_port"]==tport for l in graph["links"]):
            raise ValueError("Входной порт уже занят обычной связью")
        existing_connectives=graph["connectives"]
        if any(c["target_node_id"]==tn and c["target_port"]==tport for c in existing_connectives):
            raise ValueError("Входной порт уже занят межстраничным Connective")
        adjacency={n["id"]:set() for n in graph["nodes"]}
        for l in graph["links"]: adjacency[l["source_node_id"]].add(l["target_node_id"])
        for c0 in existing_connectives: adjacency[c0["source_node_id"]].add(c0["target_node_id"])
        adjacency[sn].add(tn)
        visiting=set(); visited=set()
        def visit_connective(node_id):
            if node_id in visiting: raise ValueError("Connective создаёт циклическую зависимость стратегии")
            if node_id in visited: return
            visiting.add(node_id)
            for nxt in adjacency[node_id]: visit_connective(nxt)
            visiting.remove(node_id); visited.add(node_id)
        for node_id in adjacency: visit_connective(node_id)
        c=StrategyConnective(document_id,str(payload.get("name") or "Connective").strip(),sp,sn,sport,tp,tn,tport,st)
        self.core.repository.save(c)
        self._touch_document(document_id)
        self.core.audit.append(actor_id="local-engineer",action="fbd.connective_created",resource_type="fbd_connective",resource_id=c.id,details={"document_id":document_id})
        return self.get(document_id)

    def delete_connective(self, document_id, connective_id):
        c,rev=self.core.repository.get(connective_id,StrategyConnective)
        if c.document_id!=document_id: raise ValueError("Connective принадлежит другой стратегии")
        self.core.repository.delete(connective_id,expected_version=rev)
        self._touch_document(document_id)
        return self.get(document_id)

    @staticmethod
    def _validate_simulation_value(signal_type, value, *, node_name):
        import math
        if signal_type == "bool":
            if not isinstance(value, bool):
                raise ValueError(f"Блок «{node_name}»: требуется BOOL, получено {type(value).__name__}")
            return value
        if signal_type == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise ValueError(f"Блок «{node_name}»: требуется конечное числовое значение")
            return float(value)
        if signal_type == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"Блок «{node_name}»: требуется INT")
            return value
        if signal_type == "string":
            if not isinstance(value, str):
                raise ValueError(f"Блок «{node_name}»: требуется STRING")
            return value
        if isinstance(value, (dict, list, tuple, set)):
            raise ValueError(f"Блок «{node_name}»: составное значение не поддерживается")
        return value

    def simulate(self, document_id, inputs=None, runtime_state=None):
        """Run an isolated FBD pass. Optional mutable state is committed only after a successful pass."""
        graph = self.get(document_id)
        if inputs is None:
            inputs = {}
        if not isinstance(inputs, dict):
            raise ValueError("Параметры симуляции должны быть объектом node_id → value")
        nodes = {n["id"]: n for n in graph["nodes"]}
        overridable = {nid for nid, node in nodes.items()
                       if node["type"].endswith("_INPUT") and node["type"] != "POINT_INPUT"}
        unknown = set(inputs) - overridable
        if unknown:
            raise ValueError("Переопределять можно только виртуальные входы; POINT_INPUT недоступен: " + ", ".join(sorted(unknown)))
        incoming = {}
        for link in graph["links"]:
            incoming[(link["target_node_id"], link["target_port"])] = (link["source_node_id"], link["source_port"])
        for connective in graph.get("connectives", []):
            incoming[(connective["target_node_id"], connective["target_port"])] = (connective["source_node_id"], connective["source_port"])
        # Build a deterministic topological order in O(V + E log V).
        # The previous repeated pending-set scan could become quadratic on long FBD chains.
        import heapq
        values, diagnostics = {}, {}
        state_work = dict(runtime_state or {})
        node_order = {node_id: index for index, node_id in enumerate(nodes)}
        indegree = {node_id: 0 for node_id in nodes}
        downstream = {node_id: [] for node_id in nodes}
        for target_id, target_node in nodes.items():
            for port in self.BLOCKS[target_node["type"]]["inputs"]:
                dependency = incoming.get((target_id, port))
                if dependency is None:
                    continue
                source_id, _source_port = dependency
                if source_id not in nodes:
                    raise ValueError("FBD-связь ссылается на отсутствующий исходный блок")
                downstream[source_id].append(target_id)
                indegree[target_id] += 1
        ready = [(node_order[node_id], node_id) for node_id, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        execution_order = []
        while ready:
            _position, node_id = heapq.heappop(ready)
            execution_order.append(node_id)
            for target_id in downstream[node_id]:
                indegree[target_id] -= 1
                if indegree[target_id] == 0:
                    heapq.heappush(ready, (node_order[target_id], target_id))
        if len(execution_order) != len(nodes):
            raise ValueError("Не удалось вычислить FBD-граф: цикл или незамкнутая зависимость")
        for node_id in execution_order:
            node = nodes[node_id]; spec = self.BLOCKS[node["type"]]
            deps = [incoming.get((node_id, port)) for port in spec["inputs"]]
            if any(dep and (dep[0], dep[1]) not in values for dep in deps):
                raise ValueError("FBD-связь ссылается на отсутствующий выходной порт")
            args = {}
            for port, signal_type in spec["inputs"].items():
                dep = incoming.get((node_id, port))
                raw = values.get(dep) if dep else (False if signal_type == "bool" else "" if signal_type == "string" else 0)
                args[port] = self._validate_simulation_value(signal_type, raw, node_name=node["name"])
            typ, params, source_meta = node["type"], node["params"], None
            if typ == "POINT_INPUT":
                from avic_core.domain.models import Point
                point, _ = self.core.repository.get(str(params.get("point_id") or ""), Point)
                live = self.core.point_runtime.read(point.id)
                if live.quality != "GOOD":
                    raise ValueError(f"Точка «{point.name}» имеет качество {live.quality}; сигнал не допускается в расчёт")
                if live.value is None:
                    raise ValueError(f"Точка «{point.name}» не имеет текущего значения")
                out = self._validate_simulation_value(params.get("data_type", "any"), live.value, node_name=node["name"])
                source_meta = {"kind": "station_point", "point_id": point.id, "source": live.source,
                               "quality": live.quality, "timestamp": live.timestamp.isoformat() if live.timestamp else None,
                               "unit": live.unit, "revision": live.revision}
            elif typ.endswith("_INPUT"):
                raw = inputs.get(node_id, params.get("value", spec["defaults"].get("value")))
                out = self._validate_simulation_value(spec["outputs"].get("OUT", "any"), raw, node_name=node["name"])
                source_meta = {"kind": "virtual_simulation_input", "overridden": node_id in inputs}
            elif typ == "SCHEDULE":
                schedule_id = str(params.get("schedule_id") or "")
                schedule = self.core.schedules.get(schedule_id)
                if schedule["station_id"] != graph["station_id"]:
                    raise ValueError(f"Расписание блока «{node['name']}» принадлежит другой станции")
                evaluated = self.core.schedules.evaluate(schedule_id)
                value_type = evaluated["value_type"]
                signal_type = {"BOOLEAN":"bool", "NUMERIC":"float", "STRING":"string", "ENUM":"any"}[value_type]
                out = self._validate_simulation_value(signal_type, evaluated["value"], node_name=node["name"])
                source_meta = {"kind":"station_schedule", "schedule_id":schedule_id,
                               "schedule_name":schedule["name"], "schedule_revision":schedule["revision"],
                               "value_type":value_type, "source":evaluated["source"],
                               "evaluated_at":evaluated["evaluated_at"], "local_time":evaluated["local_time"],
                               "timezone":evaluated["timezone"], "next_change":evaluated["next_change"],
                               "output_mode":"INTENT_ONLY_NO_FIELD_WRITE"}
            elif typ == "AND": out = bool(args["A"] and args["B"])
            elif typ == "OR": out = bool(args["A"] or args["B"])
            elif typ == "NOT": out = not bool(args["IN"])
            elif typ == "ADD": out = float(args["A"]) + float(args["B"])
            elif typ == "SUB": out = float(args["A"]) - float(args["B"])
            elif typ == "MUL": out = float(args["A"]) * float(args["B"])
            elif typ == "DIV":
                denominator = float(args["B"])
                if denominator == 0.0:
                    raise ValueError(f"Блок «{node['name']}»: деление на ноль запрещено")
                out = float(args["A"]) / denominator
            elif typ == "SELECT": out = float(args["A"]) if args["SEL"] else float(args["B"])
            elif typ == "COMPARE_GT": out = float(args["A"]) > float(args["B"])
            elif typ == "COMPARE_LT": out = float(args["A"]) < float(args["B"])
            elif typ == "LIMIT":
                low, high = float(args["LOW"]), float(args["HIGH"])
                if low > high: raise ValueError("LIMIT: LOW не может быть больше HIGH")
                out = max(low, min(high, float(args["IN"])))
            elif typ == "SCALE":
                low, high = float(args["IN_MIN"]), float(args["IN_MAX"])
                if low == high: raise ValueError("SCALE: IN_MIN и IN_MAX не должны совпадать")
                out_low, out_high = float(args["OUT_MIN"]), float(args["OUT_MAX"])
                out = out_low + ((float(args["IN"]) - low) / (high - low)) * (out_high - out_low)
                if params.get("clamp_output", False):
                    out = max(min(out_low, out_high), min(max(out_low, out_high), out))
            elif typ == "HYSTERESIS":
                low, high, value = float(args["LOW"]), float(args["HIGH"]), float(args["IN"])
                if low >= high:
                    raise ValueError(f"Блок «{node['name']}»: LOW должен быть строго меньше HIGH")
                previous = state_work.get(node_id, bool(params.get("initial_state", False)))
                if not isinstance(previous, bool):
                    raise ValueError(f"Блок «{node['name']}»: повреждено сохранённое состояние HYSTERESIS")
                out = True if (not previous and value >= high) else False if (previous and value <= low) else previous
                state_work[node_id] = out
            elif typ in {"BOOL_OUTPUT", "FLOAT_OUTPUT"}: out = args["IN"]
            else: raise ValueError(f"Нет симулятора для блока {typ}")
            if spec["outputs"]:
                out = self._validate_simulation_value(spec["outputs"].get("OUT", "any"), out, node_name=node["name"])
                values[(node_id, "OUT")] = out; port = "OUT"
            else:
                values[(node_id, "IN")] = out; port = "IN"
            diagnostics[node_id] = {"name": node["name"], "block_type": typ, "status": "GOOD",
                                    "output_port": port, "value": out, "source": source_meta}
        outputs = {n["name"]: values.get((n["id"], "IN")) for n in graph["nodes"] if n["type"].endswith("_OUTPUT")}
        if runtime_state is not None:
            runtime_state.clear()
            runtime_state.update(state_work)
        return {"document_id": document_id, "outputs": outputs,
                "node_values": {f"{k[0]}:{k[1]}": v for k, v in values.items()},
                "node_diagnostics": diagnostics, "mode": "SIMULATION_ONLY",
                "runtime_state": dict(state_work),
                "field_writes_performed": False, "runtime_published": False}
    def create_fan_demo(self, station_id):
        doc=self.create(station_id,"ПВ-1 · Разрешение вентилятора","Демонстрационная логика: Пуск разрешён И защитная цепь исправна")
        nodes=[{"id":_id(),"type":"BOOL_INPUT","name":"Команда Пуск","x":40,"y":80,"params":{"value":True}},
               {"id":_id(),"type":"BOOL_INPUT","name":"Защита исправна","x":40,"y":220,"params":{"value":True}},
               {"id":_id(),"type":"AND","name":"Разрешение ПВ-1","x":300,"y":150},
               {"id":_id(),"type":"BOOL_OUTPUT","name":"Вентилятор: RUN","x":560,"y":150}]
        links=[{"source_node_id":nodes[0]["id"],"source_port":"OUT","target_node_id":nodes[2]["id"],"target_port":"A"},{"source_node_id":nodes[1]["id"],"source_port":"OUT","target_node_id":nodes[2]["id"],"target_port":"B"},{"source_node_id":nodes[2]["id"],"source_port":"OUT","target_node_id":nodes[3]["id"],"target_port":"IN"}]
        return self.save(doc["id"],doc["revision"],nodes,links)
    def bind_graphic_output(self, graphic_element_id, logic_node_id, output_port="OUT"):
        from avic_core.graphics.models import GraphicElement
        el,_=self.core.repository.get(graphic_element_id,GraphicElement); doc,_=self.core.repository.get(logic_node_id,LogicNode)
        from avic_core.graphics.models import GraphicDocument
        gdoc,_=self.core.repository.get(el.document_id,GraphicDocument)
        ldoc,_=self.core.repository.get(doc.document_id,LogicDocument)
        if gdoc.station_id!=ldoc.station_id: raise ValueError("Мнемосхема и FBD должны принадлежать одной станции")
        if el.symbol_key not in {"fan", "ahu_section_supply_fan"}: raise ValueError("Выход FBD можно привязать только к символу вентилятора или секции приточного вентилятора ПВУ")
        spec=self.BLOCKS[doc.block_type]
        if spec["outputs"].get(output_port)!="bool": raise ValueError("Для индикации вентилятора требуется BOOL-выход FBD")
        binding=LogicGraphicsBinding(graphic_element_id,logic_node_id,output_port)
        with self.core.repository.transaction() as conn:
            for row in self.core.repository.list_records(entity_type="LogicGraphicsBinding"):
                if row["payload"].get("graphic_element_id") == graphic_element_id:
                    self.core.repository.delete(row["entity_id"], expected_version=row["version"], connection=conn)
            self.core.repository.save(binding, connection=conn)
        return {"id":binding.id,"graphic_element_id":graphic_element_id,"logic_node_id":logic_node_id,"output_port":output_port}

    def evaluate_graphic_bindings(self, graphic_document_id):
        """Evaluate read-only FBD outputs linked to elements on one graphic document.

        POINT_INPUT nodes are resolved through Core Point Runtime by simulate(); any
        non-GOOD input or simulation error fails closed and cannot animate a fan.
        """
        from avic_core.graphics.models import GraphicDocument, GraphicElement
        graphic, _ = self.core.repository.get(graphic_document_id, GraphicDocument)
        elements = {r["entity_id"]: r for r in self.core.repository.list_records(entity_type="GraphicElement")
                    if r["payload"].get("document_id") == graphic_document_id}
        bindings = [r for r in self.core.repository.list_records(entity_type="LogicGraphicsBinding")
                    if r["payload"].get("graphic_element_id") in elements]
        simulations = {}
        results = {}
        for row in bindings:
            binding_id = row["entity_id"]
            payload = row["payload"]
            element_id = payload.get("graphic_element_id")
            node_id = payload.get("logic_node_id")
            port = payload.get("output_port", "OUT")
            try:
                node, _ = self.core.repository.get(node_id, LogicNode)
                logic_doc, _ = self.core.repository.get(node.document_id, LogicDocument)
                if logic_doc.station_id != graphic.station_id:
                    raise ValueError("FBD и мнемосхема принадлежат разным станциям")
                spec = self.BLOCKS[node.block_type]
                signal_type = spec["outputs"].get(port)
                if signal_type != "bool":
                    raise ValueError("Для анимации вентилятора требуется BOOL-выход FBD")
                if logic_doc.id not in simulations:
                    logic_graph = self.get(logic_doc.id)
                    state_key = f"{logic_doc.id}:{logic_graph['revision']}"
                    runtime_state = self._graphic_runtime_states.setdefault(state_key, {})
                    simulations[logic_doc.id] = self.simulate(logic_doc.id, runtime_state=runtime_state)
                simulation = simulations[logic_doc.id]
                key = f"{node_id}:{port}"
                if key not in simulation["node_values"]:
                    raise ValueError("Выход FBD отсутствует в результатах расчёта")
                diagnostic = simulation.get("node_diagnostics", {}).get(node_id, {})
                value = simulation["node_values"][key]
                if not isinstance(value, bool) or diagnostic.get("status") != "GOOD":
                    raise ValueError("FBD не вернул достоверный BOOL")
                results[binding_id] = {"binding_id": binding_id, "element_id": element_id,
                    "logic_node_id": node_id, "output_port": port, "value": value,
                    "quality": "GOOD", "diagnostic": None, "field_writes_performed": False}
            except Exception as exc:
                results[binding_id] = {"binding_id": binding_id, "element_id": element_id,
                    "logic_node_id": node_id, "output_port": port, "value": None,
                    "quality": "BAD", "diagnostic": str(exc), "field_writes_performed": False}
        return {"document_id": graphic_document_id, "bindings": results,
                "mode": "SIMULATION_ONLY", "runtime_published": False,
                "field_writes_performed": False}
