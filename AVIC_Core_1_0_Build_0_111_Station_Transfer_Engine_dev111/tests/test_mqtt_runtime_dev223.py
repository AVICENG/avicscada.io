from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace

from avic_core.drivers.mqtt_adapter import MqttPointAdapter, MqttPointBinding
from avic_core.drivers.polling import EventDrivenSession


class FakePointRuntime:
    def __init__(self):
        self.samples = []
        self.qualities = []

    def publish(self, point_id, value, *, quality, timestamp, source_driver_id):
        sample = SimpleNamespace(timestamp=timestamp)
        self.samples.append((point_id, value, quality, source_driver_id))
        return sample

    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.qualities.append((point_id, quality, source_driver_id))


class FakeMqttClient:
    def __init__(self):
        self.subscriptions = []
        self.started = False
        self.disconnected = False

    def connect(self, host, port, keepalive):
        self.endpoint = (host, port, keepalive)

    def loop_start(self):
        self.started = True

    def loop_stop(self):
        self.started = False

    def disconnect(self):
        self.disconnected = True

    def subscribe(self, topic, qos):
        self.subscriptions.append((topic, qos))
        return (0, len(self.subscriptions))


def test_mqtt_adapter_subscribes_once_per_topic_with_highest_qos():
    client = FakeMqttClient()
    runtime = FakePointRuntime()
    adapter = MqttPointAdapter(
        client, runtime, "driver-1",
        [
            MqttPointBinding("point-a", "plant/ahu/temperature", qos=0),
            MqttPointBinding("point-b", "plant/ahu/temperature", qos=2),
        ],
        host="broker.local",
    )
    adapter.start()
    adapter._on_connect(client, None, {}, 0)
    assert client.endpoint == ("broker.local", 1883, 60)
    assert client.subscriptions == [("plant/ahu/temperature", 2)]
    assert adapter.diagnostics()["connected"] is True
    adapter.stop()
    assert client.disconnected is True
    assert runtime.qualities


def test_mqtt_adapter_decodes_json_path_and_applies_numeric_scaling():
    client = FakeMqttClient()
    runtime = FakePointRuntime()
    adapter = MqttPointAdapter(
        client, runtime, "driver-2",
        [MqttPointBinding("point-temp", "site/ahu", value_path="sensors.temp", scale=1.8, offset=32)],
        host="broker.local",
    )
    adapter._on_connect(client, None, {}, 0)
    adapter._on_message(client, None, SimpleNamespace(
        topic="site/ahu", payload=b'{"sensors":{"temp":20}}'))
    assert len(runtime.samples) == 1
    point_id, value, quality, source = runtime.samples[0]
    assert (point_id, value, source) == ("point-temp", 68.0, "driver-2")
    assert quality.value == "GOOD"


def test_mqtt_adapter_marks_bad_configuration_for_invalid_payload():
    client = FakeMqttClient()
    runtime = FakePointRuntime()
    adapter = MqttPointAdapter(
        client, runtime, "driver-3",
        [MqttPointBinding("point-temp", "site/ahu")], host="broker.local",
    )
    adapter._on_message(client, None, SimpleNamespace(topic="site/ahu", payload=b"not-json"))
    assert runtime.qualities
    assert runtime.qualities[-1][0] == "point-temp"
    assert adapter.diagnostics()["failure_count"] == 1


def test_event_driven_session_reports_disconnected_adapter_as_degraded():
    class Adapter:
        def __init__(self):
            self.started = False
            self.connected = False

        def start(self):
            self.started = True

        def stop(self):
            self.started = False

        def diagnostics(self):
            return {"connected": self.connected}

    adapter = Adapter()
    session = EventDrivenSession(adapter)
    session.start()
    assert session.diagnostics()["state"] == "DEGRADED"
    assert session.diagnostics()["event_driven"] is True
    adapter.connected = True
    assert session.diagnostics()["state"] == "RUNNING"
    session.stop()
    assert session.diagnostics()["state"] == "STOPPED"
