import pytest
from fastapi.testclient import TestClient
from avic_core.application.container import CoreApplication
from avic_core.ui.project_station import ProjectStationService
from avic_core.drivers import DriverManagerService


def make_station(tmp_path):
    core=CoreApplication(tmp_path)
    ps=ProjectStationService(core)
    project=ps.create_project('Project')
    station=ps.create_station(project['id'],'Station')
    return core,station


def test_driver_catalog_is_read_only_and_explicit_about_capabilities(tmp_path):
    core,station=make_station(tmp_path)
    catalog=DriverManagerService(core).catalog()
    assert {x['driver_id'] for x in catalog} >= {'bacnet-ip','modbus-tcp'}
    assert all(x['write_supported'] is False for x in catalog)


def test_create_driver_instance_persists_stopped_inventory(tmp_path):
    core,station=make_station(tmp_path); svc=DriverManagerService(core)
    created=svc.create_instance(station['id'],'bacnet-ip','BACnet LAN',{'interface_id':'eth0'})
    assert created['state']=='STOPPED' and created['enabled'] is False
    assert created['field_io_enabled'] is False
    rows=svc.list_instances(station['id'])
    assert rows[0]['id']==created['id'] and rows[0]['config']=={'interface_id':'eth0'}
    assert svc.get_instance(created['id'])['start_supported'] is True


def test_unknown_driver_cannot_be_instantiated(tmp_path):
    core,station=make_station(tmp_path)
    with pytest.raises(ValueError,match='доверенном'):
        DriverManagerService(core).create_instance(station['id'],'not-installed','Fake')


def test_driver_config_rejects_secrets(tmp_path):
    core,station=make_station(tmp_path)
    with pytest.raises(ValueError,match='SecretStore'):
        DriverManagerService(core).create_instance(station['id'],'bacnet-ip','Unsafe',{'password':'x'})


def test_driver_instance_cannot_be_created_enabled(tmp_path):
    from avic_core.drivers.manager import DriverInstance
    import uuid
    with pytest.raises(ValueError,match='enabled не соответствует состоянию'):
        DriverInstance('x',str(uuid.uuid4()),'bacnet-ip','BACnet/IP',enabled=True)


def test_driver_manager_http_routes_and_local_mutation_guard(tmp_path):
    from avic_core.ui.app import create_ui_app
    app=create_ui_app(data_dir=str(tmp_path/'api'))
    client=TestClient(app)
    assert client.get('/api/drivers/catalog').status_code==200
    project=client.post('/api/projects',json={'name':'P'}).json()
    station=client.post('/api/stations',json={'name':'S','project_id':project['id']}).json()
    r=client.post(f"/api/stations/{station['id']}/drivers",json={'driver_id':'bacnet-ip','name':'LAN'})
    assert r.status_code==201 and r.json()['state']=='STOPPED'
    assert client.get(f"/api/stations/{station['id']}/drivers").json()['instances'][0]['name']=='LAN'
    denied=client.post(f"/api/stations/{station['id']}/drivers",json={'driver_id':'bacnet-ip','name':'Remote'},headers={'origin':'https://evil.example'})
    assert denied.status_code==403


def test_driver_manager_explicit_runtime_factory_lifecycle(tmp_path):
    from avic_core.drivers.manager import DriverInstance
    from datetime import datetime, timezone
    import time

    class Adapter:
        def __init__(self):
            self.calls = 0
            self.closed = False
        def poll_once(self):
            self.calls += 1
            return {"results": [{"ok": True}]}
        def diagnostics(self):
            return {"calls": self.calls}
        def close(self):
            self.closed = True

    core, station = make_station(tmp_path)
    service = core.driver_manager
    created = service.create_instance(station["id"], "modbus-tcp", "Test Modbus", {"poll_interval_seconds": 0.1})
    adapter = Adapter()
    service.register_adapter_factory("modbus-tcp", lambda _core, _instance: adapter)
    started = service.start_instance(created["id"])
    assert started["state"] == "RUNNING"
    deadline = time.monotonic() + 2
    while adapter.calls < 1 and time.monotonic() < deadline:
        time.sleep(0.01)
    assert adapter.calls >= 1
    persisted, _ = core.repository.get(created["id"], DriverInstance)
    assert persisted.state == "RUNNING" and persisted.enabled is True
    stopped = service.stop_instance(created["id"])
    assert stopped["state"] == "STOPPED"
    assert adapter.closed is True
    persisted, _ = core.repository.get(created["id"], DriverInstance)
    assert persisted.state == "STOPPED" and persisted.enabled is False
    core.close()


def test_driver_manager_rejects_nested_secrets(tmp_path):
    core, station = make_station(tmp_path)
    with pytest.raises(ValueError, match="SecretStore"):
        core.driver_manager.create_instance(station["id"], "modbus-tcp", "Unsafe",
            {"bindings": [{"point_id": "x", "password": "hidden"}]})
    core.close()


def test_driver_manager_requires_registered_runtime_for_mqtt(tmp_path):
    core, station = make_station(tmp_path)
    with pytest.raises(ValueError, match="пока не реализован"):
        core.driver_manager.create_instance(station["id"], "mqtt", "MQTT")
    assert next(x for x in core.driver_manager.catalog() if x["driver_id"] == "mqtt")["runtime_start_supported"] is False
    core.close()


def test_core_shutdown_stops_active_driver_session(tmp_path):
    import time
    from avic_core.drivers.manager import DriverInstance

    class Adapter:
        def __init__(self):
            self.closed = False
        def poll_once(self):
            return {"results": [{"ok": True}]}
        def close(self):
            self.closed = True

    core, station = make_station(tmp_path)
    service = core.driver_manager
    created = service.create_instance(station["id"], "modbus-tcp", "Shutdown test",
                                      {"poll_interval_seconds": 0.1})
    adapter = Adapter()
    service.register_adapter_factory("modbus-tcp", lambda _core, _instance: adapter)
    service.start_instance(created["id"])
    core.close()
    assert adapter.closed is True
    persisted, _ = core.repository.get(created["id"], DriverInstance)
    assert persisted.state == "STOPPED" and persisted.enabled is False


def test_driver_runtime_state_and_station_stop_are_truthful(tmp_path):
    import time
    from avic_core.drivers.manager import DriverInstance

    class DegradedAdapter:
        def poll_once(self):
            return {"results": [{"ok": False, "error": "simulated link loss"}]}
        def close(self):
            self.closed = True

    core, station = make_station(tmp_path)
    adapter = DegradedAdapter()
    adapter.closed = False
    created = core.driver_manager.create_instance(station["id"], "modbus-tcp", "Degraded test",
                                                   {"poll_interval_seconds": 0.1})
    core.driver_manager.register_adapter_factory("modbus-tcp", lambda _core, _instance: adapter)
    core.driver_manager.start_instance(created["id"])
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        state = core.driver_manager.diagnostics(created["id"])["state"]
        if state == "DEGRADED":
            break
        time.sleep(0.01)
    assert core.driver_manager.diagnostics(created["id"])["state"] == "DEGRADED"
    view = core.driver_manager.get_instance(created["id"])
    assert view["state"] == "DEGRADED"
    assert view["field_read_enabled"] is True
    assert view["field_write_enabled"] is False
    core.stop_station(station["id"])
    assert adapter.closed is True
    persisted, _ = core.repository.get(created["id"], DriverInstance)
    assert persisted.state == "STOPPED" and persisted.enabled is False
    core.close()


def test_persisted_active_driver_without_worker_is_reported_orphaned(tmp_path):
    import uuid
    from avic_core.drivers.manager import DriverInstance
    core, station = make_station(tmp_path)
    item = DriverInstance("Orphan", station["id"], "modbus-tcp", "Modbus TCP",
                          state="RUNNING", enabled=True)
    core.repository.save(item)
    assert core.driver_manager.diagnostics(item.id)["state"] == "ORPHANED"
    assert core.driver_manager.get_instance(item.id)["field_read_enabled"] is False
    core.close()


def test_factory_registration_is_blocked_only_for_same_active_driver(tmp_path):
    import time
    core, station = make_station(tmp_path)
    created = core.driver_manager.create_instance(station["id"], "modbus-tcp", "Active Modbus",
                                                   {"poll_interval_seconds": 0.1})
    class Adapter:
        def poll_once(self): return {"results": []}
        def close(self): pass
    core.driver_manager.register_adapter_factory("modbus-tcp", lambda _core, _instance: Adapter())
    core.driver_manager.start_instance(created["id"])
    # Updating a different protocol factory must not be blocked by this Modbus worker.
    core.driver_manager.register_adapter_factory("bacnet-ip", lambda _core, _instance: Adapter())
    with pytest.raises(RuntimeError, match="активной сессии"):
        core.driver_manager.register_adapter_factory("modbus-tcp", lambda _core, _instance: Adapter())
    core.driver_manager.stop_station(station["id"])
    core.close()


def test_driver_config_rejects_secret_aliases_recursively(tmp_path):
    core, station = make_station(tmp_path)
    secret_configs = [
        {"api_key": "x"},
        {"mqtt_password": "x"},
        {"nested": {"oauth_refresh_token": "x"}},
        {"tls_private_key": "x"},
        {"clientKey": "x"},
    ]
    for config in secret_configs:
        with pytest.raises(ValueError, match="SecretStore"):
            core.driver_manager.create_instance(station["id"], "modbus-tcp", "Secret alias", config)
    core.close()
