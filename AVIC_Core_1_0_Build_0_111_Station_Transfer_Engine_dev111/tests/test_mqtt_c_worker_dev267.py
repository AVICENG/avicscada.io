from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime, timezone
import shutil
import socket
import subprocess
import threading
import time
from types import SimpleNamespace
from uuid import uuid4

import pytest

from avic_core.domain.models import PointQuality
from avic_core.drivers.mqtt_adapter import MqttPointBinding
from avic_core.drivers.mqtt_c_worker_adapter import MqttCWorkerPointAdapter
from avic_core.drivers.rust_worker import RustDriverWorker, RustWorkerError

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
        status = worker._request("get_status", {})
        assert status.kind == "status"
        assert status.payload["connected"] is False
        response_time = datetime.fromisoformat(status.sent_at.replace("Z", "+00:00"))
        assert abs((datetime.now(timezone.utc) - response_time).total_seconds()) < 5
    finally:
        worker.close()
    assert worker.diagnostics()["process_alive"] is False
    assert worker.diagnostics()["exit_code"] == 0

@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("mqtt_version", "5.0"),
        ("tls_ca_file", "C:/secrets/ca.pem"),
        ("qos", 3),
        ("port", 65536),
    ],
)
def test_mqtt_paho_c_worker_rejects_unsupported_or_invalid_configuration(field, value):
    worker = RustDriverWorker(
        [str(_worker())], installation_id="install-ci",
        project_id="project-ci", station_id="station-ci",
        driver_instance_id="driver-negative-ci", generation=1, timeout_seconds=5,
    )
    config = _config(18884)
    if field == "qos":
        config["bindings"][0]["qos"] = value
    else:
        config[field] = value
    with pytest.raises(RustWorkerError, match="MQTT C Worker accepts"):
        worker.start(config)
    assert worker.diagnostics()["process_alive"] is False


def _start_local_mosquitto(tmp_path, port):
    executable = shutil.which("mosquitto")
    if not executable:
        pytest.fail("mosquitto executable is required for reconnect acceptance")
    # Match the exact CLI mode used by the primary CI broker job. With no
    # config file Mosquitto 2.x creates its loopback-only default listener.
    process = subprocess.Popen(
        [executable, "-p", str(port), "-v"],
        stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT,
    )
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if process.poll() is not None:
            pytest.fail(f"Mosquitto exited early with code {process.returncode}")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return process
        except OSError:
            time.sleep(0.1)
    process.terminate()
    process.wait(timeout=3)
    pytest.fail("Mosquitto did not start listening")


@pytest.mark.skipif(
    os.environ.get("AVIC_MQTT_C_BROKER_TEST") != "1",
    reason="Mosquitto reconnect acceptance is enabled only in native integration jobs",
)
def test_mqtt_paho_c_worker_reconnects_and_resubscribes(tmp_path):
    publisher = shutil.which("mosquitto_pub")
    if not publisher:
        pytest.fail("mosquitto_pub is required for reconnect acceptance")
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    broker = _start_local_mosquitto(tmp_path, port)
    runtime = _PointRuntime()
    adapter = MqttCWorkerPointAdapter(
        worker_command=[str(_worker())],
        core=SimpleNamespace(point_runtime=runtime),
        driver_instance_id="driver-ci-reconnect",
        config={
            "host": "127.0.0.1", "port": port, "keepalive": 30,
            "client_id": f"avic-ci-{uuid4().hex[:12]}", "protocol": "3.1.1",
        },
        bindings=[
            MqttPointBinding(
                "point-ci", "avic/ci/reconnect", qos=1,
                payload_format="json", value_path="value",
            )
        ],
        installation_id="install-ci", project_id="project-ci",
        station_id="station-ci", generation=1,
    )
    replacement = None
    try:
        adapter.start()
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not adapter.diagnostics()["connected"]:
            time.sleep(0.05)
        assert adapter.diagnostics()["connected"], "initial MQTT connection did not establish"

        broker.terminate()
        broker.wait(timeout=5)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and adapter.diagnostics()["connected"]:
            time.sleep(0.05)
        assert not adapter.diagnostics()["connected"], "connection-loss callback was not observed"

        replacement = _start_local_mosquitto(tmp_path, port)
        deadline = time.monotonic() + 25
        while time.monotonic() < deadline and not adapter.diagnostics()["connected"]:
            time.sleep(0.1)
        assert adapter.diagnostics()["connected"], "Paho automatic reconnect did not restore connection: " + repr(adapter.diagnostics())
        time.sleep(0.5)  # allow the resubscribe request to be acknowledged

        subprocess.run(
            [publisher, "-h", "127.0.0.1", "-p", str(port),
             "-t", "avic/ci/reconnect", "-q", "1", "-m", '{"value":42.5}'],
            check=True, timeout=5, capture_output=True,
        )
        assert runtime.sample_event.wait(8), "resubscribed topic did not deliver a sample"
        assert runtime.samples[0][1] == 42.5
    finally:
        adapter.stop()
        for process in (replacement, broker):
            if process is not None and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)


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
    reason="Mosquitto round-trip is enabled only in native integration jobs",
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
        assert connected, "Paho C Worker did not connect to local Mosquitto: " + repr(adapter.diagnostics())
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
