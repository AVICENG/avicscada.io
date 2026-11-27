from __future__ import annotations

from types import SimpleNamespace

import pytest

from avic_core.drivers import rust_point_adapter as module


class FakeWorker:
    def __init__(self, *args, **kwargs):
        self.requests = []
        self.config = None
        self.closed = False
    def start(self, config):
        self.config = config
    def read(self, request):
        self.requests.append(request)
        protocol = request["protocol"]
        if protocol == "modbus-tcp":
            return {"result": {"values": [100]}}
        if protocol == "bacnet-ip":
            return {"result": {
                "device": {"device_instance": request["device_instance"]},
                "objects": [{
                    "object_type_name": "AnalogInput", "object_instance": 2,
                    "present_value": 21.5, "status_flags": [False, False, False, False],
                }],
            }}
        if protocol == "knxnet-ip":
            return {"result": {"value": 22.25}}
        raise AssertionError(protocol)
    def diagnostics(self):
        return {"process_alive": True}
    def close(self):
        self.closed = True


class FakeRuntime:
    def __init__(self):
        self.published = []
        self.bad = []
    def publish(self, point_id, value, *, quality, source_driver_id):
        self.published.append((point_id, value, quality, source_driver_id))
        return SimpleNamespace(value=value, quality=quality)
    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.bad.append((point_id, quality, source_driver_id))
        return SimpleNamespace(value=None, quality=quality)


class FakeCore:
    def __init__(self):
        self.point_runtime = FakeRuntime()


@pytest.fixture
def fake_worker(monkeypatch):
    worker = FakeWorker()
    monkeypatch.setattr(module, "RustDriverWorker", lambda *a, **kw: worker)
    return worker


def make_adapter(core, protocol, config, bindings):
    return module.RustDriverPointAdapter(
        worker_command=["C:/fake/avic-driver-worker.exe"], core=core,
        driver_instance_id="00000000-0000-0000-0000-000000000001",
        protocol=protocol, config=config, bindings=bindings,
        installation_id="install-1", project_id="project-1", station_id="station-1",
    )


def test_rust_modbus_worker_decodes_and_publishes_through_point_runtime(fake_worker):
    core = FakeCore()
    adapter = make_adapter(core, "modbus-tcp",
        {"host": "192.0.2.10", "port": 502, "unit_id": 1, "timeout": 2.0},
        [{"point_id": "point-1", "function": 3, "address": 100,
          "count": 1, "data_type": "uint16", "scale": 0.1, "offset": 0.0}],
    )
    result = adapter.poll_once()
    assert result["success_count"] == 1
    assert core.point_runtime.published[0][0:2] == ("point-1", 10.0)
    assert fake_worker.requests[0]["function"] == 3


def test_rust_bacnet_batches_by_device_and_maps_object_identity(fake_worker):
    core = FakeCore()
    adapter = make_adapter(core, "bacnet-ip",
        {"timeout": 3.0, "local_address": "192.0.2.10", "udp_port": 47808},
        [
            {"point_id": "point-1", "address": ("192.0.2.20", 47808),
             "device_instance": 1234, "object_type": 0, "object_instance": 2,
             "property_id": 85, "array_index": None, "scale": 1.0, "offset": 0.0},
            {"point_id": "point-2", "address": ("192.0.2.20", 47808),
             "device_instance": 1234, "object_type": 0, "object_instance": 2,
             "property_id": 85, "array_index": None, "scale": 2.0, "offset": 1.0},
        ],
    )
    result = adapter.poll_once()
    assert result["success_count"] == 2
    assert len(fake_worker.requests) == 1
    assert [row[1] for row in core.point_runtime.published] == [21.5, 44.0]


def test_rust_knx_maps_group_address_and_dpt(fake_worker):
    core = FakeCore()
    adapter = make_adapter(core, "knxnet-ip",
        {"gateway_host": "192.0.2.30", "gateway_port": 3671,
         "local_host": "192.0.2.31", "local_port": 0, "timeout": 1.0},
        [{"point_id": "point-1", "group_address": 0x0A03, "datapoint_type": "9.001"}],
    )
    result = adapter.poll_once()
    assert result["success_count"] == 1
    assert fake_worker.requests[0]["group_address"] == "1/2/3"
    assert fake_worker.requests[0]["dpt"] == "9.001"
    assert core.point_runtime.published[0][1] == 22.25


def test_rust_bacnet_rejects_unsupported_property_before_publish(fake_worker):
    core = FakeCore()
    adapter = make_adapter(core, "bacnet-ip",
        {"timeout": 3.0, "local_address": "192.0.2.10", "udp_port": 47808},
        [{"point_id": "point-1", "address": ("192.0.2.20", 47808),
          "device_instance": 1234, "object_type": 0, "object_instance": 2,
          "property_id": 77, "array_index": None, "scale": 1.0, "offset": 0.0}],
    )
    result = adapter.poll_once()
    assert result["failure_count"] == 1
    assert core.point_runtime.published == []
    assert core.point_runtime.bad[0][0] == "point-1"


def test_rust_bacnet_status_fault_is_published_with_bad_quality(fake_worker):
    from avic_core.domain.models import PointQuality
    fake_worker.read = lambda request: {"result": {
        "device": {"device_instance": request["device_instance"]},
        "objects": [{
            "object_type_name": "AnalogInput", "object_instance": 2,
            "present_value": 21.5, "status_flags": [False, True, False, False],
        }],
    }}
    core = FakeCore()
    adapter = make_adapter(core, "bacnet-ip",
        {"timeout": 3.0, "local_address": "192.0.2.10", "udp_port": 47808},
        [{"point_id": "point-1", "address": ("192.0.2.20", 47808),
          "device_instance": 1234, "object_type": 0, "object_instance": 2,
          "property_id": 85, "array_index": None, "scale": 1.0, "offset": 0.0}],
    )
    adapter.poll_once()
    assert core.point_runtime.published[0][2] == PointQuality.BAD_COMMUNICATION
