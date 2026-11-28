from __future__ import annotations

import sys
import textwrap

import pytest

from avic_core.drivers.rust_worker import RustDriverWorker, RustWorkerError


FAKE_WORKER = textwrap.dedent(r"""
    import sys
    from datetime import datetime, timezone
    from uuid import uuid4
    from avic_core.drivers.ipc import DriverEnvelope, read_frame, write_frame

    seq = 0
    for request in iter(lambda: read_frame(sys.stdin.buffer), None):
        seq += 1
        if request.kind == "initialize":
            kind, payload, stop = "initialized", {"protocol": "avic.driver.ipc", "version": 1, "worker_version": "test"}, False
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


EVENT_WORKER = textwrap.dedent(r"""
    import sys
    from datetime import datetime, timezone
    from uuid import uuid4
    from avic_core.drivers.ipc import DriverEnvelope, read_frame, write_frame

    seq = 0
    def send(request, kind, payload, correlation_id):
        global seq
        seq += 1
        frame = DriverEnvelope(
            contract=request.contract, version=request.version, message_id=str(uuid4()),
            kind=kind, installation_id=request.installation_id, project_id=request.project_id,
            station_id=request.station_id, driver_instance_id=request.driver_instance_id,
            worker_id=request.worker_id, generation=request.generation, sequence=seq,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            correlation_id=correlation_id, payload=payload,
        )
        write_frame(sys.stdout.buffer, frame)

    for request in iter(lambda: read_frame(sys.stdin.buffer), None):
        if request.kind == "initialize":
            send(request, "initialized", {"protocol":"avic.driver.ipc","version":1,"worker_version":"events"}, request.message_id)
        elif request.kind == "configure":
            send(request, "configured", {"configured":True}, request.message_id)
        elif request.kind == "start":
            send(request, "status", {"state":"RUNNING"}, request.message_id)
        elif request.kind == "read":
            count = int(request.payload.get("event_count", 1))
            event_class = request.payload.get("event_class", "sample")
            for index in range(count):
                send(request, "event", {"event_class":event_class,"topic":"plant/temperature","value":index}, None)
            send(request, "read_result", {"result":{"value":42}}, request.message_id)
        elif request.kind == "stop":
            send(request, "status", {"state":"STOPPED"}, request.message_id)
        elif request.kind == "shutdown":
            send(request, "status", {"shutdown":True}, request.message_id)
            break
""")


def make_worker(program=FAKE_WORKER, *, timeout=2):
    return RustDriverWorker(
        [sys.executable, "-u", "-c", program],
        installation_id="install-1", project_id="project-1",
        station_id="station-1", driver_instance_id="driver-1",
        generation=1, timeout_seconds=timeout,
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
    with pytest.raises(ValueError, match="absolute"):
        RustDriverWorker(
            ["python"], installation_id="i", project_id="p", station_id="s",
            driver_instance_id="d", generation=1,
        )


def test_rust_worker_timeout_terminates_unresponsive_process():
    slow_worker = textwrap.dedent(r"""
        import sys, time
        from datetime import datetime, timezone
        from uuid import uuid4
        from avic_core.drivers.ipc import DriverEnvelope, read_frame, write_frame
        seq = 0
        for request in iter(lambda: read_frame(sys.stdin.buffer), None):
            seq += 1
            if request.kind == "read":
                time.sleep(3)
                continue
            if request.kind == "initialize":
                kind, payload = "initialized", {"protocol": "avic.driver.ipc", "version": 1, "worker_version": "test"}
            elif request.kind == "configure":
                kind, payload = "configured", {"configured": True}
            else:
                kind, payload = "status", {"state": "RUNNING"}
            response = DriverEnvelope(
                contract=request.contract, version=request.version, message_id=str(uuid4()),
                kind=kind, installation_id=request.installation_id, project_id=request.project_id,
                station_id=request.station_id, driver_instance_id=request.driver_instance_id,
                worker_id=request.worker_id, generation=request.generation, sequence=seq,
                sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
                correlation_id=request.message_id, payload=payload,
            )
            write_frame(sys.stdout.buffer, response)
    """)
    worker = make_worker(slow_worker, timeout=0.2)
    worker.start({"protocol": "modbus-tcp"})
    with pytest.raises(Exception, match="timed out"):
        worker.read({"protocol": "modbus-tcp"})
    assert worker.diagnostics()["process_alive"] is False


def test_async_event_before_response_does_not_consume_command_response():
    worker = make_worker(EVENT_WORKER)
    worker.start({"protocol": "mqtt"})
    result = worker.read({"event_count": 1})
    events = worker.drain_events()
    assert result == {"result": {"value": 42}}
    assert len(events) == 1
    assert events[0].kind == "event"
    assert events[0].correlation_id is None
    assert events[0].payload["value"] == 0
    worker.close()


def test_async_event_queue_overflow_drops_only_replaceable_samples_and_counts_them():
    worker = make_worker(EVENT_WORKER)
    worker.start({"protocol": "mqtt"})
    result = worker.read({"event_count": 300, "event_class": "sample"})
    diagnostics = worker.diagnostics()
    events = worker.drain_events()
    assert result == {"result": {"value": 42}}
    assert len(events) == worker.EVENT_QUEUE_CAPACITY
    assert diagnostics["event_received_count"] == 300
    assert diagnostics["event_overflow_count"] == 44
    assert diagnostics["event_queue_depth"] == worker.EVENT_QUEUE_CAPACITY
    worker.close()


def test_critical_event_queue_overflow_fences_worker():
    worker = make_worker(EVENT_WORKER)
    worker.start({"protocol": "mqtt"})
    with pytest.raises(RustWorkerError, match="critical asynchronous event queue overflow"):
        worker.read({"event_count": 300, "event_class": "alarm"})
    assert worker.diagnostics()["process_alive"] is False
    assert worker.diagnostics()["event_overflow_count"] == 1


def test_async_event_stream_and_response_share_one_sequence_guard():
    worker = make_worker(EVENT_WORKER)
    worker.start({"protocol": "mqtt"})
    worker.read({"event_count": 3})
    assert worker.diagnostics()["inbound_sequence_gaps"] == 0
    worker.close()


def test_event_drain_limit_is_validated():
    worker = make_worker()
    with pytest.raises(ValueError, match="max_items"):
        worker.drain_events(0)
