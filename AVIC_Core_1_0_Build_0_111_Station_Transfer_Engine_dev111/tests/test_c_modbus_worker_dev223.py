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
    # Selecting a worker engine must not instantiate the in-process Python client.
    def unexpected_python_client(*args, **kwargs):
        raise AssertionError("Python Modbus client must not be constructed for the C worker engine")
    monkeypatch.setattr(manager_module, "ModbusTcpClient", unexpected_python_client)

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


def test_compiled_c_worker_reads_all_read_only_modbus_functions_when_enabled():
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

    class ModbusReadFunctionSimulator(socketserver.BaseRequestHandler):
        def handle(self):
            while True:
                try:
                    header = recv_exact(self.request, 7)
                    tid, protocol_id = header[:2], header[2:4]
                    length, unit_id = int.from_bytes(header[4:6], "big"), header[6]
                    if protocol_id != b"\\x00\\x00" or not 2 <= length <= 254:
                        return
                    pdu = recv_exact(self.request, length - 1)
                    if len(pdu) != 5:
                        return
                    function = pdu[0]
                    address = int.from_bytes(pdu[1:3], "big")
                    count = int.from_bytes(pdu[3:5], "big")
                    if function == 1 and (count < 1 or count > 2000):
                        return
                    if function == 2 and (count < 1 or count > 2000):
                        return
                    if function in (3, 4) and (count < 1 or count > 125):
                        return
                    if function not in (1, 2, 3, 4) or address + count > 65536:
                        return
                    if function == 1:
                        data = bytes((0x55, 0x01))[:(count + 7) // 8]
                    elif function == 2:
                        data = bytes((0x02,))[:(count + 7) // 8]
                    elif function == 3:
                        data = b"".join((address + i).to_bytes(2, "big") for i in range(count))
                    else:
                        values = (0x1234, 0xABCD, 0x0102)
                        data = b"".join(values[i].to_bytes(2, "big") for i in range(count))
                    response_pdu = bytes((function, len(data))) + data
                    response = (tid + b"\\x00\\x00"
                        + (len(response_pdu) + 1).to_bytes(2, "big")
                        + bytes((unit_id,)) + response_pdu)
                    self.request.sendall(response)
                except (OSError, ConnectionError, IndexError):
                    return
    class ModbusSimulator(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True
        request_queue_size = 16

    cases = [
        (1, 9, [True, False, True, False, True, False, True, False, True]),
        (2, 3, [False, True, False]),
        (4, 2, [0x1234, 0xABCD]),
    ]
    with ModbusSimulator(("127.0.0.1", 0), ModbusReadFunctionSimulator) as server:
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host, port = server.server_address
        from avic_core.drivers.rust_worker import RustDriverWorker
        worker = RustDriverWorker(
            [str(__import__("pathlib").Path(worker_path).resolve())],
            installation_id="install-c-modbus-functions", project_id="project-c-modbus-functions",
            station_id="station-c-modbus-functions", driver_instance_id="driver-c-modbus-functions",
            generation=1, timeout_seconds=5.0,
        )
        try:
            worker.start({
                "protocol": "modbus-tcp", "host": host,
                "port": port, "unit_id": 7, "timeout": 2.0,
            })
            for function, count, expected in cases:
                response = worker.read({
                    "protocol": "modbus-tcp", "host": host, "port": port,
                    "unit_id": 7, "timeout_ms": 2000,
                    "function": function, "address": 0, "count": count,
                })
                assert response["transport_ok"] is True
                assert response["result"]["function"] == function
                assert response["result"]["values"] == expected
        finally:
            worker.close()
            server.shutdown()
            thread.join(timeout=2)


def test_compiled_c_worker_rejects_oversized_modbus_read_when_enabled():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    from avic_core.drivers.rust_worker import RustDriverWorker
    worker = RustDriverWorker(
        [str(__import__("pathlib").Path(worker_path).resolve())],
        installation_id="install-c-modbus-bounds", project_id="project-c-modbus-bounds",
        station_id="station-c-modbus-bounds", driver_instance_id="driver-c-modbus-bounds",
        generation=1, timeout_seconds=5.0,
    )
    worker.start({
        "protocol": "modbus-tcp", "host": "127.0.0.1",
        "port": 502, "unit_id": 1, "timeout": 2.0,
    })
    try:
        with __import__("pytest").raises(RuntimeError):
            worker.read({
                "protocol": "modbus-tcp", "host": "127.0.0.1", "port": 502,
                "unit_id": 1, "timeout_ms": 2000,
                "function": 3, "address": 0, "count": 126,
            })
    finally:
        worker.close()


def test_compiled_c_worker_accepts_modbus_rtu_configuration_and_rejects_read_scope_mismatch():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    from pathlib import Path
    from avic_core.drivers.rust_worker import RustDriverWorker, RustWorkerError

    worker = RustDriverWorker(
        [str(Path(worker_path).resolve())],
        installation_id="install-c-modbus-rtu", project_id="project-c-modbus-rtu",
        station_id="station-c-modbus-rtu", driver_instance_id="driver-c-modbus-rtu",
        generation=1, timeout_seconds=5.0,
    )
    worker.start({
        "protocol": "modbus-rtu",
        "serial_port": "/dev/avic-test-serial",
        "baud_rate": 9600,
        "parity": "E",
        "data_bits": 8,
        "stop_bits": 1,
        "unit_id": 7,
        "timeout": 1.5,
        "rts_mode": "none",
    })
    try:
        with __import__("pytest").raises(RustWorkerError, match="serial settings"):
            worker.read({
                "protocol": "modbus-rtu",
                "serial_port": "/dev/avic-test-serial",
                "baud_rate": 19200,
                "parity": "E",
                "data_bits": 8,
                "stop_bits": 1,
                "unit_id": 7,
                "timeout_ms": 1500,
                "function": 3,
                "address": 0,
                "count": 1,
            })
    finally:
        worker.close()


def test_compiled_c_worker_rejects_invalid_modbus_rtu_configuration_when_enabled():
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        import pytest
        pytest.skip("C Worker binary is supplied only by the native C build job")

    from pathlib import Path
    from avic_core.drivers.rust_worker import RustDriverWorker, RustWorkerError

    worker = RustDriverWorker(
        [str(Path(worker_path).resolve())],
        installation_id="install-c-modbus-rtu-invalid", project_id="project-c-modbus-rtu-invalid",
        station_id="station-c-modbus-rtu-invalid", driver_instance_id="driver-c-modbus-rtu-invalid",
        generation=1, timeout_seconds=5.0,
    )
    with __import__("pytest").raises(RustWorkerError, match="Invalid Modbus TCP/RTU configuration"):
        worker.start({
            "protocol": "modbus-rtu",
            "serial_port": "/dev/avic-test-serial",
            "baud_rate": 9600,
            "parity": "X",
            "data_bits": 8,
            "stop_bits": 1,
            "unit_id": 7,
            "timeout": 1.5,
        })
    worker.close()


def test_compiled_c_worker_modbus_rtu_read_roundtrip_over_linux_pty_when_enabled():
    import pytest
    if os.name == "nt":
        pytest.skip("Linux PTY round-trip is exercised by the Linux native C job")
    worker_path = os.environ.get("AVIC_C_MODBUS_WORKER")
    if not worker_path:
        pytest.skip("C Worker binary is supplied only by the native C build job")

    import os as os_module
    import pty
    import select
    import tty
    from pathlib import Path
    from avic_core.drivers.rust_worker import RustDriverWorker

    master_fd, slave_fd = pty.openpty()
    serial_port = os_module.ttyname(slave_fd)
    tty.setraw(slave_fd)
    os_module.close(slave_fd)

    def crc16(data: bytes) -> int:
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                crc = (crc >> 1) ^ (0xA001 if crc & 1 else 0)
        return crc

    simulator_error = []

    def simulator():
        try:
            ready, _, _ = select.select([master_fd], [], [], 5.0)
            if not ready:
                raise TimeoutError("RTU simulator did not receive a request")
            request = bytearray()
            while len(request) < 8:
                ready, _, _ = select.select([master_fd], [], [], 2.0)
                if not ready:
                    raise TimeoutError("RTU request frame was truncated")
                request.extend(os_module.read(master_fd, 8 - len(request)))
            if request[0] != 7 or request[1] != 3 or crc16(request[:-2]) != int.from_bytes(request[-2:], "little"):
                raise AssertionError(f"invalid Modbus RTU request: {bytes(request).hex()}")
            body = bytes((7, 3, 2, 0x12, 0x34))
            crc = crc16(body)
            os_module.write(master_fd, body + crc.to_bytes(2, "little"))
        except Exception as exc:
            simulator_error.append(exc)

    simulator_thread = threading.Thread(target=simulator, daemon=True)
    simulator_thread.start()
    worker = RustDriverWorker(
        [str(Path(worker_path).resolve())],
        installation_id="install-c-modbus-rtu-pty", project_id="project-c-modbus-rtu-pty",
        station_id="station-c-modbus-rtu-pty", driver_instance_id="driver-c-modbus-rtu-pty",
        generation=1, timeout_seconds=5.0,
    )
    try:
        worker.start({
            "protocol": "modbus-rtu", "serial_port": serial_port,
            "baud_rate": 9600, "parity": "N", "data_bits": 8,
            "stop_bits": 1, "unit_id": 7, "timeout": 1.5,
        })
        response = worker.read({
            "protocol": "modbus-rtu", "serial_port": serial_port,
            "baud_rate": 9600, "parity": "N", "data_bits": 8,
            "stop_bits": 1, "unit_id": 7, "timeout_ms": 1500,
            "function": 3, "address": 0, "count": 1,
        })
        assert response["transport_ok"] is True
        assert response["result"] == {"function": 3, "values": [0x1234]}
        simulator_thread.join(timeout=2)
        assert not simulator_thread.is_alive()
        assert not simulator_error, repr(simulator_error)
    finally:
        worker.close()
        os_module.close(master_fd)
