from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from avic_core.domain.models import PointQuality
from avic_core.drivers.mqtt_adapter import MqttPointBinding
from avic_core.drivers.mqtt_c_worker_adapter import MqttCWorkerPointAdapter
from avic_core.drivers.rust_worker import RustDriverWorker

WORKER = os.environ.get("AVIC_MQTT_C_WORKER")


def _worker():
    if not WORKER:
        pytest.skip("AVIC_MQTT_C_WORKER is supplied by the native C build job")
    path = Path(WORKER)
    if not path.is_absolute() or not path.is_file():
        pytest.fail(f"MQTT C Worker binary is missing: {path}")
    return path


def _config(port: int):
    suffix = uuid4().hex[:12]
    return {
        "protocol": "mqtt", "host": "127.0.0.1", "port": port,
        "keepalive": 30, "client_id": f"avic-ci-{suffix}",
        "mqtt_version": "3.1.1", "tls_ca_file": None,
        "bindings": [{
            "point_id": "point-ci", "topic": "avic/ci/telemetry",
            "qos": 1, "payload_format": "json", "value_path": "value",
            "scale": 1.0, "offset": 0.0,
        }],
    }


def test_mqtt_paho_c_worker_ipc_handshake_and_shutdown():
    worker = RustDriverWorker(
        [str(_worker())], installation_id="install-ci",
        project_id="project-ci", station_id="station-ci",
        driver_instance_id="driver-ci", generation=1, timeout_seconds=5,
    )
    try:
        worker.start(_config(18884))
        assert worker.diagnostics()["worker_version"] == "0.1.0"
    finally:
        worker.close()


class _PointRuntime:
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


@pytest.mark.skipif(
    os.environ.get("AVIC_MQTT_C_BROKER_TEST") != "1",
    reason="Mosquitto round-trip is enabled only in the Linux native integration job",
)
def test_mqtt_paho_c_worker_mosquitto_to_point_runtime():
    publisher = shutil.which("mosquitto_pub")
    if not publisher:
        pytest.fail("mosquitto_pub is required for MQTT native round-trip")
    runtime = _PointRuntime()
    adapter = MqttCWorkerPointAdapter(
        worker_command=[str(_worker())],
        core=SimpleNamespace(point_runtime=runtime),
        driver_instance_id="driver-ci-point-runtime",
        config={
            "host": "127.0.0.1", "port": 18883, "keepalive": 30,
            "client_id": f"avic-ci-{uuid4().hex[:12]}", "protocol": "3.1.1",
        },
        bindings=[
            MqttPointBinding(
                "point-ci", "avic/ci/telemetry", qos=1,
                payload_format="json", value_path="value",
            )
        ],
        installation_id="install-ci", project_id="project-ci",
        station_id="station-ci", generation=1,
    )
    try:
        adapter.start()
        deadline = time.monotonic() + 8
        connected = False
        while time.monotonic() < deadline:
            if adapter.diagnostics()["connected"]:
                connected = True
                break
            time.sleep(0.05)
        assert connected, "Paho C Worker did not connect to local Mosquitto"
        time.sleep(0.25)
        subprocess.run(
            [publisher, "-h", "127.0.0.1", "-p", "18883",
             "-t", "avic/ci/telemetry", "-q", "1", "-m", '{"value":23.75}'],
            check=True, timeout=5, capture_output=True,
        )
        assert runtime.sample_event.wait(8), "No MQTT sample reached Point Runtime"
        assert len(runtime.samples) == 1
        point_id, value, quality, timestamp, source = runtime.samples[0]
        assert (point_id, value, quality) == ("point-ci", 23.75, PointQuality.GOOD)
        assert timestamp.tzinfo is not None
        assert source == "driver-ci-point-runtime"
    finally:
        adapter.stop()
