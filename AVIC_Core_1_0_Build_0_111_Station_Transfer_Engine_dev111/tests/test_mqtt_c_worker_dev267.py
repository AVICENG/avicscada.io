from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import time
from uuid import uuid4

import pytest

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


@pytest.mark.skipif(
    os.environ.get("AVIC_MQTT_C_BROKER_TEST") != "1",
    reason="Mosquitto round-trip is enabled only in the Linux native integration job",
)
def test_mqtt_paho_c_worker_receives_mosquitto_publish():
    publisher = shutil.which("mosquitto_pub")
    if not publisher:
        pytest.fail("mosquitto_pub is required for MQTT native round-trip")
    worker = RustDriverWorker(
        [str(_worker())], installation_id="install-ci",
        project_id="project-ci", station_id="station-ci",
        driver_instance_id="driver-ci", generation=1, timeout_seconds=5,
    )
    try:
        worker.start(_config(18883))
        deadline = time.monotonic() + 8
        connected = False
        while time.monotonic() < deadline:
            event = worker.next_event(timeout_seconds=0.25)
            if event and event.kind == "status" and event.payload.get("connected") is True:
                connected = True
                break
        assert connected, "Paho C Worker did not connect to local Mosquitto"
        time.sleep(0.25)
        subprocess.run(
            [publisher, "-h", "127.0.0.1", "-p", "18883",
             "-t", "avic/ci/telemetry", "-q", "1", "-m", '{"value":23.75}'],
            check=True, timeout=5, capture_output=True,
        )
        deadline = time.monotonic() + 8
        sample = None
        while time.monotonic() < deadline:
            event = worker.next_event(timeout_seconds=0.25)
            if event and event.kind == "sample":
                sample = event
                break
        assert sample is not None, "No MQTT sample event arrived over AVIC IPC"
        assert sample.payload["topic"] == "avic/ci/telemetry"
        assert sample.payload["payload"] == '{"value":23.75}'
        assert sample.payload["qos"] == 1
        assert sample.payload["event_class"] == "sample"
        assert sample.payload["received_at"].endswith("Z")
    finally:
        worker.close()
