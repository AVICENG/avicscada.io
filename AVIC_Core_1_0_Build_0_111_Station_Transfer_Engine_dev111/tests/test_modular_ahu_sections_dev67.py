"""DEV67: modular AHU cutaway SVGs, binary animation contract and demo schematic."""
from xml.etree import ElementTree as ET

from fastapi.testclient import TestClient

from avic_core.graphics.service import GraphicsService
from avic_core.graphics.svg_library import SVG_SYMBOLS, list_symbols, read_symbol_svg
from avic_core.ui.app import create_ui_app

AHU_KEYS = [
    "ahu_section_outdoor_damper",
    "ahu_section_filter",
    "ahu_section_heat_recovery",
    "ahu_section_heating_coil",
    "ahu_section_cooling_coil",
    "ahu_section_supply_fan",
    "ahu_section_open_plenum",
]


def test_modular_ahu_has_seven_svg_sections_with_common_mating_geometry():
    assert all(key in SVG_SYMBOLS for key in AHU_KEYS)
    metas = {x["id"]: x for x in list_symbols()}
    assert all(metas[key]["category"] == "ПВУ · модульные секции" for key in AHU_KEYS)
    roots = []
    for key in AHU_KEYS:
        raw = read_symbol_svg(key)
        assert raw.startswith(b"<svg")
        root = ET.fromstring(raw)
        roots.append(root)
        assert root.attrib["viewBox"] == "35 62 317 185"
        text = raw.decode("utf-8")
        assert 'data-avic-style=\"iso3d\"' in text
        assert "class=\"ahu-air-system\"" in text
        assert "state-airflow" in text
        assert 'class=\"ahu-air\" d=\"M36 133 C130 124 250 142 351 133\"' in text
        assert "<script" not in text.lower()
        assert "<foreignobject" not in text.lower()
        assert "javascript:" not in text.lower()
    assert len({r.attrib["viewBox"] for r in roots}) == 1


def test_ahu_animation_hooks_are_declarative_and_only_use_boolean_feedback():
    damper = read_symbol_svg("ahu_section_outdoor_damper").decode("utf-8")
    fan = read_symbol_svg("ahu_section_supply_fan").decode("utf-8")
    plenum = read_symbol_svg("ahu_section_open_plenum").decode("utf-8")
    assert ".state-damper-open .damper-blades" in damper
    assert "class=\"damper-blades\"" in damper
    assert ".state-fan-running .fan-rotor" in fan
    assert "@keyframes avicFanSpin" in fan
    assert ".state-airflow .ahu-air-dash" in fan
    assert "@keyframes avicAirFlow" in fan
    # Open outlet plenum has the same opening, but no opaque external side sheet.
    assert "M310 83 340 99 340 190 310 174Z" not in plenum
    assert "class=\"ahu-air-system\"" in plenum
    assert "prefers-reduced-motion" in damper and "prefers-reduced-motion" in fan


def test_modular_damper_and_fan_support_feedback_binding_slots():
    assert "feedback" in GraphicsService.SYMBOLS["ahu_section_outdoor_damper"]["slots"]
    assert "value" in GraphicsService.SYMBOLS["ahu_section_outdoor_damper"]["slots"]
    assert "feedback" in GraphicsService.SYMBOLS["ahu_section_supply_fan"]["slots"]
    assert "value" in GraphicsService.SYMBOLS["ahu_section_supply_fan"]["slots"]


def test_ahu_demo_api_creates_seven_ordered_sections_and_reopens(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "AHU demo project"})
    assert project.status_code == 201, project.text
    station = client.post("/api/stations", json={"name": "AHU-01", "project_id": project.json()["id"]})
    assert station.status_code == 201, station.text
    created = client.post(f"/api/stations/{station.json()['id']}/graphics/ahu-demo")
    assert created.status_code == 201, created.text
    graphic = created.json()
    assert graphic["width"] == 2050
    assert [x["symbol_key"] for x in sorted(graphic["elements"], key=lambda item: item["x"])] == AHU_KEYS
    assert len({x["x"] for x in graphic["elements"]}) == 7
    assert all(x["width"] == 286 and x["height"] == 228 for x in graphic["elements"])
    reopened = client.get(f"/api/graphics/{graphic['id']}")
    assert reopened.status_code == 200
    assert [x["symbol_key"] for x in sorted(reopened.json()["elements"], key=lambda item: item["x"])] == AHU_KEYS
    app.state.core.close()


def test_graphics_editor_has_inline_svg_animation_and_local_preview_without_field_writes(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    client = TestClient(app)
    html = client.get("/graphics").text
    assert 'id="animationPreview"' in html
    assert "state-damper-open" in html
    assert "state-fan-running" in html
    assert "state-airflow" in html
    assert "elementFeedbackOn" in html
    assert "pointIsGood" in html and "pointIsOn" in html
    assert "airflow:fanRunning&&damperOpen" in html
    assert "refreshPointSnapshot" in html
    assert "if(doc)render()" in html
    assert "/graphics/ahu-demo" in html
    assert "Запись в оборудование не выполняется" in html
    app.state.core.close()


def test_manifest_advertises_modular_ahu_animation_without_enabling_field_writes(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path / "manifest-data")))
    response = client.get("/api/ui/manifest")
    assert response.status_code == 200
    payload = response.json()
    capabilities = payload["capabilities"]
    assert capabilities["modular_ahu_section_count"] == 7
    assert capabilities["modular_ahu_sections"] is True
    assert capabilities["svg_binary_state_animation"] is True
    assert capabilities["ahu_airflow_visualization"] == "fan-running-and-outdoor-damper-open"
    assert payload["field_commands_enabled"] is False

