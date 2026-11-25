from fastapi.testclient import TestClient
import pytest

from avic_core.repository.sqlite_repository import ConcurrencyConflict
from avic_core.ui import create_ui_app


def _station(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV141")
    station = app.state.project_station.create_station(project["id"], "Binding station")
    return app, station


def test_stopped_driver_config_update_uses_optimistic_version_and_secret_guard(tmp_path):
    app, station = _station(tmp_path)
    created = app.state.driver_manager.create_instance(station["id"], "modbus-tcp", "Modbus", {})
    view = app.state.driver_manager.get_instance(created["id"])
    changed = app.state.driver_manager.update_config(
        created["id"], {"host": "192.0.2.10", "port": 502, "bindings": []},
        expected_version=view["version"])
    assert changed["version"] == view["version"] + 1
    assert changed["config"]["host"] == "192.0.2.10"
    with pytest.raises(ConcurrencyConflict):
        app.state.driver_manager.update_config(
            created["id"], {"host": "192.0.2.11"}, expected_version=view["version"])
    with pytest.raises(ValueError, match="SecretStore"):
        app.state.driver_manager.update_config(
            created["id"], {"api_token": "must-not-persist"},
            expected_version=changed["version"])
    app.state.core.close()


def test_driver_config_cannot_change_while_runtime_is_active(tmp_path):
    app, station = _station(tmp_path)
    created = app.state.driver_manager.create_instance(
        station["id"], "modbus-tcp", "Modbus", {"poll_interval_seconds": 0.1})

    class Adapter:
        def poll_once(self):
            return {"results": []}

        def close(self):
            pass

    app.state.driver_manager.register_adapter_factory("modbus-tcp", lambda _core, _item: Adapter())
    app.state.driver_manager.start_instance(created["id"])
    current = app.state.driver_manager.get_instance(created["id"])
    with pytest.raises(RuntimeError, match="остановленного драйвера"):
        app.state.driver_manager.update_config(
            created["id"], {"host": "192.0.2.99"}, expected_version=current["version"])
    app.state.driver_manager.stop_instance(created["id"])
    app.state.core.close()


def test_import_commits_modbus_bindings_with_points_and_is_idempotent(tmp_path):
    from tests.test_protocol_point_import_dev140 import _setup

    app, station, driver, inspection = _setup(tmp_path)
    native = inspection["points"][0]["native_identity"]
    preview = app.state.protocol_point_import.preview(station["id"], driver["id"], inspection, [native])
    assert preview["bindings_validated"] is True
    assert preview["binding_count"] == 1
    result = app.state.protocol_point_import.import_points(station["id"], driver["id"], inspection, [native])
    driver_item, _ = app.state.core.repository.get(driver["id"], __import__(
        "avic_core.drivers.manager", fromlist=["DriverInstance"]).DriverInstance)
    binding = driver_item.config["bindings"][0]
    assert binding["point_id"] == result["points_added"][0]
    assert (binding["function"], binding["address"], binding["data_type"]) == (3, 0, "uint16")
    assert driver_item.config["host"] == "10.20.0.15"
    assert driver_item.config["port"] == 502
    again = app.state.protocol_point_import.import_points(station["id"], driver["id"], inspection, [native])
    assert again["points_added"] == []
    assert len(driver_item.config["bindings"]) == 1
    app.state.core.close()


def test_import_builds_bacnet_readproperty_binding_from_confirmed_object_identity(tmp_path):
    from tests.test_protocol_point_import_dev140 import _setup
    from avic_core.drivers.manager import DriverInstance

    app, station, driver, inspection = _setup(tmp_path, driver_id="bacnet-ip")
    native = inspection["points"][0]["native_identity"]
    result = app.state.protocol_point_import.import_points(station["id"], driver["id"], inspection, [native])
    driver_item, _ = app.state.core.repository.get(driver["id"], DriverInstance)
    binding = driver_item.config["bindings"][0]
    assert binding == {
        "point_id": result["points_added"][0],
        "address": ["10.20.0.15", 47808],
        "device_instance": 123,
        "object_type": 0,
        "object_instance": 1,
        "property_id": 85,
    }
    app.state.core.close()


def test_driver_config_api_is_local_and_version_guarded(tmp_path):
    app, station = _station(tmp_path)
    client = TestClient(app)
    created = client.post(
        f"/api/stations/{station['id']}/drivers",
        json={"driver_id": "modbus-tcp", "name": "API Modbus"}).json()
    view = client.get(f"/api/driver-instances/{created['id']}").json()
    denied = client.put(
        f"/api/driver-instances/{created['id']}/config",
        json={"expected_version": view["version"], "config": {"host": "192.0.2.20"}},
        headers={"origin": "https://evil.example"})
    assert denied.status_code == 403
    updated = client.put(
        f"/api/driver-instances/{created['id']}/config",
        json={"expected_version": view["version"], "config": {"host": "192.0.2.20"}})
    assert updated.status_code == 200
    stale = client.put(
        f"/api/driver-instances/{created['id']}/config",
        json={"expected_version": view["version"], "config": {"host": "192.0.2.21"}})
    assert stale.status_code == 409
    app.state.core.close()
