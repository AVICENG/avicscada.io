"""Read-only parser for Trend TSITE XML exports."""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET


class TrendTSiteError(ValueError):
    """Invalid or unsupported TSITE export."""


def _safe_int(value: str | None, field: str) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise TrendTSiteError(f"Некорректное целое значение {field}: {value!r}") from exc


def parse_tsite(source: str | Path | bytes, *, max_bytes: int = 32 * 1024 * 1024) -> dict:
    """Parse a Trend TSOM XML export without executing or mutating anything."""
    if isinstance(source, bytes):
        raw = source
    else:
        path = Path(source)
        try:
            if path.stat().st_size > max_bytes:
                raise TrendTSiteError("TSITE превышает допустимый размер")
            raw = path.read_bytes()
        except OSError as exc:
            raise TrendTSiteError(f"Не удалось прочитать TSITE: {exc}") from exc
    if len(raw) > max_bytes:
        raise TrendTSiteError("TSITE превышает допустимый размер")
    if not raw.strip():
        raise TrendTSiteError("TSITE пуст")
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        raise TrendTSiteError(f"Ошибка XML TSITE: {exc}") from exc
    if root.tag != "TrendProject":
        raise TrendTSiteError("Ожидался корневой элемент TrendProject")
    sites, lans = [], []
    device_count = module_count = parameter_count = 0
    device_types, versions = Counter(), Counter()
    for site_index, site in enumerate(root.findall("./Site")):
        site_info = {"index": site_index, "cnc_address": site.attrib.get("CncAddress", ""),
                     "tua_string": site.attrib.get("TuaString", ""), "lans": []}
        for lan in site.findall(".//Lan"):
            lan_number = _safe_int(lan.attrib.get("LanNumber"), "LanNumber")
            devices = []
            for device in lan.findall("./Device"):
                overview = device.find("DeviceOverview")
                dtype = overview.attrib.get("DeviceType", "") if overview is not None else ""
                modules = []
                for module in device.findall("Module"):
                    params = [{"name": q.attrib.get("Name", ""),
                               "type_code": _safe_int(q.attrib.get("Type"), "Param.Type"),
                               "raw_value": q.attrib.get("Value", "")} for q in module.findall("Param")]
                    modules.append({"name": module.attrib.get("Name", ""),
                                    "subtype_number": _safe_int(module.attrib.get("SubTypeNumber"), "Module.SubTypeNumber"),
                                    "parameters": params})
                    module_count += 1
                    parameter_count += len(params)
                devices.append({
                    "device_number": _safe_int(device.attrib.get("DeviceNumber"), "DeviceNumber"),
                    "version": device.attrib.get("VersionString", ""), "device_type": dtype,
                    "major_version": _safe_int(overview.attrib.get("MajorVersion"), "MajorVersion") if overview is not None else None,
                    "minor_version": _safe_int(overview.attrib.get("MinorVersion"), "MinorVersion") if overview is not None else None,
                    "revision": _safe_int(overview.attrib.get("Revision"), "Revision") if overview is not None else None,
                    "hex_identity": overview.attrib.get("HexEncoded", "") if overview is not None else "",
                    "modules": modules})
                device_count += 1
                device_types[dtype or "UNKNOWN"] += 1
                if device.attrib.get("VersionString"):
                    versions[device.attrib["VersionString"]] += 1
            item = {"number": lan_number, "is_local": lan.attrib.get("IsLocal", "").casefold() == "true",
                    "devices": devices}
            site_info["lans"].append(item)
            lans.append(item)
        sites.append(site_info)
    if not sites:
        raise TrendTSiteError("В TSITE не найден ни один Site")
    return {"format": "Trend TSOM TSITE XML", "site_count": len(sites), "lan_count": len(lans),
            "device_count": device_count, "module_count": module_count, "parameter_count": parameter_count,
            "device_types": dict(device_types), "versions": dict(versions), "sites": sites,
            "import_policy": {"mode": "read_only_inventory_preview", "physical_points_created": False,
                "logic_created": False, "controller_writes_performed": False,
                "note": "Параметры Trend сохранены как исходные данные; они не классифицируются как точки или логика без схемы формата и профиля устройства."}}
