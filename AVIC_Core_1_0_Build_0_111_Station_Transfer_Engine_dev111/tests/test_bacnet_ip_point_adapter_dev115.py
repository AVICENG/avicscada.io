from avic_core.domain.models import Device, Point, PointQuality
from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.ui import create_ui_app


class FakeBacnetClient:
    def __init__(self, values=None, fail_instances=()):
        self.values, self.fail_instances, self.calls = values or {}, set(fail_instances), []
    def read_property(self, address, device_instance, object_type, object_instance, property_id, array_index=None):
        self.calls.append((address, device_instance, object_type, object_instance, property_id, array_index))
        if object_instance in self.fail_instances: raise TimeoutError("simulated BACnet timeout")
        return self.values[object_instance]


def _setup(tmp_path, count=2):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("BACnet adapter tests")
    station = app.state.project_station.create_station(project["id"], "BACnet station")
    driver = app.state.driver_manager.create_instance(station["id"], "bacnet-ip", "BACnet test driver", {})
    device = Device(name="BACnet device", station_id=station["id"], protocol="bacnet/ip",
                    address="192.0.2.40:47808", driver_instance_id=driver["id"])
    app.state.core.repository.save(device)
    points = []
    for i in range(count):
        p = Point(name=f"AI {i}", device_id=device.id, data_type="analog-input",
                  native_identity=f"bacnet:ai:{i}", source_ref=f"bacnet://ai/{i}",
                  value=None, quality=PointQuality.UNCERTAIN)
        app.state.core.repository.save(p); points.append(p)
    return app, points, driver["id"]


def test_bacnet_adapter_reads_present_value_into_shared_runtime(tmp_path):
    app, pts, driver_id = _setup(tmp_path)
    client = FakeBacnetClient({1: 21.75, 2: 22.5})
    adapter = BacnetIpPointAdapter(client, app.state.core.point_runtime, driver_id, [
        BacnetIpPointBinding(pts[0].id, ("192.0.2.40", 47808), 1234, 0, 1, scale=0.1),
        BacnetIpPointBinding(pts[1].id, ("192.0.2.40", 47808), 1234, 0, 2, offset=1.0)])
    result = adapter.poll_once()
    assert result["polled"] == 2
    assert [x["quality"] for x in result["results"]] == ["GOOD", "GOOD"]
    import pytest
    assert app.state.core.point_runtime.read(pts[0].id).value == pytest.approx(2.175, rel=1e-12)
    assert app.state.core.point_runtime.read(pts[1].id).value == 23.5
    assert all(c[4] == 85 for c in client.calls)
    app.state.core.close()


def test_bacnet_adapter_retains_last_value_and_marks_communication_failure(tmp_path):
    app, pts, driver_id = _setup(tmp_path, 1)
    client = FakeBacnetClient({1: 20.0})
    binding = BacnetIpPointBinding(pts[0].id, ("192.0.2.40", 47808), 1234, 0, 1)
    adapter = BacnetIpPointAdapter(client, app.state.core.point_runtime, driver_id, [binding])
    adapter.poll_once(); before = app.state.core.point_runtime.read(pts[0].id)
    client.fail_instances.add(1); result = adapter.poll_once()
    after = app.state.core.point_runtime.read(pts[0].id)
    assert not result["results"][0]["ok"]
    assert after.value == before.value == 20.0
    assert after.quality == "BAD_COMMUNICATION" and after.timestamp == before.timestamp
    app.state.core.close()


def test_bacnet_adapter_checks_driver_ownership(tmp_path):
    app, pts, driver_id = _setup(tmp_path, 1)
    adapter = BacnetIpPointAdapter(FakeBacnetClient({1: 20.0}), app.state.core.point_runtime,
        "wrong-owner", [BacnetIpPointBinding(pts[0].id, ("192.0.2.40", 47808), 1234, 0, 1)])
    result = adapter.poll_once()
    assert not result["results"][0]["ok"]
    assert "does not match" in result["results"][0]["error"] or "не совпадает" in result["results"][0]["error"]
    app.state.core.close()


def test_bacnet_binding_rejects_bad_address_and_identifiers():
    import pytest
    with pytest.raises(ValueError): BacnetIpPointBinding("p", ("bad", 47808), 1, 0, 1)
    with pytest.raises(ValueError): BacnetIpPointBinding("p", ("192.0.2.1", 47808), 4_194_304, 0, 1)
