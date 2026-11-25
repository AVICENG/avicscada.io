"""Typed, read-only graphics binding contracts and deterministic value presentation.

This module deliberately does not perform field writes. Setpoint/action bindings are
recognized as intents but fail closed until a separately authorized Command Manager
adapter is connected.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re
from typing import Any


class BindingType(str, Enum):
    VALUE = "value"
    BOUND_LABEL = "bound_label"
    SPECTRUM = "spectrum"
    STATUS = "status"
    SETPOINT = "setpoint"
    ACTION = "action"
    POPUP = "popup"
    HYPERLINK = "hyperlink"
    HISTORIAN = "historian"


class TargetProperty(str, Enum):
    TEXT = "text"
    VALUE = "value"
    COLOR = "color"
    VISIBLE = "visible"
    ROTATION = "rotation"
    ANIMATION = "animation"
    IMAGE = "image"
    STATUS = "status"
    TOOLTIP = "tooltip"


class DegradeBehavior(str, Enum):
    SHOW_QUALITY = "show_quality"
    HIDE = "hide"
    SAFE_DEFAULT = "safe_default"


_HEX_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")
_ALLOWED_QUALITY = {"GOOD", "BAD", "UNCERTAIN", "STALE", "COMM_LOST", "NOT_CONNECTED", "UNKNOWN"}


@dataclass(frozen=True, slots=True)
class BindingResult:
    binding_type: str
    target_property: str
    value: Any
    display_text: str | None
    quality: str
    degraded: bool
    visible: bool
    animation_allowed: bool
    interaction_allowed: bool
    diagnostic: str | None = None


def validate_binding_config(binding_type: str = "value", target_property: str = "value",
                            settings: dict | None = None) -> dict:
    """Validate persisted binding configuration and return a normalized copy."""
    try:
        kind = BindingType(str(binding_type))
        target = TargetProperty(str(target_property))
    except ValueError as exc:
        raise ValueError("Неизвестный тип привязки или целевое свойство") from exc
    compatible_targets = {
        BindingType.BOUND_LABEL: {TargetProperty.TEXT},
        BindingType.SPECTRUM: {TargetProperty.COLOR},
        BindingType.STATUS: {TargetProperty.STATUS, TargetProperty.ANIMATION, TargetProperty.VISIBLE, TargetProperty.COLOR},
        BindingType.POPUP: {TargetProperty.TOOLTIP},
        BindingType.HYPERLINK: {TargetProperty.TEXT, TargetProperty.VALUE, TargetProperty.TOOLTIP},
        BindingType.HISTORIAN: {TargetProperty.VALUE},
    }
    if kind in compatible_targets and target not in compatible_targets[kind]:
        raise ValueError(f"Тип привязки {kind.value} несовместим со свойством {target.value}")
    # SETPOINT/ACTION are accepted as authoring contracts only; execution stays fail-closed.
    cfg = dict(settings or {})
    allowed = {"decimals", "unit", "prefix", "suffix", "scale", "offset", "converter",
               "true_text", "false_text", "enum_map", "thresholds", "degrade_behavior",
               "safe_default", "min_value", "max_value", "hyperlink", "popup_id", "historian_range"}
    unknown = set(cfg) - allowed
    if unknown:
        raise ValueError(f"Неизвестные параметры привязки: {', '.join(sorted(unknown))}")
    decimals = cfg.get("decimals", 1)
    if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 8:
        raise ValueError("decimals должен быть целым числом от 0 до 8")
    for key in ("scale", "offset", "min_value", "max_value"):
        if key in cfg:
            val = cfg[key]
            if isinstance(val, bool) or not isinstance(val, (int, float)) or not math.isfinite(float(val)):
                raise ValueError(f"{key} должен быть конечным числом")
    if "scale" in cfg and float(cfg["scale"]) == 0:
        raise ValueError("scale не может быть равен нулю")
    for key in ("unit", "prefix", "suffix", "true_text", "false_text"):
        if key in cfg and (not isinstance(cfg[key], str) or len(cfg[key]) > 64):
            raise ValueError(f"{key} должен быть строкой не длиннее 64 символов")
    converter = cfg.get("converter", "auto")
    if converter not in {"auto", "numeric", "boolean", "enum", "string"}:
        raise ValueError("Недопустимый converter")
    if "enum_map" in cfg:
        em = cfg["enum_map"]
        if not isinstance(em, dict) or len(em) > 128 or any(not isinstance(k, str) or len(k) > 64 or not isinstance(v, str) or len(v) > 128 for k, v in em.items()):
            raise ValueError("enum_map должен быть словарём строковых состояний (до 128 записей)")
    thresholds = cfg.get("thresholds", [])
    if not isinstance(thresholds, list) or len(thresholds) > 64:
        raise ValueError("thresholds должен содержать не более 64 диапазонов")
    checked = []
    for item in thresholds:
        if not isinstance(item, dict) or set(item) != {"min", "max", "color"}:
            raise ValueError("Диапазон должен содержать min, max и color")
        lo, hi, color = item["min"], item["max"], item["color"]
        if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(float(v)) for v in (lo, hi)) or float(lo) >= float(hi):
            raise ValueError("Границы диапазона должны быть конечными и min < max")
        if not isinstance(color, str) or not _HEX_COLOR.fullmatch(color):
            raise ValueError("Цвет диапазона должен быть в формате #RRGGBB")
        checked.append({"min": float(lo), "max": float(hi), "color": color.upper()})
    checked.sort(key=lambda x: x["min"])
    for left, right in zip(checked, checked[1:]):
        if right["min"] < left["max"]:
            raise ValueError("Диапазоны thresholds не должны пересекаться")
    cfg["thresholds"] = checked
    degrade = cfg.get("degrade_behavior", DegradeBehavior.SHOW_QUALITY.value)
    if degrade not in {x.value for x in DegradeBehavior}:
        raise ValueError("Недопустимое degrade_behavior")
    cfg["degrade_behavior"] = degrade
    if "safe_default" in cfg and (isinstance(cfg["safe_default"], (dict, list, tuple, set)) or
            (isinstance(cfg["safe_default"], str) and len(cfg["safe_default"]) > 128)):
        raise ValueError("safe_default должен быть простым скалярным значением")
    if "hyperlink" in cfg:
        from urllib.parse import unquote, urlsplit
        link = cfg["hyperlink"]
        parsed = urlsplit(link) if isinstance(link, str) else None
        decoded_path = unquote(parsed.path) if parsed else ""
        if (not isinstance(link, str) or not link.startswith("/") or link.startswith("//") or
                not parsed or parsed.scheme or parsed.netloc or "\\" in link or
                any(part == ".." for part in decoded_path.split("/")) or
                any(ord(ch) < 32 for ch in link)):
            raise ValueError("Гиперссылка должна быть внутренним абсолютным путём AVIC")
    if "historian_range" in cfg and cfg["historian_range"] not in {"1h", "8h", "24h", "7d", "30d", "custom"}:
        raise ValueError("Недопустимый диапазон Historian")
    return cfg


def evaluate_binding(*, binding_type: str = "value", target_property: str = "value",
                     settings: dict | None = None, value: Any = None, quality: str = "UNKNOWN") -> BindingResult:
    """Map one Core point sample to one graphics property without executing writes."""
    cfg = validate_binding_config(binding_type, target_property, settings)
    kind, target = BindingType(binding_type), TargetProperty(target_property)
    q = str(quality).upper()
    if q not in _ALLOWED_QUALITY:
        q = "UNKNOWN"
    if q != "GOOD":
        degrade = cfg["degrade_behavior"]
        if degrade == DegradeBehavior.HIDE.value:
            return BindingResult(kind.value, target.value, None, None, q, True, False, False, False, "QUALITY_NOT_GOOD")
        safe = cfg.get("safe_default") if degrade == DegradeBehavior.SAFE_DEFAULT.value else None
        return BindingResult(kind.value, target.value, safe, f"{q}" if degrade == DegradeBehavior.SHOW_QUALITY.value else None,
                             q, True, True, False, False, "QUALITY_NOT_GOOD")

    if kind in {BindingType.SETPOINT, BindingType.ACTION}:
        return BindingResult(kind.value, target.value, None, None, q, False, True, False, False,
                             "COMMAND_MANAGER_NOT_CONNECTED")
    if kind == BindingType.HYPERLINK:
        return BindingResult(kind.value, target.value, cfg.get("hyperlink"), None, q, False, True, False, False)
    if kind == BindingType.POPUP:
        return BindingResult(kind.value, target.value, cfg.get("popup_id"), None, q, False, True, False, False)
    if kind == BindingType.HISTORIAN:
        return BindingResult(kind.value, target.value, cfg.get("historian_range", "24h"), None, q, False, True, False, False)

    converter = cfg.get("converter", "auto")
    display_value = value
    if converter == "numeric" or (converter == "auto" and isinstance(value, (int, float)) and not isinstance(value, bool)):
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
            return BindingResult(kind.value, target.value, None, None, q, True, True, False, False, "TYPE_MISMATCH")
        display_value = float(value) * float(cfg.get("scale", 1.0)) + float(cfg.get("offset", 0.0))
        if "min_value" in cfg: display_value = max(float(cfg["min_value"]), display_value)
        if "max_value" in cfg: display_value = min(float(cfg["max_value"]), display_value)
        text = f"{cfg.get('prefix', '')}{display_value:.{cfg.get('decimals', 1)}f}{cfg.get('unit', '')}{cfg.get('suffix', '')}"
    elif converter == "boolean" or isinstance(value, bool):
        if not isinstance(value, bool):
            return BindingResult(kind.value, target.value, None, None, q, True, True, False, False, "TYPE_MISMATCH")
        display_value = value
        text = cfg.get("true_text", "ВКЛ") if value else cfg.get("false_text", "ВЫКЛ")
    elif converter == "enum":
        text = cfg.get("enum_map", {}).get(str(value), str(value))
        display_value = text
    elif converter == "string" or isinstance(value, str):
        if not isinstance(value, str):
            return BindingResult(kind.value, target.value, None, None, q, True, True, False, False, "TYPE_MISMATCH")
        text = value
    else:
        text = str(value)

    if kind == BindingType.SPECTRUM:
        if not isinstance(display_value, (int, float)) or isinstance(display_value, bool):
            return BindingResult(kind.value, target.value, None, None, q, True, True, False, False, "SPECTRUM_REQUIRES_NUMERIC")
        color = next((x["color"] for x in cfg["thresholds"] if x["min"] <= float(display_value) < x["max"]), None)
        return BindingResult(kind.value, target.value, color, text, q, color is None, True, False, False,
                             None if color else "NO_THRESHOLD_MATCH")
    if kind == BindingType.STATUS:
        return BindingResult(kind.value, target.value, display_value, text, q, False, True,
                             bool(display_value) if isinstance(display_value, bool) else False, False)
    return BindingResult(kind.value, target.value, display_value, text, q, False, True,
                         bool(display_value) if isinstance(display_value, bool) else False, False)
