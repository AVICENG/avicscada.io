"""DEV102: end-to-end read-only Point Runtime -> FBD -> AHU fan animation binding."""
from uuid import uuid4
from fastapi.testclient import TestClient

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.ui.app import create_ui_app


def _make_ahu_chain(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "data"))
    core = app.state.core
    project = app.state.project_station.create_project("AHU DEV102")
    station = app.state.project_station.create_station(project["id"], "AHU-01")
    driver = core.driver_manager.create_instance(
        station["id"], "bacnet-ip", "DEV102 BACnet", {}
    )
    device = Device(name="Virtual AHU Controller", station_id=station["id"],
                    protocol="bacnet/ip", address="192.0.2.50", driver_instance_id=driver["id"])
    core.repository.save(device)
    point = Point(name="Fan run feedback", device_id=device.id, data_type="binary-input",
                  value=None, quality=PointQuality.UNCERTAIN, unit="")
    core.repository.save(point)
    core.point_runtime.publish(point.id, True, quality="GOOD", source_driver_id=device.driver_instance_id)

    graphic = app.state.graphics.create_modular_ahu_demo(station["id"])
    fan = next(x for x in graphic["elements"] if x["symbol_key"] == "ahu_section_supply_fan")

    fbd = app.state.fbd.create(station["id"], "AHU fan permissive")
    fbd = app.state.fbd.add_point_node(fbd["id"], point.id)
    point_node = next(n for n in fbd["nodes"] if n["type"] == "POINT_INPUT")
    safety_id, and_id = str(uuid4()), str(uuid4())
    nodes = fbd["nodes"] + [
        {"id": safety_id, "type": "BOOL_INPUT", "name": "Thermal protection healthy",
         "x": 120, "y": 240, "params": {"value": True}},
        {"id": and_id, "type": "AND", "name": "Fan run permissive", "x": 420, "y": 160},
    ]
    links = [
        {"source_node_id": point_node["id"], "source_port": "OUT",
         "target_node_id": and_id, "target_port": "A"},
        {"source_node_id": safety_id, "source_port": "OUT",
         "target_node_id": and_id, "target_port": "B"},
    ]
    fbd = app.state.fbd.save(fbd["id"], fbd["revision"], nodes, links)
    binding = app.state.fbd.bind_graphic_output(fan["id"], and_id, "OUT")
    return app, station, point, graphic, fan, fbd, binding, and_id


def test_real_point_to_fbd_bool_output_drives_ahu_fan_binding_and_persists(tmp_path):
    app, station, point, graphic, fan, fbd, binding, and_id = _make_ahu_chain(tmp_path)
    try:
        assert binding["graphic_element_id"] == fan["id"]
        # Saving the drawing must not delete the FBD link on the modular AHU fan symbol.
        saved = app.state.graphics.save(graphic["id"], graphic["revision"], graphic["elements"])
        reopened_fan = next(x for x in saved["elements"] if x["id"] == fan["id"])
        assert reopened_fan["logic_bindings"][0]["logic_node_id"] == and_id

        evaluated = app.state.fbd.evaluate_graphic_bindings(graphic["id"])
        state = evaluated["bindings"][binding["id"]]
        assert state["quality"] == "GOOD"
        assert state["value"] is True
        assert state["field_writes_performed"] is False
        assert evaluated["mode"] == "SIMULATION_ONLY"
        assert evaluated["runtime_published"] is False

        driver_id = app.state.core.repository.get_record(point.device_id)["payload"]["driver_instance_id"]
        app.state.core.point_runtime.publish(point.id, False, quality="GOOD", source_driver_id=driver_id)
        stopped = app.state.fbd.evaluate_graphic_bindings(graphic["id"])["bindings"][binding["id"]]
        assert stopped["quality"] == "GOOD" and stopped["value"] is False

        app.state.core.point_runtime.publish(point.id, True, quality="UNCERTAIN", source_driver_id=driver_id)
        degraded = app.state.fbd.evaluate_graphic_bindings(graphic["id"])["bindings"][binding["id"]]
        assert degraded["quality"] == "BAD" and degraded["value"] is None
    finally:
        app.state.core.close()


def test_ahu_fbd_logic_evaluation_http_endpoint_and_editor_hook(tmp_path):
    app, station, point, graphic, fan, fbd, binding, and_id = _make_ahu_chain(tmp_path)
    try:
        client = TestClient(app)
        response = client.get(f"/api/graphics/{graphic['id']}/logic-bindings/evaluate")
        assert response.status_code == 200, response.text
        assert response.json()["bindings"][binding["id"]]["value"] is True
        html = client.get("/graphics").text
        assert "/logic-bindings/evaluate" in html
        assert "logicEvaluations" in html
        assert "ahu_section_supply_fan" in html
        assert "elementFeedbackOn" in html
        assert "animationTimes" in html
        assert 'class="hitbox"' in html
    finally:
        app.state.core.close()


def test_fbd_output_rejects_non_bool_for_modular_ahu_fan(tmp_path):
    app, station, point, graphic, fan, fbd, binding, and_id = _make_ahu_chain(tmp_path)
    try:
        # Existing bool binding is valid; the fan cannot bind an analog output node.
        analog_id = str(uuid4())
        changed = app.state.fbd.save(fbd["id"], fbd["revision"], fbd["nodes"] + [
            {"id": analog_id, "type": "FLOAT_INPUT", "name": "Speed reference",
             "x": 50, "y": 360, "params": {"value": 35.0}}
        ], fbd["links"])
        import pytest
        with pytest.raises(ValueError, match="BOOL-выход"):
            app.state.fbd.bind_graphic_output(fan["id"], analog_id, "OUT")
    finally:
        app.state.core.close()


def test_rebinding_ahu_fan_replaces_old_logic_link_instead_of_duplicating(tmp_path):
    app, station, point, graphic, fan, fbd, binding, and_id = _make_ahu_chain(tmp_path)
    try:
        second_id = str(uuid4())
        changed = app.state.fbd.save(fbd["id"], fbd["revision"], fbd["nodes"] + [
            {"id": second_id, "type": "NOT", "name": "Invert permissive", "x": 620, "y": 160}
        ], fbd["links"])
        replacement = app.state.fbd.bind_graphic_output(fan["id"], second_id, "OUT")
        reopened = app.state.graphics.get(graphic["id"])
        reopened_fan = next(x for x in reopened["elements"] if x["id"] == fan["id"])
        assert len(reopened_fan["logic_bindings"]) == 1
        assert reopened_fan["logic_bindings"][0]["id"] == replacement["id"]
        assert reopened_fan["logic_bindings"][0]["logic_node_id"] == second_id
    finally:
        app.state.core.close()
