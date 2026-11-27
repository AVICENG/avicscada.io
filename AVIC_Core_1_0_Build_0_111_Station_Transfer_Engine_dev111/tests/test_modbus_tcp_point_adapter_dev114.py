from avic_core.domain.models import Device, Point, PointQuality
from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.ui import create_ui_app


class FakeModbusClient:
    def __init__(self, values=None, fail_addresses=()):
        self.values, self.fail_addresses, self.calls = values or {}, set(fail_addresses), []
    def _read(self, fn, addr, count):
        self.calls.append((fn, addr, count))
        if addr in self.fail_addresses: raise TimeoutError("simulated timeout")
        v = self.values[addr]
        return v if isinstance(v, list) else [v]
    def read_coils(self, address, count=1): return self._read(1, address, count)
    def read_discrete_inputs(self, address, count=1): return self._read(2, address, count)
    def read_holding_registers(self, address, count=1): return self._read(3, address, count)
    def read_input_registers(self, address, count=1): return self._read(4, address, count)


def _setup(tmp_path, count=2):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV115")
    station = app.state.project_station.create_station(project["id"], "Modbus tests")
    driver = app.state.core.driver_manager.create_instance(
        station["id"], "modbus-tcp", "Modbus adapter test", {})
    device = Device(name="Modbus device", station_id=station["id"], protocol="modbus/tcp",
                    address="192.0.2.20", driver_instance_id=driver["id"])
    app.state.core.repository.save(device)
    points = []
    for i in range(count):
        p = Point(name=f"Input {i}", device_id=device.id, data_type="analog-input",
                  native_identity=f"modbus:hr:{i}", source_ref=f"modbus://hr/{i}",
                  value=None, quality=PointQuality.UNCERTAIN)
        app.state.core.repository.save(p); points.append(p)
    return app, points


def _driver_id(app):
    rows = app.state.core.repository.list_records(entity_type="DriverInstance")
    assert len(rows) == 1
    return rows[0]["entity_id"]


def test_modbus_adapter_publishes_scaled_values_into_runtime(tmp_path):
    app, pts = _setup(tmp_path)
    client = FakeModbusClient({0: [2345], 1: [1987]})
    adapter = ModbusTcpPointAdapter(client, app.state.core.point_runtime, _driver_id(app), [
        ModbusTcpPointBinding(pts[0].id, 3, 0, data_type="uint16", scale=0.1),
        ModbusTcpPointBinding(pts[1].id, 4, 1, data_type="uint16", offset=1.0)])
    result = adapter.poll_once()
    assert result["polled"] == 2
    assert [x["quality"] for x in result["results"]] == ["GOOD", "GOOD"]
    assert app.state.core.point_runtime.read(pts[0].id).value == 234.5
    assert app.state.core.point_runtime.read(pts[1].id).value == 1988.0
    assert all(c[0] in (3, 4) for c in client.calls)
    app.state.core.close()


def test_modbus_adapter_retains_value_and_marks_communication_failure(tmp_path):
    app, pts = _setup(tmp_path, 1)
    client = FakeModbusClient({0: [2150]})
    adapter = ModbusTcpPointAdapter(client, app.state.core.point_runtime, _driver_id(app),
        [ModbusTcpPointBinding(pts[0].id, 3, 0, data_type="uint16", scale=0.1)])
    adapter.poll_once(); before = app.state.core.point_runtime.read(pts[0].id)
    client.fail_addresses.add(0); result = adapter.poll_once()
    after = app.state.core.point_runtime.read(pts[0].id)
    assert not result["results"][0]["ok"]
    assert after.value == before.value == 215.0
    assert after.quality == "BAD_COMMUNICATION" and after.timestamp == before.timestamp
    app.state.core.close()


def test_modbus_binding_refuses_write_functions_and_invalid_ranges():
    import pytest
    with pytest.raises(ValueError): ModbusTcpPointBinding("p", 5, 0)
    with pytest.raises(ValueError): ModbusTcpPointBinding("p", 3, 65535, 2, "uint32")
    with pytest.raises(ValueError): ModbusTcpPointBinding("p", 1, 0, 2, "bool")


def test_modbus_adapter_checks_driver_ownership(tmp_path):
    app, pts = _setup(tmp_path, 1)
    adapter = ModbusTcpPointAdapter(FakeModbusClient({0:[10]}), app.state.core.point_runtime,
        "wrong-owner", [ModbusTcpPointBinding(pts[0].id, 3, 0)])
    result = adapter.poll_once()
    assert not result["results"][0]["ok"]
    assert "does not match" in result["results"][0]["error"] or "не совпадает" in result["results"][0]["error"]
    app.state.core.close()


def test_modbus_adapter_coalesces_adjacent_register_bindings(tmp_path):
    app, pts = _setup(tmp_path, 2)
    client = FakeModbusClient({0: [100, 200]})
    adapter = ModbusTcpPointAdapter(client, app.state.core.point_runtime, _driver_id(app), [
        ModbusTcpPointBinding(pts[0].id, 3, 0, data_type="uint16"),
        ModbusTcpPointBinding(pts[1].id, 3, 1, data_type="uint16"),
    ])
    result = adapter.poll_once()
    assert result["group_count"] == 1
    assert client.calls == [(3, 0, 2)]
    assert [app.state.core.point_runtime.read(point.id).value for point in pts] == [100, 200]
    app.state.core.close()
