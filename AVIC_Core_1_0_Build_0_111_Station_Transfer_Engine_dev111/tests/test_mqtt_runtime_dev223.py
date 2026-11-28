from __future__ import annotations

import pytest

from types import ModuleType, SimpleNamespace
from uuid import uuid4

from avic_core.drivers.mqtt_adapter import MqttPointAdapter, MqttPointBinding
from avic_core.drivers.polling import EventDrivenSession
from avic_core.drivers.manager import DriverManagerService, DriverInstance


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

    def tls_set(self, ca_certs):
        self.ca_certs = ca_certs

    def tls_insecure_set(self, value):
        self.tls_insecure = value


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


def test_driver_manager_builds_mqtt_runtime_with_optional_paho_and_verified_tls(tmp_path, monkeypatch):
    ca_file = tmp_path / "broker-ca.pem"
    ca_file.write_text("test CA placeholder", encoding="utf-8")
    client = FakeMqttClient()
    module = ModuleType("paho.mqtt.client")
    module.MQTTv311 = 4
    module.MQTTv5 = 5
    module.CallbackAPIVersion = SimpleNamespace(VERSION2=2)
    module.Client = lambda **kwargs: client
    paho = ModuleType("paho")
    paho.__path__ = []
    mqtt_package = ModuleType("paho.mqtt")
    mqtt_package.__path__ = []
    mqtt_package.client = module
    monkeypatch.setitem(__import__("sys").modules, "paho", paho)
    monkeypatch.setitem(__import__("sys").modules, "paho.mqtt", mqtt_package)
    monkeypatch.setitem(__import__("sys").modules, "paho.mqtt.client", module)

    runtime = FakePointRuntime()
    core = SimpleNamespace(point_runtime=runtime)
    instance = DriverInstance(
        name="MQTT test", station_id=str(uuid4()), driver_id="mqtt",
        protocol="MQTT 3.1.1", config={
            "host": "broker.example", "tls_ca_certs": str(ca_file),
            "bindings": [{"point_id": "point-1", "topic": "site/ahu/temp"}],
        },
    )
    adapter = DriverManagerService._build_mqtt_adapter(object(), core, instance)
    assert adapter.host == "broker.example"
    assert adapter.port == 8883
    assert client.ca_certs == str(ca_file)
    assert client.tls_insecure is False



def test_driver_manager_selects_native_c_worker_without_importing_paho(monkeypatch, tmp_path):
    from pathlib import Path
    from avic_core.drivers.manager import DriverManagerService

    called = {}
    def build(self, core, instance, cfg, bindings):
        called["engine"] = cfg["engine"]
        called["host"] = cfg["host"]
        called["bindings"] = bindings
        return "native-mqtt-adapter"

    monkeypatch.setattr(DriverManagerService, "_build_mqtt_c_worker_adapter", build)
    instance = DriverInstance(
        name="MQTT native", station_id=str(uuid4()), driver_id="mqtt",
        protocol="MQTT 5.0", config={
            "engine": "c", "host": "broker.local", "protocol": "5.0",
            "bindings": [{"point_id": "p1", "topic": "plant/temp", "qos": 2}],
        },
    )
    result = DriverManagerService._build_mqtt_adapter(
        object(), SimpleNamespace(point_runtime=FakePointRuntime()), instance,
    )
    assert result == "native-mqtt-adapter"
    assert called["engine"] == "c"
    assert called["host"] == "broker.local"
    assert called["bindings"][0].qos == 2



@pytest.mark.parametrize(
    ("topic_filter", "topic", "expected"),
    [
        ("plant/+/temp", "plant/ahu/temp", True),
        ("plant/+/temp", "plant/ahu/zone1/temp", False),
        ("plant/#", "plant", True),
        ("plant/#", "plant/ahu/temp", True),
        ("plant/ahu/temp", "plant/ahu/temp", True),
        ("plant/ahu/temp", "plant/ahu/humidity", False),
        ("#", "$SYS/broker/uptime", False),
        ("$SYS/#", "$SYS/broker/uptime", True),
        ("plant/+/temp", "plant//temp", True),
    ],
)
def test_mqtt_topic_filter_matching(topic_filter, topic, expected):
    from avic_core.drivers.mqtt_adapter import mqtt_topic_matches
    assert mqtt_topic_matches(topic_filter, topic) is expected


def test_mqtt_topic_filter_rejects_misplaced_wildcards():
    import pytest
    from avic_core.drivers.mqtt_adapter import MqttPointBinding
    with pytest.raises(ValueError, match="wildcards"):
        MqttPointBinding("bad", "plant/ahu#")
    with pytest.raises(ValueError, match="wildcards"):
        MqttPointBinding("bad", "plant/#/temp")
