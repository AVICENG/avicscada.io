"""DEV67: AVIC 3D HVAC/ITP SVG library with modular animated AHU sections."""
from pathlib import Path
import xml.etree.ElementTree as ET

from fastapi.testclient import TestClient

from avic_core.graphics.svg_library import SVG_DIR, SVG_SYMBOLS, list_symbols, read_symbol_svg
from avic_core.ui.app import create_ui_app


def test_iso3d_library_contains_66_original_assets_and_niagara_like_hvac_categories():
    items = list_symbols()
    assert len(items) == len(SVG_SYMBOLS) == 66
    assert len({x["category"] for x in items}) >= 15
    categories = {x["category"] for x in items}
    assert "Вентиляция" in categories
    assert "Воздуховоды и секции" in categories
    assert "Воздушные заслонки" in categories
    assert "Вентиляторы" in categories
    assert "ИТП · теплообменники" in categories
    assert "ИТП · насосы" in categories
    assert {"fan", "damper", "heating_coil", "cooling_coil", "duct", "duct_elbow",
            "duct_tee", "heat_exchanger", "pump_group_dual", "itp_heating_substation"} <= set(SVG_SYMBOLS)
    assert {x["visual_style"] for x in items} == {"isometric-3d", "isometric-3d-modular-cutaway"}
    assert all("3D" in x["tags"] and "изометрия" in x["tags"] for x in items)


def test_every_iso3d_svg_is_well_formed_self_contained_vector_with_depth_and_shading():
    assert len(list(SVG_DIR.glob("*.svg"))) >= 66
    for key in SVG_SYMBOLS:
        payload = read_symbol_svg(key)
        root = ET.fromstring(payload)
        assert root.tag.endswith("svg")
        assert root.attrib.get("viewBox") == ("35 62 317 185" if key.startswith("ahu_section_") else "0 0 320 200")
        assert root.attrib.get("data-avic-style") == "iso3d"
        lowered = payload.decode("utf-8").lower()
        assert "lineargradient" in lowered
        assert "filter id=\"shadow\"" in lowered or (key.startswith("ahu_section_") and "_shadow\"" in lowered)
        assert "<script" not in lowered
        assert "foreignobject" not in lowered
        assert "javascript:" not in lowered
        assert "http://" not in lowered.replace('xmlns="http://www.w3.org/2000/svg"', '').replace('xmlns:xlink="http://www.w3.org/1999/xlink"', '')
        assert " onload=" not in lowered and " onclick=" not in lowered


def test_key_hvac_assets_expose_rotor_or_hot_cold_visual_geometry():
    for key in ("fan", "fan_centrifugal", "fan_belt_drive", "fan_plug", "fan_roof", "fan_twin", "cooling_tower"):
        text = read_symbol_svg(key).decode("utf-8")
        assert 'id="rotor"' in text and 'class="anim-rotor"' in text
    for key in ("heating_coil", "cooling_coil", "heat_exchanger", "shell_tube_exchanger", "itp_heating_substation", "itp_dhw_substation"):
        text = read_symbol_svg(key).decode("utf-8")
        assert "redPipe" in text or "redCoil" in text
        assert "bluePipe" in text or "blueCoil" in text
    for key in ("damper", "damper_parallel", "damper_opposed", "fire_damper", "smoke_damper"):
        text = read_symbol_svg(key).decode("utf-8")
        assert "motorGreen" in text and "metalFront" in text


def test_iso3d_assets_are_listed_and_served_by_api_without_changing_legacy_symbol_keys(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    response = client.get("/api/graphics/library")
    assert response.status_code == 200
    payload = response.json()
    assert payload["style"] == "isometric-3d"
    assert payload["count"] == 66
    ids = {item["id"] for item in payload["items"]}
    assert "fan" in ids and "damper" in ids and "heat_exchanger" in ids
    assert "itp_heating_substation" in ids and "duct_elbow" in ids
    assert {"ahu_section_outdoor_damper", "ahu_section_filter", "ahu_section_heat_recovery", "ahu_section_heating_coil", "ahu_section_cooling_coil", "ahu_section_supply_fan", "ahu_section_open_plenum"} <= ids
    for item in payload["items"]:
        served = client.get(item["svg_url"])
        assert served.status_code == 200, item["id"]
        assert served.headers["content-type"].startswith("image/svg+xml")
        assert served.headers["x-content-type-options"] == "nosniff"
        assert b'data-avic-style="iso3d"' in served.content
    app.state.core.close()
