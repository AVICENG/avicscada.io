import json
from types import SimpleNamespace

import pytest

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.drivers.manager import DriverInstance
from avic_core.drivers.mqtt_adapter import MqttPointAdapter, MqttPointBinding
from avic_core.ui import create_ui_app


class FakeMqttClient:
    def __init__(self):
        self.subscriptions = []
        self.connected_to = None
        self.started = False
        self.disconnected = False
    def connect(self, host, port, keepalive):
        self.connected_to = (host, port, keepalive)
    def loop_start(self):
        self.started = True
    def loop_stop(self):
        self.started = False
    def disconnect(self):
        self.disconnected = True
    def subscribe(self, topic, qos=0):
        self.subscriptions.append((topic, qos))
        return (0, len(self.subscriptions))


def _setup(tmp_path, count=1):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("MQTT adapter tests")
    station = app.state.project_station.create_station(project["id"], "MQTT station")
    # MQTT remains planned for production Driver Manager lifecycle. This adapter-level
    # test persists an explicit station-owned identity without claiming production start.
    driver = DriverInstance(name="MQTT adapter test", station_id=station["id"],
                            driver_id="mqtt", protocol="MQTT")
    app.state.core.repository.save(driver)
    device = Device(name="MQTT device", station_id=station["id"], protocol="mqtt",
                    address="mqtt://broker.example:1883", driver_instance_id=driver.id)
    app.state.core.repository.save(device)
    points = []
    for i in range(count):
        p = Point(name=f"MQTT {i}", device_id=device.id, data_type="analog-input",
                  native_identity=f"mqtt:sensor/{i}", source_ref=f"mqtt://sensor/{i}",
                  value=None, quality=PointQuality.UNCERTAIN)
        app.state.core.repository.save(p)
        points.append(p)
    return app, points


def _driver_id(app):
    rows = app.state.core.repository.list_records(entity_type="DriverInstance")
    assert len(rows) == 1
    return rows[0]["entity_id"]


def test_mqtt_subscribes_and_publishes_json_value_to_point_runtime(tmp_path):
    app, points = _setup(tmp_path)
    client = FakeMqttClient()
    adapter = MqttPointAdapter(client, app.state.core.point_runtime, _driver_id(app),
        [MqttPointBinding(points[0].id, "site/ahu1/supply", qos=1, value_path="telemetry.temp", scale=1.8, offset=32)],
        host="broker.example", port=8883)
    adapter.start()
    client.on_connect(client, None, {}, 0, None)
    assert client.subscriptions == [("site/ahu1/supply", 1)]
    client.on_message(client, None, SimpleNamespace(topic="site/ahu1/supply",
        payload=json.dumps({"telemetry": {"temp": 20}}).encode()))
    value = app.state.core.point_runtime.read(points[0].id)
    assert value.value == pytest.approx(68.0)
    assert value.quality == "GOOD"
    assert adapter.diagnostics()["connected"] is True
    adapter.stop()
    assert client.disconnected is True
    app.state.core.close()


def test_mqtt_disconnect_preserves_last_value_and_marks_bad_communication(tmp_path):
    app, points = _setup(tmp_path)
    client = FakeMqttClient()
    adapter = MqttPointAdapter(client, app.state.core.point_runtime, _driver_id(app),
        [MqttPointBinding(points[0].id, "sensor/temp")], host="broker.example")
    adapter._on_connect(client, None, {}, 0)
    client.on_message(client, None, SimpleNamespace(topic="sensor/temp", payload=b'{"value": 21.5}'))
    before = app.state.core.point_runtime.read(points[0].id)
    client.on_disconnect(client, None, None, 1, None)
    after = app.state.core.point_runtime.read(points[0].id)
    assert after.value == before.value == 21.5
    assert after.timestamp == before.timestamp
    assert after.quality == "BAD_COMMUNICATION"
    app.state.core.close()


def test_mqtt_invalid_json_marks_bad_configuration(tmp_path):
    app, points = _setup(tmp_path)
    client = FakeMqttClient()
    adapter = MqttPointAdapter(client, app.state.core.point_runtime, _driver_id(app),
        [MqttPointBinding(points[0].id, "sensor/temp")], host="broker.example")
    adapter._on_message(client, None, SimpleNamespace(topic="sensor/temp", payload=b"{bad"))
    assert app.state.core.point_runtime.read(points[0].id).quality == "BAD_CONFIGURATION"
    app.state.core.close()


def test_mqtt_rejects_unsafe_or_invalid_bindings():
    with pytest.raises(ValueError):
        MqttPointBinding("p", "", payload_format="json")
    with pytest.raises(ValueError):
        MqttPointBinding("p", "sensor", qos=3)
    with pytest.raises(ValueError):
        MqttPointBinding("p", "sensor", scale=float("nan"))
