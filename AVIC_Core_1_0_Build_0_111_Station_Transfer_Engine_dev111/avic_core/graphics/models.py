from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4, UUID
from avic_core.graphics.svg_library import SVG_SYMBOLS
from avic_core.graphics.binding_engine import validate_binding_config


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _id() -> str:
    return str(uuid4())

@dataclass(slots=True)
class GraphicDocument:
    name: str
    station_id: str
    id: str = field(default_factory=_id)
    description: str = ""
    width: int = 1600
    height: int = 900
    grid_size: int = 10
    revision: int = 0
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        UUID(self.id); UUID(self.station_id)
        if not self.name.strip(): raise ValueError("Graphic document name cannot be empty")
        if not (100 <= self.width <= 10000 and 100 <= self.height <= 10000): raise ValueError("Canvas dimensions must be between 100 and 10000")
        if not (1 <= self.grid_size <= 200): raise ValueError("Grid size must be between 1 and 200")

@dataclass(slots=True)
class GraphicElement:
    name: str
    document_id: str
    symbol_key: str
    x: float
    y: float
    width: float = 100
    height: float = 80
    rotation: float = 0
    layer: int = 0
    id: str = field(default_factory=_id)
    symbol_version: str = "1.0.0"
    properties: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    def __post_init__(self):
        UUID(self.id); UUID(self.document_id)
        if self.symbol_key not in SVG_SYMBOLS:
            import re
            if not re.fullmatch(r"custom_[0-9a-f]{32}", self.symbol_key):
                raise ValueError("Unsupported symbol key")
        if not (1 <= self.width <= 2000 and 1 <= self.height <= 2000): raise ValueError("Element dimensions out of range")
        if not (-360 <= self.rotation <= 360): raise ValueError("Element rotation out of range")

@dataclass(slots=True)
class PointBinding:
    element_id: str
    point_id: str
    role: str = "value"
    binding_type: str = "value"
    target_property: str = "value"
    settings: dict = field(default_factory=dict)
    id: str = field(default_factory=_id)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)
    @property
    def name(self) -> str:
        return f"{self.role}:{self.point_id}"
    def __post_init__(self):
        UUID(self.id); UUID(self.element_id); UUID(self.point_id)
        if self.role not in {"value", "feedback", "alarm", "quality"}:
            raise ValueError("Binding role is not enabled; command execution is intentionally unavailable")
        self.settings = validate_binding_config(self.binding_type, self.target_property, self.settings)
