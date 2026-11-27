from __future__ import annotations

import os
import socketserver
import threading
import subprocess
from datetime import datetime, timezone
from uuid import uuid4

from avic_core.application import CoreApplication
from avic_core.domain.models import Platform, Project, Station
from avic_core.drivers import manager as manager_module
from avic_core.drivers.manager import DriverInstance


def test_driver_manager_selects_c_libmodbus_worker_for_modbus(tmp_path, monkeypatch):
    executable = tmp_path / ("avic-modbus-c-worker.exe" if os.name == "nt" else "avic-modbus-c-worker")
    executable.write_bytes(b"test placeholder")
    if os.name != "nt":
        executable.chmod(0o755)

    captured = {}

    class FakeCAdapter:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(manager_module, "RustDriverPointAdapter", FakeCAdapter)

    with CoreApplication(tmp_path / "data", c_worker_command=executable) as core:
        platform = Platform(name="AVIC Platform")
        project = Project(name="C Worker Project", platform_id=platform.id)
        station = Station(name="C Worker Station", project_id=project.id)
        core.repository.save(platform)
        core.repository.save(project)
        core.repository.save(station)

        instance = DriverInstance(
            name="Modbus C", station_id=station.id,
            driver_id="modbus-tcp", protocol="Modbus TCP",
            config={
                "engine": "c", "host": "192.0.2.10", "port": 502,
                "unit_id": 1, "timeout": 2.0,
                "bindings": [{
                    "point_id": "point-1", "function": 3,
                    "address": 0, "count": 1, "data_type": "uint16",
                }],
            },
        )
        core.repository.save(instance)

        adapter = core.driver_manager._build_modbus_adapter(core, instance)
        assert isinstance(adapter, FakeCAdapter)
        assert captured["worker_command"] == [str(executable.resolve())]
        assert captured["protocol"] == "modbus-tcp"
        assert captured["worker_mode"] == "C_LIBMODBUS_READ_ONLY"
        assert captured["bindings"][0]["point_id"] == "point-1"
        assert captured["generation"] == 1

        catalog = {item["driver_id"]: item for item in core.driver_manager.catalog()}
        assert "c" in catalog["modbus-tcp"]["supported_engines"]
        assert catalog["modbus-tcp"]["c_engine_available"] is True


def test_c_worker_registration_requires_absolute_existing_executable(tmp_path):
    with CoreApplication(tmp_path / "data") as core:
        import pytest
        with pytest.raises(ValueError, match="absolute"):
            core.driver_manager.register_c_worker_command("avic-modbus-c-worker")


def test_compiled_c_worker_ipc_handshake_when_enabled():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    from avic_core.drivers.rust_worker import RustDriverWorker

    worker = RustDriverWorker(
        [str(__import__("pathlib").Path(worker_path).resolve())],
        installation_id="install-c-test", project_id="project-c-test",
        station_id="station-c-test", driver_instance_id="driver-c-test",
        generation=1, timeout_seconds=3.0,
    )
    worker.start({
        "protocol": "modbus-tcp", "host": "127.0.0.1",
        "port": 502, "unit_id": 1, "timeout": 2.0,
    })
    try:
        assert worker.diagnostics()["started"] is True
        assert worker.diagnostics()["process_alive"] is True
    finally:
        worker.close()
    assert worker.diagnostics()["process_alive"] is False



def test_compiled_c_worker_reads_modbus_tcp_register_range_when_enabled():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    def recv_exact(sock, size):
        data = bytearray()
        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("client closed Modbus test socket")
            data.extend(chunk)
        return bytes(data)

    class ModbusSimulatorHandler(socketserver.BaseRequestHandler):
        def handle(self):
            while True:
                try:
                    header = recv_exact(self.request, 7)
                    transaction_id = header[:2]
                    protocol_id = header[2:4]
                    length = int.from_bytes(header[4:6], "big")
                    unit_id = header[6]
                    if protocol_id != b"\x00\x00" or not 2 <= length <= 254:
                        return
                    pdu = recv_exact(self.request, length - 1)
                    if len(pdu) != 5 or pdu[0] != 3:
                        return
                    address = int.from_bytes(pdu[1:3], "big")
                    count = int.from_bytes(pdu[3:5], "big")
                    if not 1 <= count <= 125 or address + count > 65536:
                        return
                    data = b"".join(
                        (address + offset).to_bytes(2, "big")
                        for offset in range(count)
                    )
                    response_pdu = bytes((3, len(data))) + data
                    response = (
                        transaction_id + b"\x00\x00"
                        + (len(response_pdu) + 1).to_bytes(2, "big")
                        + bytes((unit_id,)) + response_pdu
                    )
                    self.request.sendall(response)
                except (OSError, ConnectionError):
                    return

    class ModbusSimulator(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
        request_queue_size = 16

    with ModbusSimulator(("127.0.0.1", 0), ModbusSimulatorHandler) as server:
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        host, port = server.server_address
        from avic_core.drivers.rust_worker import RustDriverWorker

        worker = RustDriverWorker(
            [str(__import__("pathlib").Path(worker_path).resolve())],
            installation_id="install-c-modbus-test", project_id="project-c-modbus-test",
            station_id="station-c-modbus-test", driver_instance_id="driver-c-modbus-test",
            generation=1, timeout_seconds=5.0,
        )
        try:
            worker.start({
                "protocol": "modbus-tcp", "host": host,
                "port": port, "unit_id": 7, "timeout": 2.0,
            })
            response = worker.read({
                "protocol": "modbus-tcp", "host": host, "port": port,
                "unit_id": 7, "timeout_ms": 2000,
                "function": 3, "address": 7, "count": 3,
            })
            assert response["transport_ok"] is True
            assert response["result"]["function"] == 3
            assert response["result"]["values"] == [7, 8, 9]
        finally:
            worker.close()
            server.shutdown()
            server_thread.join(timeout=2)



def test_compiled_c_worker_fails_closed_on_replayed_ipc_sequence():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    from avic_core.drivers.ipc import DriverEnvelope, encode_frame, read_frame

    process = subprocess.Popen(
        [str(__import__("pathlib").Path(worker_path).resolve())],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=0,
    )
    worker_id = str(uuid4())
    scope = {
        "installation_id": "install-sequence-test",
        "project_id": "project-sequence-test",
        "station_id": "station-sequence-test",
        "driver_instance_id": "driver-sequence-test",
        "worker_id": worker_id,
        "generation": 1,
    }

    def send(kind, sequence, payload):
        envelope = DriverEnvelope(
            contract="avic.driver.ipc", version=1, message_id=str(uuid4()),
            kind=kind, **scope, sequence=sequence,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            correlation_id=None, payload=payload,
        )
        process.stdin.write(encode_frame(envelope))
        process.stdin.flush()
        response = read_frame(process.stdout)
        if response is None:
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
            raise AssertionError(
                f"C Worker closed stdout during {kind}; exit_code={process.returncode}; stderr={stderr!r}"
            )
        return response

    try:
        assert send("initialize", 1, {}).kind == "initialized"
        assert send("configure", 2, {
            "protocol": "modbus-tcp", "host": "127.0.0.1",
            "port": 502, "unit_id": 1, "timeout": 2.0,
        }).kind == "configured"
        assert send("start", 3, {}).kind == "status"
        write_response = send("write", 4, {
            "protocol": "modbus-tcp", "address": 7, "value": 99,
        })
        assert write_response.kind == "error"
        assert write_response.payload["code"] == "WRITE_DISABLED"

        # A replayed sequence must terminate the worker before any new action.
        process.stdin.write(encode_frame(DriverEnvelope(
            contract="avic.driver.ipc", version=1, message_id=str(uuid4()),
            kind="get_status", **scope, sequence=4,
            sent_at=datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
            correlation_id=None, payload={},
        )))
        process.stdin.flush()
        assert read_frame(process.stdout) is None
        assert process.wait(timeout=3) == 3
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=3)
        for stream in (process.stdin, process.stdout, process.stderr):
            if stream is not None:
                stream.close()
