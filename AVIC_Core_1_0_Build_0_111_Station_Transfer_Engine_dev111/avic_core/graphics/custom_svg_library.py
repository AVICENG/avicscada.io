"""Station-scoped imported SVG symbols with a restrictive SVG sanitizer.

Only inert SVG drawing primitives are accepted. Scripts, embedded documents,
external links, CSS imports, animation and event-handler attributes are rejected.
"""
from __future__ import annotations

import hashlib
import re
import sqlite3
import threading
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

SVG_NS = "http://www.w3.org/2000/svg"
XLINK_NS = "http://www.w3.org/1999/xlink"
ET.register_namespace("", SVG_NS)
ET.register_namespace("xlink", XLINK_NS)

MAX_SVG_BYTES = 1_000_000
MAX_SVG_NODES = 10_000
MAX_SVG_DEPTH = 50
_ALLOWED_TAGS = {
    "svg", "g", "path", "rect", "circle", "ellipse", "line", "polyline", "polygon",
    "defs", "linearGradient", "radialGradient", "stop", "clipPath", "mask", "pattern",
    "marker", "symbol", "use", "title", "desc", "text", "tspan",
}
_ALLOWED_ATTRS = {
    "id", "class", "xmlns", "viewBox", "width", "height", "version", "preserveAspectRatio",
    "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry", "d", "points",
    "fill", "fill-rule", "fill-opacity", "stroke", "stroke-width", "stroke-linecap",
    "stroke-linejoin", "stroke-dasharray", "stroke-dashoffset", "stroke-opacity", "opacity",
    "transform", "style", "offset", "stop-color", "stop-opacity", "gradientUnits",
    "gradientTransform", "spreadMethod", "fx", "fy", "clipPathUnits", "clip-path", "mask",
    "patternUnits", "patternContentUnits", "patternTransform", "markerWidth", "markerHeight",
    "markerUnits", "refX", "refY", "orient", "marker-start", "marker-mid", "marker-end",
    "href", "font-family", "font-size", "font-weight", "text-anchor", "dominant-baseline",
    "alignment-baseline", "vector-effect", "shape-rendering", "display", "visibility",
}
_STYLE_PROPERTIES = {
    "fill", "fill-rule", "fill-opacity", "stroke", "stroke-width", "stroke-linecap", "stroke-linejoin",
    "stroke-dasharray", "stroke-dashoffset", "stroke-opacity", "opacity", "font-family", "font-size",
    "font-weight", "text-anchor", "dominant-baseline", "display", "visibility", "stroke-miterlimit", "stop-color", "stop-opacity",
}
_ID_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.:-]{0,127}$")
_URL_RE = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I)


class SvgImportError(ValueError):
    """Raised when an uploaded SVG is invalid or unsafe."""


def _local_name(value: str) -> str:
    return value.rsplit("}", 1)[-1]


def sanitize_svg(payload: str | bytes) -> tuple[bytes, dict[str, str]]:
    if isinstance(payload, str):
        raw = payload.encode("utf-8")
    elif isinstance(payload, bytes):
        raw = payload
    else:
        raise SvgImportError("SVG-файл должен быть текстом UTF-8")
    if not raw or len(raw) > MAX_SVG_BYTES:
        raise SvgImportError("Размер SVG должен быть от 1 байта до 1 МБ")
    try:
        source = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SvgImportError("SVG должен быть сохранён в UTF-8") from exc
    lowered = source.lower()
    if "<!doctype" in lowered or "<!entity" in lowered:
        raise SvgImportError("DOCTYPE и ENTITY запрещены в импортируемом SVG")
    if re.search(r"<\s*(script|foreignObject|iframe|object|embed|audio|video|image|animate|animateTransform|set)\b", source, re.I):
        raise SvgImportError("SVG содержит запрещённый активный или внешний элемент")
    try:
        root = ET.fromstring(source)
    except ET.ParseError as exc:
        raise SvgImportError(f"Некорректный XML/SVG: {exc}") from exc
    if _local_name(root.tag) != "svg" or (root.tag.startswith("{") and not root.tag.startswith("{" + SVG_NS + "}")):
        raise SvgImportError("Корневой элемент должен быть SVG")

    node_count = 0
    ids: set[str] = set()
    references: list[str] = []

    def clean(element: ET.Element, depth: int = 0) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > MAX_SVG_NODES or depth > MAX_SVG_DEPTH:
            raise SvgImportError("SVG слишком сложный: превышен лимит элементов или вложенности")
        tag = _local_name(element.tag)
        if tag not in _ALLOWED_TAGS:
            raise SvgImportError(f"Элемент SVG «{tag}» не поддерживается или запрещён")
        if element.tag.startswith("{") and not element.tag.startswith("{" + SVG_NS + "}"):
            raise SvgImportError("Внешние XML-пространства имён запрещены")
        element.tag = "{" + SVG_NS + "}" + tag
        cleaned_attrs: dict[str, str] = {}
        for raw_name, raw_value in list(element.attrib.items()):
            if raw_name.startswith("{"):
                namespace = raw_name[1:].split("}", 1)[0]
                if namespace not in {SVG_NS, XLINK_NS}:
                    raise SvgImportError("Атрибуты внешних XML-пространств имён запрещены")
                if namespace == XLINK_NS and _local_name(raw_name) != "href":
                    raise SvgImportError("В пространстве xlink поддерживается только href")
            name = _local_name(raw_name)
            value = str(raw_value).strip()
            if name.lower().startswith("on"):
                raise SvgImportError("Обработчики событий SVG (on*) запрещены")
            if name not in _ALLOWED_ATTRS:
                # Remove editor metadata and unknown presentation extensions instead of serving them.
                del element.attrib[raw_name]
                continue
            if len(value) > 10_000 or any(ord(ch) < 32 and ch not in "\t\n\r" for ch in value):
                raise SvgImportError(f"Недопустимое значение атрибута {name}")
            if name == "id":
                if not _ID_RE.fullmatch(value) or value in ids:
                    raise SvgImportError("SVG содержит некорректный или повторяющийся id")
                ids.add(value)
            if name == "href":
                if not value.startswith("#") or not _ID_RE.fullmatch(value[1:]):
                    raise SvgImportError("Допускаются только локальные ссылки href на #id")
                references.append(value[1:])
            for match in _URL_RE.finditer(value):
                ref = match.group(2).strip()
                if not ref.startswith("#") or not _ID_RE.fullmatch(ref[1:]):
                    raise SvgImportError("Внешние URL и ресурсы в SVG запрещены")
                references.append(ref[1:])
            if re.search(r"javascript:|data:|vbscript:|expression\s*\(|@import", value, re.I):
                raise SvgImportError("Недопустимое активное содержимое в SVG")
            if name == "style":
                for declaration in value.split(";"):
                    if not declaration.strip():
                        continue
                    if ":" not in declaration:
                        raise SvgImportError("Некорректный inline style в SVG")
                    prop, css_value = declaration.split(":", 1)
                    if prop.strip() not in _STYLE_PROPERTIES:
                        raise SvgImportError(f"CSS-свойство {prop.strip()} запрещено в SVG")
                    for match in _URL_RE.finditer(css_value):
                        ref = match.group(2).strip()
                        if not ref.startswith("#") or not _ID_RE.fullmatch(ref[1:]):
                            raise SvgImportError("Внешние URL в SVG-стилях запрещены")
            cleaned_attrs[raw_name] = value
        element.attrib.clear()
        element.attrib.update(cleaned_attrs)
        if element.text and len(element.text) > 20_000:
            raise SvgImportError("Слишком большой текстовый фрагмент SVG")
        for child in list(element):
            clean(child, depth + 1)

    clean(root)
    for reference in references:
        if reference not in ids:
            raise SvgImportError(f"SVG ссылается на отсутствующий локальный id #{reference}")
    view_box = root.attrib.get("viewBox")
    if view_box:
        try:
            parts = [float(x) for x in re.split(r"[\s,]+", view_box.strip())]
            if len(parts) != 4 or not all(x == x and abs(x) < 1e7 for x in parts) or parts[2] <= 0 or parts[3] <= 0:
                raise ValueError
        except ValueError as exc:
            raise SvgImportError("SVG viewBox должен содержать четыре конечных числа с положительной шириной и высотой") from exc
    elif not (root.attrib.get("width") and root.attrib.get("height")):
        raise SvgImportError("SVG должен задавать viewBox либо width и height")
    cleaned = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return cleaned, {"viewBox": root.attrib.get("viewBox", ""), "nodes": str(node_count)}


class CustomSvgLibrary:
    """Persistent station-scoped custom SVG library stored in SQLite."""
    def __init__(self, database_path: str | Path):
        self.path = str(database_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with sqlite3.connect(self.path) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS custom_svg_assets (
                symbol_id TEXT PRIMARY KEY, station_id TEXT NOT NULL, name TEXT NOT NULL,
                category TEXT NOT NULL, filename TEXT NOT NULL, svg BLOB NOT NULL,
                sha256 TEXT NOT NULL, created_at TEXT NOT NULL)""")
            db.execute("CREATE INDEX IF NOT EXISTS idx_custom_svg_station ON custom_svg_assets(station_id, category, name)")
            db.commit()

    def import_svg(self, station_id: str, *, name: str, category: str, filename: str, svg: str | bytes) -> dict:
        from uuid import UUID
        try:
            UUID(station_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise SvgImportError("Некорректный идентификатор станции") from exc
        name = str(name or "").strip()
        category = str(category or "Пользовательские").strip()
        filename = re.split(r"[\\/]", str(filename or "import.svg"))[-1]
        if not name or len(name) > 160:
            raise SvgImportError("Название символа должно содержать от 1 до 160 символов")
        if not category or len(category) > 80:
            raise SvgImportError("Категория должна содержать от 1 до 80 символов")
        if not filename.lower().endswith(".svg") or len(filename) > 180:
            raise SvgImportError("Импортируемый файл должен иметь расширение .svg")
        cleaned, info = sanitize_svg(svg)
        symbol_id = "custom_" + uuid.uuid4().hex
        created = datetime.now(timezone.utc).isoformat()
        digest = hashlib.sha256(cleaned).hexdigest()
        with self._lock, sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO custom_svg_assets VALUES(?,?,?,?,?,?,?,?)",
                       (symbol_id, station_id, name, category, filename, cleaned, digest, created))
            db.commit()
        return {"id": symbol_id, "symbol_key": symbol_id, "station_id": station_id, "name": name,
                "category": category, "filename": filename, "sha256": digest, "created_at": created,
                "svg_url": f"/api/graphics/custom-symbols/{symbol_id}/svg", "viewBox": info["viewBox"]}

    def list_for_station(self, station_id: str) -> list[dict]:
        with self._lock, sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute("SELECT symbol_id,station_id,name,category,filename,sha256,created_at FROM custom_svg_assets WHERE station_id=? ORDER BY category COLLATE NOCASE,name COLLATE NOCASE", (station_id,)).fetchall()
        return [{"id": r["symbol_id"], "symbol_key": r["symbol_id"], "station_id": r["station_id"],
                 "name": r["name"], "category": r["category"], "filename": r["filename"],
                 "sha256": r["sha256"], "created_at": r["created_at"],
                 "svg_url": f"/api/graphics/custom-symbols/{r['symbol_id']}/svg"} for r in rows]

    def get(self, symbol_id: str, station_id: str | None = None) -> dict:
        with self._lock, sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            if station_id is None:
                row = db.execute("SELECT * FROM custom_svg_assets WHERE symbol_id=?", (symbol_id,)).fetchone()
            else:
                row = db.execute("SELECT * FROM custom_svg_assets WHERE symbol_id=? AND station_id=?", (symbol_id, station_id)).fetchone()
        if row is None:
            raise KeyError(symbol_id)
        return {"id": row["symbol_id"], "symbol_key": row["symbol_id"], "station_id": row["station_id"],
                "name": row["name"], "category": row["category"], "filename": row["filename"],
                "sha256": row["sha256"], "created_at": row["created_at"], "svg": bytes(row["svg"])}

    def read_svg(self, symbol_id: str, station_id: str | None = None) -> bytes:
        return self.get(symbol_id, station_id)["svg"]

    def delete(self, symbol_id: str, station_id: str) -> bool:
        with self._lock, sqlite3.connect(self.path) as db:
            cur = db.execute("DELETE FROM custom_svg_assets WHERE symbol_id=? AND station_id=?", (symbol_id, station_id))
            db.commit()
            return cur.rowcount == 1
