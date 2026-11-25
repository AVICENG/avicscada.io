from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class SignalQuality(str, Enum):
    GOOD = "GOOD"
    UNCERTAIN = "UNCERTAIN"
    STALE = "STALE"
    BAD = "BAD"
    COMM_LOST = "COMM_LOST"
    CONFIG_ERROR = "CONFIG_ERROR"
    DISABLED = "DISABLED"


class ExecutionClass(str, Enum):
    FAST = "FAST"
    NORMAL = "NORMAL"
    SLOW = "SLOW"
    EVENT_DRIVEN = "EVENT_DRIVEN"
    BACKGROUND = "BACKGROUND"


class FBDCategory(str, Enum):
    LOGIC = "Logic"
    COMPARE = "Compare"
    MATH = "Math"
    ANALOG = "Analog"
    DIGITAL = "Digital"
    TIMER = "Timer"
    COUNTER = "Counter"
    CONTROL = "Control"
    SIGNAL_PROCESSING = "Signal Processing"
    HVAC = "HVAC"
    HYDRAULICS = "Hydraulics"
    SCHEDULING = "Scheduling"
    ALARM = "Alarm"
    DATA = "Data"
    COMMUNICATION = "Communication"
    SYSTEM = "System"


class FBDType(str, Enum):
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STRING = "string"
    DATETIME = "datetime"
    ANY = "any"


@dataclass(frozen=True, slots=True)
class SignalEnvelope:
    """Common value envelope shared by drivers, FBD, graphics, alarms and trends."""

    value: Any
    data_type: FBDType
    quality: SignalQuality
    timestamp: datetime
    source_ref: str
    sequence: int = 0
    unit: str = ""

    def __post_init__(self) -> None:
        if not self.source_ref.strip():
            raise ValueError("source_ref cannot be empty")
        if self.sequence < 0:
            raise ValueError("sequence cannot be negative")
        if self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        if self.data_type is FBDType.BOOL and not isinstance(self.value, bool):
            raise TypeError("BOOL signal requires bool value")
        if self.data_type is FBDType.INT and (not isinstance(self.value, int) or isinstance(self.value, bool)):
            raise TypeError("INT signal requires int value")
        if self.data_type is FBDType.FLOAT and (not isinstance(self.value, (int, float)) or isinstance(self.value, bool)):
            raise TypeError("FLOAT signal requires numeric value")
        if self.data_type is FBDType.STRING and not isinstance(self.value, str):
            raise TypeError("STRING signal requires str value")

    @classmethod
    def now(
        cls, value: Any, data_type: FBDType, quality: SignalQuality,
        source_ref: str, sequence: int = 0, unit: str = "",
    ) -> "SignalEnvelope":
        return cls(value, data_type, quality, datetime.now(timezone.utc), source_ref, sequence, unit)


@dataclass(frozen=True, slots=True)
class EventEnvelope:
    """Version-neutral event contract for future event bus consumers."""

    event_type: str
    source_ref: str
    occurred_at: datetime
    payload: Mapping[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid4()))
    correlation_id: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        if not self.event_type.strip() or not self.source_ref.strip() or not self.event_id.strip():
            raise ValueError("event_type, source_ref and event_id are required")
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValueError("occurred_at must be timezone-aware")
        if self.sequence < 0:
            raise ValueError("sequence cannot be negative")


@dataclass(frozen=True, slots=True)
class CommandRequest:
    """A command proposal, not an execution primitive or protocol write."""

    target_ref: str
    command: str
    requested_by: str
    requested_at: datetime
    parameters: Mapping[str, Any] = field(default_factory=dict)
    priority: int = 50
    idempotency_key: str = ""
    reason: str = ""
    requires_confirmation: bool = True

    def __post_init__(self) -> None:
        if not self.target_ref.strip() or not self.command.strip() or not self.requested_by.strip():
            raise ValueError("target_ref, command and requested_by are required")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("requested_at must be timezone-aware")
        if not 0 <= self.priority <= 100:
            raise ValueError("priority must be between 0 and 100")


@dataclass(frozen=True, slots=True)
class FBDPortDefinition:
    port_id: str
    name: str
    direction: str
    data_type: FBDType
    required: bool = True

    def __post_init__(self) -> None:
        if not self.port_id.strip() or not self.name.strip():
            raise ValueError("FBD port id and name are required")
        if self.direction not in {"input", "output", "inout"}:
            raise ValueError("direction must be input, output or inout")


@dataclass(frozen=True, slots=True)
class PluginManifest:
    plugin_id: str
    version: str
    api_version: str
    kind: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    permissions: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        for name in ("plugin_id", "version", "api_version", "kind"):
            if not getattr(self, name).strip():
                raise ValueError(f"{name} cannot be empty")


@dataclass(frozen=True, slots=True)
class GraphicsBinding:
    """Reference to an existing runtime object; graphics must not own point identity."""

    runtime_ref: str
    property_path: str = "value"

    def __post_init__(self) -> None:
        if not self.runtime_ref.strip() or not self.property_path.strip():
            raise ValueError("runtime_ref and property_path are required")


@dataclass(frozen=True, slots=True)
class SymbolManifest:
    symbol_id: str
    version: str
    view_box: tuple[float, float, float, float]
    category: str
    ports: tuple[str, ...] = ()
    anchors: tuple[str, ...] = ()
    supported_states: tuple[str, ...] = ()
    bindings: tuple[GraphicsBinding, ...] = ()
    scale: float = 1.0
    properties_schema: tuple[str, ...] = ()
    animations: tuple[str, ...] = ()
    locales: tuple[str, ...] = ("ru", "en")
    license_feature: str | None = None

    def __post_init__(self) -> None:
        if not self.symbol_id.strip() or not self.version.strip() or not self.category.strip():
            raise ValueError("symbol_id, version and category are required")
        if len(self.view_box) != 4 or self.view_box[2] <= 0 or self.view_box[3] <= 0:
            raise ValueError("view_box must be (min_x, min_y, positive_width, positive_height)")
        if self.scale <= 0:
            raise ValueError("scale must be positive")
        if not self.locales or any(locale not in {"ru", "en"} for locale in self.locales):
            raise ValueError("locales must contain supported values: ru and/or en")
