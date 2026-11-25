from fastapi.testclient import TestClient
import pytest

from avic_core.ui import create_ui_app


def _setup(tmp_path, driver_id="modbus-tcp"):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV140 Project")
    station = app.state.project_station.create_station(project["id"], "DEV140 Station")
    driver = app.state.core.driver_manager.create_instance(
        station["id"], driver_id, "Field protocol driver", {})
    protocol = "modbus/tcp" if driver_id == "modbus-tcp" else "bacnet/ip"
    inspection = {
        "protocol": protocol,
        "network_id": "lan-01",
        "device": {
            "native_identity": f"{protocol}:device:10.20.0.15",
            "address": "10.20.0.15:502" if driver_id == "modbus-tcp" else "10.20.0.15:47808",
            "name": "Test controller",
            "manufacturer": "Example Vendor",
            "model": "Controller-X",
            "identity_sources": {"manufacturer": "discovery response"},
        },
        "points": [
            {"native_identity": f"{protocol}:holding-register:40001", "name": "Supply temperature",
             "data_type": "float", "unit": "°C", "direction": "input", "object_type": "holding-register"},
            {"native_identity": f"{protocol}:coil:00001", "name": "Fan command",
             "data_type": "bool", "unit": "", "direction": "output", "object_type": "coil"},
        ],
    }
    return app, station, driver, inspection


def test_protocol_neutral_import_preview_is_non_mutating_and_import_is_idempotent(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    service = app.state.protocol_point_import
    selected = [inspection["points"][0]["native_identity"]]

    preview = service.preview(station["id"], driver["id"], inspection, selected)
    assert preview["can_import"] is True
    assert preview["new_points"] == selected
    assert preview["device_exists"] is False
    assert app.state.core.repository.list_records(entity_type="Device", station_id=station["id"]) == []

    first = service.import_points(station["id"], driver["id"], inspection, selected)
    second = service.import_points(station["id"], driver["id"], inspection, selected)
    tree = app.state.device_import.station_tree(station["id"])

    assert first["device_created"] is True
    assert len(first["points_added"]) == 1
    assert second["device_created"] is False
    assert second["points_added"] == []
    assert len(second["points_skipped_existing"]) == 1
    assert len(tree["devices"]) == 1
    assert len(tree["devices"][0]["points"]) == 1
    assert tree["devices"][0]["points"][0]["native_identity"] == selected[0]
    app.state.core.close()


def test_imported_point_is_immediately_available_to_shared_runtime_and_fbd(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    native = inspection["points"][0]["native_identity"]
    result = app.state.protocol_point_import.import_points(
        station["id"], driver["id"], inspection, [native])
    point_id = result["points_added"][0]

    sample = app.state.core.point_runtime.publish(
        point_id, 21.75, quality="GOOD", source_driver_id=driver["id"])
    assert app.state.core.point_runtime.read(point_id).value == 21.75
    assert sample.quality == "GOOD"

    doc = app.state.fbd.create(station["id"], "DEV140 imported point")
    doc = app.state.fbd.add_point_node(doc["id"], point_id)
    simulation = app.state.fbd.simulate(doc["id"])
    node = next(n for n in doc["nodes"] if n["type"] == "POINT_INPUT")
    assert simulation["node_values"][f'{node["id"]}:OUT'] == 21.75
    app.state.core.close()


def test_protocol_import_rejects_wrong_station_driver_protocol_and_duplicate_native_ids(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    project = app.state.project_station.create_project("Other")
    other_station = app.state.project_station.create_station(project["id"], "Other station")
    with pytest.raises(ValueError, match="другой станции"):
        app.state.protocol_point_import.preview(other_station["id"], driver["id"], inspection)

    bad_protocol = dict(inspection, protocol="knxnet/ip")
    with pytest.raises(ValueError, match="не поддерживает общий импорт"):
        app.state.protocol_point_import.preview(station["id"], driver["id"], bad_protocol)

    duplicate = dict(inspection, points=[inspection["points"][0], dict(inspection["points"][0])])
    with pytest.raises(ValueError, match="повторяется"):
        app.state.protocol_point_import.import_points(station["id"], driver["id"], duplicate, import_all=True)

    assert app.state.core.repository.list_records(entity_type="Device", station_id=station["id"]) == []
    app.state.core.close()


def test_protocol_import_api_preview_and_commit(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    client = TestClient(app)
    native = inspection["points"][0]["native_identity"]
    payload = {"driver_instance_id": driver["id"], "inspection": inspection,
               "selected_native_ids": [native]}

    preview = client.post(
        f"/api/stations/{station['id']}/protocol-devices/import-preview", json=payload)
    assert preview.status_code == 200
    assert preview.json()["new_points"] == [native]

    imported = client.post(
        f"/api/stations/{station['id']}/protocol-devices/import", json=payload)
    assert imported.status_code == 200
    assert len(imported.json()["points_added"]) == 1
    app.state.core.close()



def test_same_normalized_import_contract_accepts_bacnet_points(tmp_path):
    app, station, driver, inspection = _setup(tmp_path, driver_id="bacnet-ip")
    inspection["points"][0]["data_type"] = "analog-input"
    inspection["points"][1]["data_type"] = "binary-output"
    native = inspection["points"][0]["native_identity"]
    result = app.state.protocol_point_import.import_points(
        station["id"], driver["id"], inspection, [native])
    point = app.state.core.repository.get_record(result["points_added"][0])
    assert point["payload"]["data_type"] == "analog-input"
    assert point["payload"]["direction"]["value"] == "input"
    app.state.core.close()


def test_import_requires_explicit_point_direction(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    del inspection["points"][0]["direction"]
    with pytest.raises(ValueError, match="должно быть задано явно"):
        app.state.protocol_point_import.import_points(
            station["id"], driver["id"], inspection, import_all=True)
    assert app.state.core.repository.list_records(entity_type="Device", station_id=station["id"]) == []
    app.state.core.close()



def test_imported_point_is_selectable_in_graphics_and_web_pages(tmp_path):
    app, station, driver, inspection = _setup(tmp_path)
    native = inspection["points"][0]["native_identity"]
    imported = app.state.protocol_point_import.import_points(
        station["id"], driver["id"], inspection, [native])
    point_id = imported["points_added"][0]
    app.state.core.point_runtime.publish(
        point_id, 23.0, quality="GOOD", source_driver_id=driver["id"])

    catalog = app.state.graphics.points(station["id"])
    assert any(item["id"] == point_id and item["protocol"] == "modbus/tcp" for item in catalog)

    graphic = app.state.graphics.create(station["id"], "DEV140 Graphic")
    saved = app.state.graphics.save(graphic["id"], graphic["revision"], [{
        "name": "Supply fan", "symbol_key": "fan", "x": 20, "y": 20,
        "width": 120, "height": 100,
        "bindings": [{"point_id": point_id, "role": "value"}],
    }])
    assert saved["elements"][0]["bindings"][0]["point_id"] == point_id
    evaluated = app.state.graphics.evaluate_bindings(graphic["id"])
    assert evaluated

    site = app.state.web_pages.create(station["id"], "Site", "site")
    page = app.state.web_pages.create(station["id"], "Overview", "page", parent_id=site["id"])
    updated = app.state.web_pages.update(page["id"], page["revision"], layout=[{
        "type": "value", "point_id": point_id, "x": 10, "y": 10, "width": 240, "height": 100,
    }])
    assert updated["layout"][0]["point_id"] == point_id
    app.state.core.close()
