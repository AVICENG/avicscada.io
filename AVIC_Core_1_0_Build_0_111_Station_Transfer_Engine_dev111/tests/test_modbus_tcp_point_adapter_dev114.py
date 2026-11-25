from datetime import datetime, timezone

import pytest

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.ui import create_ui_app


class FakeModbusClient:
    def __init__(self, values=None, fail_addresses=()):
        self.values = values or {}
        self.fail_addresses = set(fail_addresses)
        self.calls = []

    def _read(self, function, address, count):
        self.calls.append((function, address, count))
        if address in self.fail_addresses:
            raise TimeoutError("simulated timeout")
        value = self.values[address]
        return value if isinstance(value, list) else [value]

    def read_coils(self, address, count=1):
        return self._read(1, address, count)

    def read_discrete_inputs(self, address, count=1):
        return self._read(2, address, count)

    def read_holding_registers(self, address, count=1):
        return self._read(3, address, count)

    def read_input_registers(self, address, count=1):
        return self._read(4, address, count)


def _setup(tmp_path, count=2):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV114")
    station = app.state.project_station.create_station(project["id"], "Driver tests")
    device = Device(name="Modbus test device", station_id=station["id"],
                    protocol="modbus/tcp", address="192.0.2.20",
                    driver_instance_id="driver-modbus-test")
    app.state.core.repository.save(device)
    points = []
    for i in range(count):
        point = Point(name=f"Input {i}", device_id=device.id, data_type="analog-input",
                      native_identity=f"modbus:holding-register:{i}", source_ref=f"modbus://hr/{i}",
                      value=None, quality=PointQuality.UNCERTAIN)
        app.state.core.repository.save(point)
        points.append(point)
    return app, points


def test_modbus_adapter_publishes_live_values_into_shared_runtime(tmp_path):
    app, points = _setup(tmp_path)
    client = FakeModbusClient({0: [2345], 1: [1987]})
    adapter = ModbusTcpPointAdapter(
        client, app.state.core.point_runtime, "driver-modbus-test",
        [ModbusTcpPointBinding(points[0].id, 3, 0, data_type="uint16", scale=0.1),
         ModbusTcpPointBinding(points[1].id, 4, 1, data_type="uint16", offset=1.0)],
    )
    result = adapter.poll_once()
    assert result["polled"] == 2
    assert [x["quality"] for x in result["results"]] == ["GOOD", "GOOD"]
    assert app.state.core.point_runtime.read(points[0].id).value == 234.5
    assert app.state.core.point_runtime.read(points[1].id).value == 1988.0
    assert adapter.diagnostics()["success_count"] == 2
    assert all(call[0] in (3, 4) for call in client.calls)
    app.state.core.close()


def test_modbus_adapter_retains_last_value_and_marks_bad_communication(tmp_path):
    app, points = _setup(tmp_path, count=1)
    client = FakeModbusClient({0: [2150]})
    binding = ModbusTcpPointBinding(points[0].id, 3, 0, data_type="uint16", scale=0.1)
    adapter = ModbusTcpPointAdapter(client, app.state.core.point_runtime, "driver-modbus-test", [binding])
    adapter.poll_once()
    last_good = app.state.core.point_runtime.read(points[0].id)
    client.fail_addresses.add(0)
    result = adapter.poll_once()
    live = app.state.core.point_runtime.read(points[0].id)
    assert result["results"][0]["ok"] is False
    assert live.value == last_good.value == 215.0
    assert live.quality == "BAD_COMMUNICATION"
    assert live.timestamp == last_good.timestamp
    assert adapter.diagnostics()["failure_count"] == 1
    app.state.core.close()


def test_modbus_adapter_rejects_wrong_driver_owner(tmp_path):
    app, points = _setup(tmp_path, count=1)
    client = FakeModbusClient({0: [10]})
    adapter = ModbusTcpPointAdapter(
        client, app.state.core.point_runtime, "not-the-owner",
        [ModbusTcpPointBinding(points[0].id, 3, 0)],
    )
    result = adapter.poll_once()
    assert result["results"][0]["ok"] is False
    assert "не совпадает" in result["results"][0]["error"]
    app.state.core.close()


def test_modbus_binding_validation_blocks_write_functions_and_bad_ranges():
    with pytest.raises(ValueError):
        ModbusTcpPointBinding("point", 5, 0)  # write-single-coil
    with pytest.raises(ValueError):
        ModbusTcpPointBinding("point", 3, 65535, count=2, data_type="uint32")
    with pytest.raises(ValueError):
        ModbusTcpPointBinding("point", 1, 0, count=2, data_type="bool")
