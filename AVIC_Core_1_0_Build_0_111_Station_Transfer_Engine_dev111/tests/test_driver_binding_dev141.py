from fastapi.testclient import TestClient
import pytest

from avic_core.repository.sqlite_repository import ConcurrencyConflict
from avic_core.ui import create_ui_app


def _station(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV141")
    station = app.state.project_station.create_station(project["id"], "Binding station")
    return app, station


def _import_setup(tmp_path, driver_id="modbus-tcp"):
    app, station = _station(tmp_path)
    driver = app.state.driver_manager.create_instance(station["id"], driver_id, "Field driver", {})
    protocol = "modbus/tcp" if driver_id == "modbus-tcp" else "bacnet/ip"
    if driver_id == "modbus-tcp":
        device_id = f"{protocol}:device:10.20.0.15"
        points = [
            {"native_identity": f"{protocol}:holding-register:40001", "name": "Supply temperature",
             "data_type": "float", "unit": "°C", "direction": "input", "object_type": "holding-register",
             "driver_binding": {"function": 3, "address": 0, "count": 1, "data_type": "uint16", "scale": 0.1}},
            {"native_identity": f"{protocol}:coil:00001", "name": "Fan command",
             "data_type": "bool", "unit": "", "direction": "output", "object_type": "coil",
             "driver_binding": {"function": 1, "address": 0, "count": 1, "data_type": "bool"}},
        ]
    else:
        device_id = f"{protocol}:device:123"
        points = [
            {"native_identity": f"{protocol}:object:0:1", "name": "Supply temperature",
             "data_type": "analog-input", "unit": "°C", "direction": "input", "object_type": "analog-input"},
        ]
    inspection = {
        "protocol": protocol, "network_id": "lan-01",
        "device": {"native_identity": device_id,
                   "address": "10.20.0.15:502" if driver_id == "modbus-tcp" else "10.20.0.15:47808",
                   "device_instance": 123 if driver_id == "bacnet-ip" else None,
                   "name": "Controller"},
        "points": points,
    }
    return app, station, driver, inspection


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
    app, station, driver, inspection = _import_setup(tmp_path)
    native = inspection["points"][0]["native_identity"]
    preview = app.state.protocol_point_import.preview(station["id"], driver["id"], inspection, [native])
    assert preview["bindings_validated"] is True
    assert preview["binding_count"] == 1
    result = app.state.protocol_point_import.import_points(station["id"], driver["id"], inspection, [native])
    from avic_core.drivers.manager import DriverInstance
    driver_item, _ = app.state.core.repository.get(driver["id"], DriverInstance)
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
    from avic_core.drivers.manager import DriverInstance

    app, station, driver, inspection = _import_setup(tmp_path, driver_id="bacnet-ip")
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


def test_protocol_import_rechecks_driver_entitlement_before_any_mutation(tmp_path):
    from types import SimpleNamespace
    from avic_core.licensing import LicenseStatus

    class Entitlements:
        status = LicenseStatus(True, "OK", features=("driver.modbus-tcp",))

        def inspect(self, license_file):
            return SimpleNamespace(status=self.status)

        def assert_feature_enabled(self, status, feature):
            if not status.valid or feature not in status.features:
                raise PermissionError("driver entitlement denied")

    app, station, driver, inspection = _import_setup(tmp_path, driver_id="modbus-tcp")
    app.state.core.installation_license_service = Entitlements()
    app.state.core.license_file = "signed.aviclic"

    # The driver was created while its feature was entitled. Revoke that feature
    # before import and prove that neither Device, Point nor driver bindings commit.
    app.state.core.installation_license_service.status = LicenseStatus(
        True, "OK", features=()
    )
    before_devices = app.state.core.repository.list_records(
        entity_type="Device", station_id=station["id"]
    )
    before_points = app.state.core.repository.list_records(entity_type="Point")
    before_driver = app.state.driver_manager.get_instance(driver["id"])

    with pytest.raises(PermissionError, match="entitlement denied"):
        app.state.protocol_point_import.import_points(
            station["id"], driver["id"], inspection,
            [inspection["points"][0]["native_identity"]],
        )

    assert app.state.core.repository.list_records(
        entity_type="Device", station_id=station["id"]
    ) == before_devices
    assert app.state.core.repository.list_records(entity_type="Point") == before_points
    after_driver = app.state.driver_manager.get_instance(driver["id"])
    assert after_driver["config"] == before_driver["config"]
    assert after_driver["state"] == "STOPPED"
    app.state.core.close()


def test_driver_publication_and_quality_fail_closed_for_unowned_device(tmp_path):
    from avic_core.domain.models import Device, Point

    app, station, driver, inspection = _import_setup(tmp_path, "bacnet-ip")
    native = inspection["points"][0]["native_identity"]
    imported = app.state.protocol_point_import.import_points(
        station["id"], driver["id"], inspection, [native])
    core = app.state.core
    device, version = core.repository.get(imported["device_id"], Device)
    device.driver_instance_id = ""
    core.repository.save(device, expected_version=version)

    point_id = imported["points_added"][0]
    with pytest.raises(ValueError, match="Источник публикации не совпадает"):
        core.point_runtime.publish(point_id, 21.5, source_driver_id=driver["id"])
    with pytest.raises(ValueError, match="Quality source does not match"):
        core.point_runtime.mark_quality(
            point_id, "BAD_COMMUNICATION", source_driver_id=driver["id"])

    # Explicit trusted internal publication without an adapter identity remains
    # available to controlled Core services; field adapters must identify ownership.
    sample = core.point_runtime.publish(point_id, 21.5, source_driver_id=None)
    assert sample.value == 21.5 and sample.quality == "GOOD"
    core.close()


def test_point_runtime_rejects_driver_from_another_station_for_value_and_quality(tmp_path):
    from avic_core.domain.models import Device

    app, station_a, driver_a, inspection = _import_setup(tmp_path, "bacnet-ip")
    project_b = app.state.project_station.create_project("Second project")
    station_b = app.state.project_station.create_station(project_b["id"], "Second station")
    driver_b = app.state.driver_manager.create_instance(
        station_b["id"], "bacnet-ip", "Foreign station driver", {}
    )
    native = inspection["points"][0]["native_identity"]
    imported = app.state.protocol_point_import.import_points(
        station_a["id"], driver_a["id"], inspection, [native]
    )

    device, version = app.state.core.repository.get(imported["device_id"], Device)
    # Simulate corrupted or manually tampered ownership metadata: the device
    # now names a valid driver, but that driver belongs to another station.
    device.driver_instance_id = driver_b["id"]
    app.state.core.repository.save(device, expected_version=version)

    point_id = imported["points_added"][0]
    with pytest.raises(ValueError, match="принадлежат разным станциям"):
        app.state.core.point_runtime.publish(
            point_id, 22.0, source_driver_id=driver_b["id"]
        )
    with pytest.raises(ValueError, match="принадлежат разным станциям"):
        app.state.core.point_runtime.mark_quality(
            point_id, "BAD_COMMUNICATION", source_driver_id=driver_b["id"]
        )

    # The valid driver from station A is also rejected because it no longer
    # matches the Device owner; station separation is enforced independently.
    with pytest.raises(ValueError, match="Источник публикации не совпадает"):
        app.state.core.point_runtime.publish(
            point_id, 22.0, source_driver_id=driver_a["id"]
        )
    app.state.core.close()
