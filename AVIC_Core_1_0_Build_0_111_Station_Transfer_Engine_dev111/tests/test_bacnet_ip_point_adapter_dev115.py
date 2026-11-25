import pytest

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.ui import create_ui_app


class FakeBacnetClient:
    def __init__(self, values=None, fail_instances=()):
        self.values = values or {}
        self.fail_instances = set(fail_instances)
        self.calls = []

    def read_property(self, address, device_instance, object_type, object_instance,
                      property_id, array_index=None):
        self.calls.append((address, device_instance, object_type, object_instance, property_id, array_index))
        if object_instance in self.fail_instances:
            raise TimeoutError("simulated BACnet timeout")
        return self.values[object_instance]


def _setup(tmp_path, count=2):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("BACnet adapter tests")
    station = app.state.project_station.create_station(project["id"], "BACnet station")
    device = Device(name="BACnet device", station_id=station["id"], protocol="bacnet/ip",
                    address="192.0.2.40:47808", driver_instance_id="driver-bacnet-test")
    app.state.core.repository.save(device)
    points = []
    for i in range(count):
        point = Point(name=f"AI {i}", device_id=device.id, data_type="analog-input",
                      native_identity=f"bacnet:analog-input:{i}", source_ref=f"bacnet://ai/{i}",
                      value=None, quality=PointQuality.UNCERTAIN)
        app.state.core.repository.save(point)
        points.append(point)
    return app, points


def test_bacnet_adapter_reads_present_value_into_shared_runtime(tmp_path):
    app, points = _setup(tmp_path)
    client = FakeBacnetClient({1: 21.75, 2: 22.5})
    adapter = BacnetIpPointAdapter(client, app.state.core.point_runtime, "driver-bacnet-test", [
        BacnetIpPointBinding(points[0].id, ("192.0.2.40", 47808), 1234, 0, 1, scale=0.1),
        BacnetIpPointBinding(points[1].id, ("192.0.2.40", 47808), 1234, 0, 2, offset=1.0),
    ])
    result = adapter.poll_once()
    assert result["polled"] == 2
    assert [x["quality"] for x in result["results"]] == ["GOOD", "GOOD"]
    assert app.state.core.point_runtime.read(points[0].id).value == 2.175
    assert app.state.core.point_runtime.read(points[1].id).value == 23.5
    assert all(call[4] == 85 for call in client.calls)
    assert adapter.diagnostics()["write_supported"] is False
    app.state.core.close()


def test_bacnet_adapter_retains_last_value_and_marks_bad_communication(tmp_path):
    app, points = _setup(tmp_path, count=1)
    client = FakeBacnetClient({1: 20.0})
    binding = BacnetIpPointBinding(points[0].id, ("192.0.2.40", 47808), 1234, 0, 1)
    adapter = BacnetIpPointAdapter(client, app.state.core.point_runtime, "driver-bacnet-test", [binding])
    adapter.poll_once()
    before = app.state.core.point_runtime.read(points[0].id)
    client.fail_instances.add(1)
    result = adapter.poll_once()
    after = app.state.core.point_runtime.read(points[0].id)
    assert result["results"][0]["ok"] is False
    assert after.value == before.value == 20.0
    assert after.quality == "BAD_COMMUNICATION"
    assert after.timestamp == before.timestamp
    app.state.core.close()


def test_bacnet_adapter_rejects_wrong_driver_owner(tmp_path):
    app, points = _setup(tmp_path, count=1)
    client = FakeBacnetClient({1: 20.0})
    adapter = BacnetIpPointAdapter(
        client, app.state.core.point_runtime, "wrong-owner",
        [BacnetIpPointBinding(points[0].id, ("192.0.2.40", 47808), 1234, 0, 1)],
    )
    result = adapter.poll_once()
    assert result["results"][0]["ok"] is False
    assert "не совпадает" in result["results"][0]["error"]
    app.state.core.close()


def test_bacnet_binding_rejects_invalid_addresses_and_ids():
    with pytest.raises(ValueError):
        BacnetIpPointBinding("p", ("not-an-ip", 47808), 1234, 0, 1)
    with pytest.raises(ValueError):
        BacnetIpPointBinding("p", ("192.0.2.1", 47808), 4_194_304, 0, 1)
