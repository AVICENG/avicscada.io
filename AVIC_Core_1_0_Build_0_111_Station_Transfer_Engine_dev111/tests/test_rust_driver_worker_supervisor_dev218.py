from __future__ import annotations

import sys
import textwrap
from pathlib import Path

from avic_core.drivers.rust_worker import RustDriverWorker


FAKE_WORKER = textwrap.dedent(r"""
    import sys
    from datetime import datetime, timezone
    from uuid import uuid4
    from avic_core.drivers.ipc import DriverEnvelope, read_frame, write_frame

    seq = 0
    for request in iter(lambda: read_frame(sys.stdin.buffer), None):
        seq += 1
        if request.kind == "initialize":
            kind, payload, stop = "initialized", {"version": 1}, False
        elif request.kind == "configure":
            kind, payload, stop = "configured", {"configured": True}, False
        elif request.kind == "start":
            kind, payload, stop = "status", {"state": "RUNNING"}, False
        elif request.kind == "read":
            kind, payload, stop = "read_result", {"transport_ok": True, "result": {"value": 42}}, False
        elif request.kind == "stop":
            kind, payload, stop = "status", {"state": "STOPPED"}, False
        elif request.kind == "shutdown":
            kind, payload, stop = "status", {"shutdown": True}, True
        else:
            kind, payload, stop = "error", {"code": "UNKNOWN"}, False
        response = DriverEnvelope(
            contract=request.contract, version=request.version, message_id=str(uuid4()),
            kind=kind, installation_id=request.installation_id, project_id=request.project_id,
            station_id=request.station_id, driver_instance_id=request.driver_instance_id,
            worker_id=request.worker_id, generation=request.generation, sequence=seq,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            correlation_id=request.message_id, payload=payload,
        )
        write_frame(sys.stdout.buffer, response)
        if stop:
            break
""")


def make_worker():
    return RustDriverWorker(
        [sys.executable, "-u", "-c", FAKE_WORKER],
        installation_id="install-1", project_id="project-1",
        station_id="station-1", driver_instance_id="driver-1",
        generation=1, timeout_seconds=2,
    )


def test_rust_worker_supervisor_lifecycle_and_read_round_trip():
    worker = make_worker()
    worker.start({"protocol": "modbus-tcp", "host": "127.0.0.1"})
    assert worker.diagnostics()["process_alive"] is True
    result = worker.read({"protocol": "modbus-tcp", "point_external_id": "p1"})
    assert result == {"transport_ok": True, "result": {"value": 42}}
    worker.close()
    assert worker.diagnostics()["process_alive"] is False


def test_rust_worker_requires_absolute_existing_executable():
    import pytest
    with pytest.raises(ValueError, match="absolute"):
        RustDriverWorker(
            ["python"], installation_id="i", project_id="p", station_id="s",
            driver_instance_id="d", generation=1,
        )
