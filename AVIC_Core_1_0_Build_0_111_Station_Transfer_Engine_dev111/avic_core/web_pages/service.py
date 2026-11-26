from __future__ import annotations
from datetime import datetime, timezone
import re
import math
from avic_core.web_pages.models import WebPageNode
from avic_core.web_pages.assets import RepositoryAsset
import base64
from hashlib import sha256
from uuid import UUID
from avic_core.repository.sqlite_repository import EntityNotFound

class WebPagesService:
    """Station-scoped page tree, visual layout, repository assets and controlled publication."""
    @staticmethod
    def _slugify(value):
        table=str.maketrans({"а":"a","б":"b","в":"v","г":"g","д":"d","е":"e","ё":"e","ж":"zh","з":"z","и":"i","й":"y","к":"k","л":"l","м":"m","н":"n","о":"o","п":"p","р":"r","с":"s","т":"t","у":"u","ф":"f","х":"kh","ц":"ts","ч":"ch","ш":"sh","щ":"shch","ъ":"","ы":"y","ь":"","э":"e","ю":"yu","я":"ya"})
        value=value.lower().translate(table)
        return re.sub(r"[^a-z0-9]+","-",value).strip("-")
    def __init__(self, core): self.core=core

    @staticmethod
    def _validate_layout(node: WebPageNode) -> None:
        if not isinstance(node.layout, list) or len(node.layout) > 500:
            raise ValueError("На странице допускается не более 500 визуальных компонентов")
        allowed_types = {"heading", "text", "button", "card", "image", "divider", "value", "graphic"}
        safe_colors = re.compile(r"^(#[0-9a-fA-F]{3,8}|[a-zA-Z]{1,24})$")
        for index, block in enumerate(node.layout):
            if not isinstance(block, dict):
                raise ValueError(f"Компонент страницы {index + 1} должен быть объектом")
            kind = block.get("type") or ("graphic" if block.get("graphic_id") else "text")
            if not isinstance(kind, str) or kind not in allowed_types:
                raise ValueError(f"Компонент страницы {index + 1}: тип {kind!r} не поддерживается")
            if "graphic_id" in block and block["graphic_id"] not in node.graphic_ids:
                raise ValueError("Блок ссылается на мнемосхему, не назначенную странице")
            if kind == "graphic" and not block.get("graphic_id"):
                raise ValueError("Компонент «Мнемосхема» должен ссылаться на назначенную графику")
            for key in ("x", "y", "width", "height"):
                value = block.get(key, 0 if key in {"x", "y"} else 240)
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 10000:
                    raise ValueError(f"Компонент {index + 1}: некорректное значение геометрии {key}")
            min_height = 1 if kind == "divider" else 12
            if block.get("width", 240) < 20 or block.get("height", 100) < min_height:
                raise ValueError(f"Компонент {index + 1}: минимальный размер 20×{min_height} px")
            for key, limit in (("label", 4000), ("text", 10000), ("title", 500), ("alt", 500)):
                value = block.get(key, "")
                if not isinstance(value, str) or len(value) > limit:
                    raise ValueError(f"Компонент {index + 1}: поле {key} превышает допустимый размер")
            for key in ("color", "background"):
                value = block.get(key)
                if value is not None and (not isinstance(value, str) or not safe_colors.fullmatch(value)):
                    raise ValueError(f"Компонент {index + 1}: недопустимый цвет {key}")
            align = block.get("align", "left")
            if not isinstance(align, str) or align not in {"left", "center", "right"}:
                raise ValueError(f"Компонент {index + 1}: недопустимое выравнивание")
            size = block.get("font_size", 16)
            if isinstance(size, bool) or not isinstance(size, (int, float)) or not 8 <= size <= 96:
                raise ValueError(f"Компонент {index + 1}: размер шрифта должен быть от 8 до 96 px")
            for key in ("href", "src"):
                value = block.get(key)
                if value is None or value == "":
                    continue
                if not isinstance(value, str) or len(value) > 2048 or re.match(r"^\s*(javascript|data|vbscript):", value, re.I):
                    raise ValueError(f"Компонент {index + 1}: небезопасный URL в поле {key}")
                local_path = value.startswith("/") and not value.startswith("//")
                if key == "href" and not (local_path or value.startswith("#") or re.match(r"^(https?://|mailto:)", value, re.I)):
                    raise ValueError("Ссылка должна быть локальным путём, якорем, http(s) или mailto; protocol-relative URL запрещён")
                if key == "src" and not (local_path or re.match(r"^https?://", value, re.I)):
                    raise ValueError("Источник изображения должен быть локальным путём или HTTP(S) URL; protocol-relative URL запрещён")
    def _validate_page_bindings(self, node: WebPageNode) -> None:
        from avic_core.points.runtime import FBDExposedPoint
        from avic_core.domain.models import Point
        for index, block in enumerate(node.layout):
            if not isinstance(block, dict):
                continue
            if block.get("type") == "value":
                point_id = block.get("point_id")
                if not isinstance(point_id, str) or not point_id:
                    raise ValueError(f"Элемент значения {index + 1}: выберите точку Core")
                try:
                    row = self.core.repository.get_record(point_id)
                except (EntityNotFound, ValueError) as exc:
                    raise ValueError(f"Элемент значения {index + 1}: точка не найдена") from exc
                if row.get("entity_type") == "FBDExposedPoint":
                    point, _ = self.core.repository.get(point_id, FBDExposedPoint)
                    point_station = point.station_id
                elif row.get("entity_type") == "Point":
                    point, _ = self.core.repository.get(point_id, Point)
                    device = self.core.repository.get_record(point.device_id)
                    point_station = device.get("payload", {}).get("station_id")
                else:
                    raise ValueError(f"Элемент значения {index + 1}: объект не является точкой Core")
                if point_station != node.station_id:
                    raise ValueError(f"Элемент значения {index + 1}: точка принадлежит другой станции")

    def _station(self, station_id):
        row=self.core.repository.get_record(station_id)
        if row["entity_type"] != "Station": raise ValueError("Узел сайта должен принадлежать станции")
        return row
    def _get(self, node_id):
        node,version=self.core.repository.get(node_id,WebPageNode)
        return node,version
    def _descendants(self, node_id):
        all_nodes=[self.core.repository.get(r["entity_id"],WebPageNode)[0] for r in self.core.repository.list_records(entity_type="WebPageNode")]
        children={}
        for n in all_nodes: children.setdefault(n.parent_id,[]).append(n)
        result=[]; stack=list(children.get(node_id,[]))
        while stack:
            n=stack.pop(); result.append(n); stack.extend(children.get(n.id,[]))
        return result
    def list_tree(self, station_id):
        self._station(station_id)
        nodes=[]
        for row in self.core.repository.list_records(entity_type="WebPageNode",station_id=station_id):
            n,v=self.core.repository.get(row["entity_id"],WebPageNode)
            nodes.append({"id":n.id,"name":n.name,"kind":n.node_kind,"parent_id":n.parent_id,"slug":n.slug,"url":self.url_for(n,nodes),"description":n.description,"graphic_ids":n.graphic_ids,"published":n.published,"revision":v,"navigation_order":n.navigation_order})
        by_parent={}
        for n in nodes: by_parent.setdefault(n["parent_id"],[]).append(n)
        def branch(parent):
            out=[]
            for n in sorted(by_parent.get(parent,[]),key=lambda x:(x["navigation_order"],x["name"].casefold())):
                out.append({**n,"children":branch(n["id"])})
            return out
        return {"station_id":station_id,"nodes":branch(None),"flat":nodes,"publish_enabled":True}
    def url_for(self,node,nodes=None):
        if node.node_kind!="page": return ""
        parts=[node.slug]; parent=node.parent_id
        while parent:
            p,_=self._get(parent)
            if p.node_kind=="folder": parts.append(p.slug or self._slugify(p.name))
            parent=p.parent_id
        return "/"+"/".join(reversed(parts))
    def create(self,station_id,name,kind,parent_id=None,slug=None,description=""):
        self._station(station_id)
        if kind not in {"site","folder","page"}: raise ValueError("Недопустимый тип узла")
        if kind=="site" and parent_id: raise ValueError("Сайт должен быть корневым узлом")
        if kind=="site" and any(self._get(r["entity_id"])[0].node_kind == "site" for r in self.core.repository.list_records(entity_type="WebPageNode", station_id=station_id)):
            raise ValueError("В Web Application станции уже существует корневой сайт")
        if kind in {"folder", "page"} and not parent_id: raise ValueError("Сначала создайте сайт и выберите сайт или папку-родителя")
        if parent_id:
            p,_=self._get(parent_id)
            if p.station_id!=station_id or p.node_kind=="page": raise ValueError("Родитель должен быть сайтом или папкой этой станции")
        slug=(slug or self._slugify(name)) if kind in {"page","folder"} else ""
        if kind in {"page","folder"}:
            if not slug: raise ValueError("Для страницы или папки нужен URL slug")
            if any(n.slug==slug and n.parent_id==parent_id and n.node_kind in {"page", "folder"} for n in [self._get(r["entity_id"])[0] for r in self.core.repository.list_records(entity_type="WebPageNode",station_id=station_id)]): raise ValueError("Узел с таким URL уже существует в этой папке")
        node=WebPageNode(name=name,station_id=station_id,node_kind=kind,parent_id=parent_id,slug=slug,description=description)
        self.core.repository.save(node)
        self.core.audit.append(actor_id="local-engineer",action="web_pages.node_created",resource_type=kind,resource_id=node.id,details={"station_id":station_id,"parent_id":parent_id})
        return self.get(node.id)
    def get(self,node_id):
        n,v=self._get(node_id)
        return {"id":n.id,"name":n.name,"kind":n.node_kind,"station_id":n.station_id,"parent_id":n.parent_id,"slug":n.slug,"url":self.url_for(n),"description":n.description,"html":n.html,"css":n.css,"javascript":n.javascript,"graphic_ids":n.graphic_ids,"layout":n.layout,"published":n.published,"published_at":n.published_at.isoformat() if n.published_at else None,"published_revision":n.published_revision,"published_versions":[{"revision":item.get("revision"),"published_at":item.get("published_at"),"rollback_of":item.get("rollback_of")} for item in n.published_versions],"revision":v}
    def update(self,node_id,expected_revision,**changes):
        n,v=self._get(node_id)
        if v!=expected_revision: raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {v}")
        allowed={"name","slug","description","html","css","javascript","graphic_ids","layout","navigation_order"}
        for k,val in changes.items():
            if k in allowed and val is not None: setattr(n,k,val)
        n.updated_at=datetime.now(timezone.utc)
        # Validate model constraints after mutation and ensure page slug uniqueness.
        n.__post_init__()
        if n.node_kind in {"page", "folder"}:
            for row in self.core.repository.list_records(entity_type="WebPageNode",station_id=n.station_id):
                if row["entity_id"]!=n.id:
                    other,_=self._get(row["entity_id"])
                    if other.node_kind in {"page", "folder"} and other.parent_id==n.parent_id and other.slug==n.slug: raise ValueError("Узел с таким URL уже существует в этой папке")
        if n.node_kind=="page":
            self._validate_page_bindings(n)
            for block in n.layout:
                src = block.get("src", "") if isinstance(block, dict) else ""
                match = re.fullmatch(r"/api/repository-assets/([0-9a-fA-F-]{36})", src) if isinstance(src, str) else None
                if match:
                    asset, _ = self.core.repository.get(match.group(1), RepositoryAsset)
                    if asset.station_id != n.station_id:
                        raise ValueError("Изображение принадлежит другой станции")
            for graphic_id in n.graphic_ids:
                from avic_core.graphics.models import GraphicDocument
                graphic,_=self.core.repository.get(graphic_id,GraphicDocument)
                if graphic.station_id!=n.station_id: raise ValueError("Мнемосхема принадлежит другой станции")
            self._validate_layout(n)
        self.core.repository.save(n,expected_version=v)
        self.core.audit.append(actor_id="local-engineer",action="web_pages.node_updated",resource_type=n.node_kind,resource_id=n.id,details={"fields":sorted(k for k in changes if k in allowed)})
        return self.get(n.id)
    def move(self,node_id,new_parent_id):
        n,v=self._get(node_id)
        if new_parent_id:
            p,_=self._get(new_parent_id)
            if p.station_id!=n.station_id or p.node_kind=="page": raise ValueError("Нельзя переместить узел в выбранного родителя")
            if p.id==n.id or any(x.id==p.id for x in self._descendants(n.id)): raise ValueError("Перемещение создаёт циклическую иерархию")
        if n.node_kind=="site" and new_parent_id: raise ValueError("Сайт должен оставаться корневым узлом")
        if n.node_kind in {"folder", "page"} and not new_parent_id: raise ValueError("Папка или страница должна находиться внутри сайта или другой папки")
        if n.node_kind in {"page", "folder"}:
            for row in self.core.repository.list_records(entity_type="WebPageNode",station_id=n.station_id):
                if row["entity_id"]!=n.id:
                    other,_=self._get(row["entity_id"])
                    if other.node_kind in {"page", "folder"} and other.parent_id==new_parent_id and other.slug==n.slug:
                        raise ValueError("В целевой папке уже есть узел с таким URL")
        n.parent_id=new_parent_id; n.updated_at=datetime.now(timezone.utc); n.__post_init__()
        self.core.repository.save(n,expected_version=v)
        self.core.audit.append(actor_id="local-engineer",action="web_pages.node_moved",resource_type=n.node_kind,resource_id=n.id,details={"parent_id":new_parent_id})
        return self.get(n.id)
    def reorder(self,node_id,direction):
        if direction not in {"up", "down"}:
            raise ValueError("Направление сортировки должно быть up или down")
        node,version=self._get(node_id)
        siblings=[]
        for row in self.core.repository.list_records(entity_type="WebPageNode",station_id=node.station_id):
            sibling,_=self._get(row["entity_id"])
            if sibling.parent_id==node.parent_id:
                siblings.append(sibling)
        siblings.sort(key=lambda item:(item.navigation_order,item.name.casefold()))
        index=next(i for i,item in enumerate(siblings) if item.id==node_id)
        target=index+(-1 if direction=="up" else 1)
        if target<0 or target>=len(siblings):
            return self.get(node_id)
        siblings[index],siblings[target]=siblings[target],siblings[index]
        with self.core.repository.transaction() as conn:
            for order,item in enumerate(siblings):
                if item.navigation_order==order:
                    continue
                current,expected=self._get(item.id)
                current.navigation_order=order
                current.updated_at=datetime.now(timezone.utc)
                self.core.repository.save(current,expected_version=expected,connection=conn)
        self.core.audit.append(actor_id="local-engineer",action="web_pages.node_reordered",resource_type=node.node_kind,resource_id=node.id,details={"direction":direction,"navigation_order":target})
        return self.get(node_id)
    def delete(self,node_id,expected_revision):
        n,v=self._get(node_id)
        if v!=expected_revision: raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {v}")
        descendants=self._descendants(node_id)
        with self.core.repository.transaction() as conn:
            # Delete in post-order so children are removed before their parents.
            by_parent={}
            for child in descendants: by_parent.setdefault(child.parent_id,[]).append(child)
            ordered=[]
            def visit(parent):
                for child in by_parent.get(parent,[]):
                    visit(child.id); ordered.append(child)
            visit(node_id)
            for child in ordered:
                row=self.core.repository.get_record(child.id)
                self.core.repository.delete(child.id,expected_version=row["version"],connection=conn)
            self.core.repository.delete(node_id,expected_version=v,connection=conn)
        self.core.audit.append(actor_id="local-engineer",action="web_pages.node_deleted",resource_type=n.node_kind,resource_id=n.id,details={"descendants":len(descendants)})
        return {"deleted":node_id,"deleted_descendants":len(descendants)}
    def create_asset(self, station_id, filename, media_type, content):
        self._station(station_id)
        if not isinstance(filename, str) or not filename.strip() or len(filename) > 180:
            raise ValueError("Некорректное имя файла")
        signatures = {
            "image/png": content.startswith(b"\x89PNG\r\n\x1a\n"),
            "image/jpeg": content.startswith(b"\xff\xd8\xff"),
            "image/gif": content.startswith((b"GIF87a", b"GIF89a")),
            "image/webp": len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP",
        }
        if len(content) > 3 * 1024 * 1024:
            raise ValueError("Размер изображения превышает 3 МБ")
        if media_type not in signatures or not signatures[media_type]:
            raise ValueError("Формат файла не совпадает с содержимым или не поддерживается")
        asset = RepositoryAsset(name=filename.strip(), station_id=station_id, media_type=media_type,
                                content_base64=base64.b64encode(content).decode("ascii"),
                                byte_size=len(content), content_sha256=sha256(content).hexdigest())
        self.core.repository.save(asset)
        self.core.audit.append(actor_id="local-engineer", action="repository.asset_uploaded", resource_type="RepositoryAsset", resource_id=asset.id, details={"station_id": station_id, "size": len(content), "sha256": asset.content_sha256})
        return {"id": asset.id, "name": asset.name, "media_type": asset.media_type,
                "byte_size": asset.byte_size, "url": f"/api/repository-assets/{asset.id}", "sha256": asset.content_sha256}

    def list_assets(self, station_id):
        self._station(station_id)
        result = []
        for row in self.core.repository.list_records(entity_type="RepositoryAsset", station_id=station_id):
            asset, version = self.core.repository.get(row["entity_id"], RepositoryAsset)
            result.append({"id": asset.id, "name": asset.name, "media_type": asset.media_type,
                           "byte_size": asset.byte_size, "url": f"/api/repository-assets/{asset.id}", "revision": version})
        return result

    def read_asset(self, asset_id):
        asset, _ = self.core.repository.get(asset_id, RepositoryAsset)
        return asset

    def publish(self, node_id, expected_revision):
        """Publish an immutable, validated layout snapshot for operator viewing."""
        n, version = self._get(node_id)
        if n.node_kind != "page":
            raise ValueError("Публиковать можно только страницу")
        if version != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {version}")
        self._validate_layout(n)
        self._validate_page_bindings(n)
        if not n.layout:
            raise ValueError("Страница пустая: добавьте хотя бы один визуальный элемент перед публикацией")
        for graphic_id in n.graphic_ids:
            from avic_core.graphics.models import GraphicDocument
            graphic, _ = self.core.repository.get(graphic_id, GraphicDocument)
            if graphic.station_id != n.station_id:
                raise ValueError("Мнемосхема принадлежит другой станции")
        n.published = True
        n.published_at = datetime.now(timezone.utc)
        # Freeze the referenced Graphics documents into the publication snapshot.
        # Point samples remain live through Point Runtime, but graphic geometry,
        # symbol selection and binding configuration cannot drift after publish.
        from copy import deepcopy
        from avic_core.graphics.service import GraphicsService
        published_layout = deepcopy(n.layout)
        graphics_service = GraphicsService(self.core)
        for block in published_layout:
            if isinstance(block, dict) and block.get("type") == "graphic":
                graphic_id = str(block.get("graphic_id") or "")
                graphic, _ = self.core.repository.get(graphic_id, __import__("avic_core.graphics.models", fromlist=["GraphicDocument"]).GraphicDocument)
                if graphic.station_id != n.station_id:
                    raise ValueError("Мнемосхема принадлежит другой станции")
                block["graphic_snapshot"] = graphics_service.get(graphic_id)
        n.published_layout = published_layout
        n.published_revision = version + 1
        n.published_versions.append({"revision": n.published_revision, "published_at": n.published_at.isoformat(),
                                     "layout": deepcopy(published_layout), "rollback_of": None})
        n.published_versions = n.published_versions[-50:]
        self.core.repository.save(n, expected_version=version)
        self.core.audit.append(actor_id="local-engineer", action="web_pages.published", resource_type="page", resource_id=n.id, details={"station_id": n.station_id, "url": self.url_for(n), "revision": n.published_revision})
        return self.get(n.id)

    def unpublish(self, node_id, expected_revision):
        n, version = self._get(node_id)
        if version != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {version}")
        n.published = False
        n.updated_at = datetime.now(timezone.utc)
        self.core.repository.save(n, expected_version=version)
        self.core.audit.append(actor_id="local-engineer", action="web_pages.unpublished", resource_type=n.node_kind, resource_id=n.id, details={"station_id": n.station_id})
        return self.get(n.id)

    def rollback_publication(self, node_id, expected_revision, target_published_revision):
        n, version = self._get(node_id)
        if n.node_kind != "page":
            raise ValueError("Откат публикации доступен только для страницы")
        if version != expected_revision:
            raise ValueError(f"CONCURRENCY_CONFLICT: current revision is {version}")
        target = next((item for item in n.published_versions if item.get("revision") == target_published_revision), None)
        if target is None:
            raise ValueError("Версия публикации не найдена в истории")
        now = datetime.now(timezone.utc)
        n.published = True
        n.published_at = now
        from copy import deepcopy
        n.published_layout = deepcopy(target.get("layout", []))
        if not isinstance(n.published_layout, list):
            raise ValueError("История публикации повреждена: снимок страницы недоступен")
        for block in n.published_layout:
            if isinstance(block, dict) and block.get("type") == "graphic" and not isinstance(block.get("graphic_snapshot"), dict):
                raise ValueError("Эта историческая версия не содержит замороженного снимка мнемосхемы; откат запрещён")
        n.published_revision = version + 1
        n.published_versions.append({"revision": n.published_revision, "published_at": now.isoformat(),
                                     "layout": deepcopy(n.published_layout), "rollback_of": target_published_revision})
        n.published_versions = n.published_versions[-50:]
        n.updated_at = now
        self.core.repository.save(n, expected_version=version)
        self.core.audit.append(actor_id="local-engineer", action="web_pages.publication_rolled_back", resource_type="page", resource_id=n.id,
                               details={"station_id": n.station_id, "rollback_of": target_published_revision, "published_revision": n.published_revision})
        return self.get(n.id)

    def published_page(self, station_id, path):
        self._station(station_id)
        normalized = "/" + path.strip("/")
        for row in self.core.repository.list_records(entity_type="WebPageNode", station_id=station_id):
            node, _ = self._get(row["entity_id"])
            if node.node_kind == "page" and node.published and self.url_for(node) == normalized:
                return {"id": node.id, "station_id": node.station_id, "name": node.name,
                        "layout": list(node.published_layout), "published_revision": node.published_revision}
        raise EntityNotFound("Published page not found")

    def assign_graphic(self,node_id,graphic_id,expected_revision):
        n,v=self._get(node_id)
        if n.node_kind!="page": raise ValueError("Мнемосхемы можно назначать только страницам")
        doc,gv=self.core.repository.get(graphic_id,__import__('avic_core.graphics.models',fromlist=['GraphicDocument']).GraphicDocument)
        if doc.station_id!=n.station_id: raise ValueError("Мнемосхема принадлежит другой станции")
        ids=list(n.graphic_ids)
        if graphic_id not in ids: ids.append(graphic_id)
        return self.update(node_id,expected_revision,graphic_ids=ids)
    def unassign_graphic(self,node_id,graphic_id,expected_revision):
        n,v=self._get(node_id)
        return self.update(node_id,expected_revision,
                           graphic_ids=[x for x in n.graphic_ids if x!=graphic_id],
                           layout=[x for x in n.layout if x.get("graphic_id") != graphic_id])
