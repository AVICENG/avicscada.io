import pytest

from avic_core.graphics.binding_engine import evaluate_binding, validate_binding_config
from avic_core.graphics import GraphicsService
from test_graphics_workbench_dev35 import setup


def test_numeric_binding_format_scale_offset_and_unit():
    result = evaluate_binding(binding_type="bound_label", target_property="text",
        settings={"converter": "numeric", "decimals": 1, "scale": 1.8, "offset": 32, "unit": " °F"},
        value=20, quality="GOOD")
    assert result.display_text == "68.0 °F"
    assert result.quality == "GOOD" and not result.degraded


def test_boolean_binding_maps_labels_and_animation_only_on_good_feedback():
    good = evaluate_binding(binding_type="status", target_property="animation",
        settings={"converter": "boolean", "true_text": "РАБОТАЕТ", "false_text": "ОСТАНОВЛЕН"},
        value=True, quality="GOOD")
    assert good.display_text == "РАБОТАЕТ" and good.animation_allowed
    bad = evaluate_binding(binding_type="status", target_property="animation", value=True, quality="STALE")
    assert not bad.animation_allowed and not bad.interaction_allowed and bad.display_text == "STALE"


def test_spectrum_binding_maps_numeric_thresholds_to_color():
    result = evaluate_binding(binding_type="spectrum", target_property="color",
        settings={"converter": "numeric", "thresholds": [
            {"min": 0, "max": 10, "color": "#00AA00"},
            {"min": 10, "max": 20, "color": "#FF0000"}]}, value=15, quality="GOOD")
    assert result.value == "#FF0000"


def test_degrade_behaviors_never_leave_animation_or_interaction_enabled():
    for behavior in ("show_quality", "hide", "safe_default"):
        result = evaluate_binding(target_property="animation", settings={"degrade_behavior": behavior,
            "safe_default": False}, value=True, quality="COMM_LOST")
        assert result.degraded and not result.animation_allowed and not result.interaction_allowed
    hidden = evaluate_binding(settings={"degrade_behavior": "hide"}, quality="BAD")
    assert hidden.visible is False


def test_action_and_setpoint_are_contract_only_without_command_manager():
    for kind in ("action", "setpoint"):
        result = evaluate_binding(binding_type=kind, target_property="value", value=1, quality="GOOD")
        assert result.diagnostic == "COMMAND_MANAGER_NOT_CONNECTED"
        assert result.interaction_allowed is False


def test_invalid_binding_settings_are_rejected():
    with pytest.raises(ValueError):
        validate_binding_config("spectrum", "color", {"thresholds": [
            {"min": 0, "max": 10, "color": "#00FF00"},
            {"min": 9, "max": 20, "color": "#FF0000"}]})
    with pytest.raises(ValueError):
        validate_binding_config("value", "text", {"hyperlink": "//evil.example"})
    with pytest.raises(ValueError):
        validate_binding_config("value", "text", {"decimals": 99})


def test_graphics_service_persists_multiple_independent_bindings_on_same_role(tmp_path):
    core, station, point = setup(tmp_path)
    service = GraphicsService(core)
    doc = service.create(station["id"], "Binding config")
    element = {"id": "7c56d5a0-02f5-4a5a-99e6-9a9a5a7d2011", "name": "Temperature",
        "symbol_key": "sensor", "x": 10, "y": 10, "width": 80, "height": 60,
        "bindings": [
            {"point_id": point.id, "role": "value", "binding_type": "bound_label", "target_property": "text",
             "settings": {"converter": "numeric", "decimals": 2, "unit": " °C"}},
            {"point_id": point.id, "role": "value", "binding_type": "spectrum", "target_property": "color",
             "settings": {"converter": "numeric", "thresholds": [{"min": 0, "max": 100, "color": "#00AA00"}]}}
        ]}
    saved = service.save(doc["id"], doc["revision"], [element])
    bindings = saved["elements"][0]["bindings"]
    assert len(bindings) == 2
    assert {b["target_property"] for b in bindings} == {"text", "color"}
    assert next(b for b in bindings if b["target_property"] == "text")["settings"]["unit"] == " °C"


def test_graphics_service_rejects_duplicate_binding_target(tmp_path):
    core, station, point = setup(tmp_path)
    service = GraphicsService(core)
    doc = service.create(station["id"], "Duplicate binding target")
    element = {"id": "7c56d5a0-02f5-4a5a-99e6-9a9a5a7d2012", "name": "Sensor",
        "symbol_key": "sensor", "x": 10, "y": 10, "width": 80, "height": 60,
        "bindings": [{"point_id": point.id, "role": "value", "target_property": "text"},
                      {"point_id": point.id, "role": "value", "target_property": "text"}]}
    with pytest.raises(ValueError, match="уже задана"):
        service.save(doc["id"], doc["revision"], [element])


def test_graphics_binding_runtime_endpoint_returns_core_point_quality_and_formatting(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    from avic_core.ui.project_station import ProjectStationService
    from avic_core.domain.models import Device, DriverInstance, Point, PointQuality
    from avic_core.graphics import GraphicsService
    app = create_ui_app(data_dir=str(tmp_path / "runtime-api"))
    core = app.state.core
    ps = ProjectStationService(core)
    project = ps.create_project("P")
    station = ps.create_station(project["id"], "S")
    driver = DriverInstance(name="Test driver", station_id=station["id"])
    core.repository.save(driver)
    device = Device(name="Device", station_id=station["id"], driver_instance_id=driver.id,
                    address="127.0.0.1", protocol="test")
    core.repository.save(device)
    point = Point(name="Temperature", device_id=device.id, unit="°C", quality=PointQuality.GOOD)
    core.repository.save(point)
    core.point_runtime.publish(point.id, 21.75, quality="GOOD")
    service = GraphicsService(core)
    doc = service.create(station["id"], "Runtime binding")
    element = {"id": "7c56d5a0-02f5-4a5a-99e6-9a9a5a7d2013", "name": "T",
        "symbol_key": "sensor", "x": 10, "y": 10, "width": 80, "height": 60,
        "bindings": [{"point_id": point.id, "role": "value", "binding_type": "bound_label",
                      "target_property": "text", "settings": {"converter": "numeric", "decimals": 1, "unit": " °C"}}]}
    saved = service.save(doc["id"], doc["revision"], [element])
    result = service.evaluate_bindings(doc["id"])
    row = next(iter(result["bindings"].values()))
    assert row["display_text"] == "21.8 °C"
    assert row["quality"] == "GOOD" and row["animation_allowed"] is False
    with TestClient(app) as client:
        response = client.get(f"/api/graphics/{doc['id']}/bindings/evaluate")
        assert response.status_code == 200
        assert next(iter(response.json()["bindings"].values()))["display_text"] == "21.8 °C"


def test_binding_target_compatibility_and_encoded_path_traversal_are_rejected():
    with pytest.raises(ValueError, match="несовместим"):
        validate_binding_config("spectrum", "text", {"thresholds": []})
    with pytest.raises(ValueError, match="внутренним абсолютным"):
        validate_binding_config("hyperlink", "text", {"hyperlink": "/pages/%2e%2e/admin"})
