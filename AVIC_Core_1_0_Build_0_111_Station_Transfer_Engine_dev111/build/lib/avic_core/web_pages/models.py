from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4, UUID


def _now(): return datetime.now(timezone.utc)
def _id(): return str(uuid4())

@dataclass(slots=True)
class WebPageNode:
    name: str
    station_id: str
    node_kind: str = "page"  # site, folder, page
    parent_id: str | None = None
    slug: str = ""
    description: str = ""
    html: str = ""
    css: str = ""
    javascript: str = ""
    graphic_ids: list[str] = field(default_factory=list)
    layout: list[dict] = field(default_factory=list)
    navigation_order: int = 0
    published: bool = False
    published_at: datetime | None = None
    published_revision: int | None = None
    published_layout: list[dict] = field(default_factory=list)
    published_versions: list[dict] = field(default_factory=list)
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        UUID(self.id); UUID(self.station_id)
        if self.parent_id: UUID(self.parent_id)
        if self.node_kind not in {"site", "folder", "page"}: raise ValueError("Недопустимый тип узла")
        if not self.name.strip(): raise ValueError("Название не может быть пустым")
        if self.node_kind in {"page", "folder"}:
            import re
            if not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,78}[a-z0-9])?", self.slug):
                raise ValueError("URL slug: только латинские строчные буквы, цифры и дефис")
        if self.node_kind == "site" and self.parent_id:
            raise ValueError("Сайт должен быть корневым узлом")
        if len(self.html) > 1_000_000 or len(self.css) > 500_000 or len(self.javascript) > 500_000:
            raise ValueError("Содержимое страницы превышает допустимый размер")
