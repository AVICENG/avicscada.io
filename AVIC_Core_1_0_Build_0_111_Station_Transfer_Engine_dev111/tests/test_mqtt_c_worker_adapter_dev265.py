from __future__ import annotations

from datetime import datetime, timezone
from queue import Queue, Empty
from types import SimpleNamespace
import threading

import pytest

from avic_core.domain.models import PointQuality
from avic_core.drivers.mqtt_adapter import MqttPointBinding
from avic_core.drivers.mqtt_c_worker_adapter import MqttCWorkerPointAdapter


class FakeWorker:
    def __init__(self, *args, **kwargs):
        self.events = Queue()
        self.started = False
        self.closed = False
        self.config = None

    def start(self, config):
        self.config = config
        self.started = True

    def next_event(self, timeout_seconds=0):
        try:
            return self.events.get(timeout=timeout_seconds)
        except Empty:
            return None

    def close(self):
        self.closed = True
        self.started = False

    def diagnostics(self):
        return {"started": self.started, "process_alive": self.started}


class FakeRuntime:
    def __init__(self):
        self.samples = []
        self.qualities = []
        self.sample_event = threading.Event()

    def publish(self, point_id, value, *, quality, timestamp, source_driver_id):
        self.samples.append((point_id, value, quality, timestamp, source_driver_id))
        self.sample_event.set()
        return SimpleNamespace(timestamp=timestamp, value=value, quality=quality)

    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.qualities.append((point_id, quality, source_driver_id))


def build_adapter(monkeypatch):
    from avic_core.drivers import mqtt_c_worker_adapter as module

    worker = FakeWorker()
    monkeypatch.setattr(module, "RustDriverWorker", lambda *a, **k: worker)
    runtime = FakeRuntime()
    core = SimpleNamespace(point_runtime=runtime)
    adapter = MqttCWorkerPointAdapter(
        worker_command=["/absolute/avic-mqtt-c-worker"], core=core,
        driver_instance_id="driver-123",
        config={"host": "broker.local", "port": 1883, "protocol": "5.0"},
        bindings=[
            MqttPointBinding("point-1", "plant/ahu/temp", qos=1,
                             value_path="telemetry.temp", scale=1.8, offset=32),
            MqttPointBinding("point-2", "plant/ahu/temp", qos=2,
                             value_path="telemetry.temp"),
        ],
        installation_id="install-1", project_id="project-1",
        station_id="station-1", generation=3,
    )
    return adapter, worker, runtime


def test_mqtt_c_worker_receives_config_and_routes_sample_to_bound_points(monkeypatch):
    adapter, worker, runtime = build_adapter(monkeypatch)
    adapter.start()
    assert worker.started is True
    assert worker.config["protocol"] == "mqtt"
    assert worker.config["mqtt_version"] == "5.0"
    assert len(worker.config["bindings"]) == 2

    worker.events.put(SimpleNamespace(kind="status", payload={"connected": True}))
    worker.events.put(SimpleNamespace(kind="sample", payload={
        "topic": "plant/ahu/temp",
        "payload": '{"telemetry":{"temp":20}}',
        "qos": 1,
        "received_at": "2026-11-28T08:00:00.000Z",
    }))
    assert runtime.sample_event.wait(2.0)
    assert len(runtime.samples) == 2
    assert runtime.samples[0][0:3] == ("point-1", 68.0, PointQuality.GOOD)
    assert runtime.samples[1][0:3] == ("point-2", 20.0, PointQuality.GOOD)
    assert all(sample[3].tzinfo == timezone.utc for sample in runtime.samples)
    assert adapter.diagnostics()["connected"] is True
    adapter.stop()
    assert worker.closed is True


def test_mqtt_c_worker_rejects_bad_timestamp_without_publishing(monkeypatch):
    adapter, worker, runtime = build_adapter(monkeypatch)
    adapter.start()
    worker.events.put(SimpleNamespace(kind="sample", payload={
        "topic": "plant/ahu/temp", "payload": '{"telemetry":{"temp":20}}',
        "qos": 1, "received_at": "2026-11-28T08:00:00",
    }))
    # Invalid event envelope must be rejected and diagnosed; no point may receive it.
    import time
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and "__event__" not in adapter.diagnostics()["last_errors"]:
        time.sleep(0.01)
    assert runtime.samples == []
    assert "__event__" in adapter.diagnostics()["last_errors"]
    adapter.stop()


def test_mqtt_c_worker_ignores_unmapped_topics_and_marks_points_stale_on_stop(monkeypatch):
    adapter, worker, runtime = build_adapter(monkeypatch)
    adapter.start()
    worker.events.put(SimpleNamespace(kind="sample", payload={
        "topic": "unmapped/topic", "payload": '{"value":1}',
        "qos": 0, "received_at": "2026-11-28T08:00:00.000Z",
    }))
    import time
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and adapter.diagnostics()["unknown_topic_count"] == 0:
        time.sleep(0.01)
    assert runtime.samples == []
    assert adapter.diagnostics()["unknown_topic_count"] == 1
    adapter.stop()
    assert all(item[1] == PointQuality.STALE for item in runtime.qualities)


def test_mqtt_c_worker_rejects_duplicate_point_bindings(monkeypatch):
    from avic_core.drivers import mqtt_c_worker_adapter as module
    monkeypatch.setattr(module, "RustDriverWorker", lambda *a, **k: FakeWorker())
    core = SimpleNamespace(point_runtime=FakeRuntime())
    with pytest.raises(ValueError, match="duplicate"):
        MqttCWorkerPointAdapter(
            worker_command=["/absolute/worker"], core=core, driver_instance_id="d",
            config={"host": "broker"}, bindings=[
                MqttPointBinding("same", "a"), MqttPointBinding("same", "b"),
            ],
            installation_id="i", project_id="p", station_id="s",
        )



def test_mqtt_c_worker_routes_wildcard_topic_filters(monkeypatch):
    adapter, worker, runtime = build_adapter(monkeypatch)
    # Replace the exact filters with a legal wildcard binding for this scenario.
    adapter.stop() if adapter._started else None
    adapter = MqttCWorkerPointAdapter(
        worker_command=["/absolute/avic-mqtt-c-worker"],
        core=SimpleNamespace(point_runtime=runtime),
        driver_instance_id="driver-wildcard",
        config={"host": "broker.local"},
        bindings=[MqttPointBinding("point-wild", "plant/+/temp", qos=1)],
        installation_id="install-1", project_id="project-1", station_id="station-1",
    )
    adapter.start()
    worker.events.put(SimpleNamespace(kind="sample", payload={
        "topic": "plant/ahu/temp", "payload": '{"value":22.5}',
        "qos": 1, "received_at": "2026-11-28T08:00:00.000Z",
    }))
    assert runtime.sample_event.wait(2.0)
    assert runtime.samples[0][0:3] == ("point-wild", 22.5, PointQuality.GOOD)
    adapter.stop()


def test_mqtt_subscription_fault_is_scoped_to_affected_point(monkeypatch):
    from avic_core.drivers import mqtt_c_worker_adapter as module

    worker = FakeWorker()
    monkeypatch.setattr(module, "RustDriverWorker", lambda *a, **k: worker)
    runtime = FakeRuntime()
    adapter = MqttCWorkerPointAdapter(
        worker_command=["/absolute/avic-mqtt-c-worker"],
        core=SimpleNamespace(point_runtime=runtime),
        driver_instance_id="driver-subscription-fault",
        config={"host": "broker.local", "port": 1883, "protocol": "3.1.1"},
        bindings=[
            MqttPointBinding("point-allowed", "plant/ahu/temp", qos=1),
            MqttPointBinding("point-denied", "plant/ahu/pressure", qos=1),
        ],
        installation_id="install-1", project_id="project-1",
        station_id="station-1", generation=1,
    )
    adapter.start()
    worker.events.put(SimpleNamespace(kind="status", payload={"connected": True}))
    worker.events.put(SimpleNamespace(kind="fault", payload={
        "message": "MQTT subscription rejected by broker",
        "topic": "plant/ahu/pressure",
        "point_id": "point-denied",
        "broker_code": 5,
    }))
    import time
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and not runtime.qualities:
        time.sleep(0.01)
    assert runtime.qualities == [
        ("point-denied", PointQuality.BAD_CONFIGURATION, "driver-subscription-fault")
    ]
    assert adapter.diagnostics()["connected"] is True
    assert "point-denied" in adapter.diagnostics()["last_errors"]
    adapter.stop()
