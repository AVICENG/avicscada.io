from __future__ import annotations

import os

import pytest

from avic_core.application import CoreApplication
from avic_core.domain.models import Platform, Project, Station
from avic_core.drivers import manager as manager_module
from avic_core.drivers.manager import DriverInstance


def _core_with_project(tmp_path, monkeypatch):
    executable = tmp_path / ("avic-modbus-c-worker.exe" if os.name == "nt" else "avic-modbus-c-worker")
    executable.write_bytes(b"test placeholder")
    if os.name != "nt":
        executable.chmod(0o755)

    captured = {}

    class FakeCAdapter:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    if monkeypatch is not None:
        monkeypatch.setattr(manager_module, "RustDriverPointAdapter", FakeCAdapter)
    core = CoreApplication(tmp_path / "data", c_worker_command=executable)
    platform = Platform(name="AVIC Platform")
    project = Project(name="RTU Project", platform_id=platform.id)
    station = Station(name="RTU Station", project_id=project.id)
    core.repository.save(platform)
    core.repository.save(project)
    core.repository.save(station)
    return core, station, captured


def test_modbus_rtu_catalog_and_driver_manager_use_c_worker(tmp_path, monkeypatch):
    core, station, captured = _core_with_project(tmp_path, monkeypatch)
    try:
        catalog = {row["driver_id"]: row for row in core.driver_manager.catalog()}
        assert catalog["modbus-rtu"]["read_supported"] is True
        assert catalog["modbus-rtu"]["write_supported"] is False
        assert catalog["modbus-rtu"]["runtime_start_supported"] is True

        instance = DriverInstance(
            name="RS-485 line", station_id=station.id,
            driver_id="modbus-rtu", protocol="Modbus RTU",
            config={
                "serial_port": "COM12" if os.name == "nt" else "/dev/ttyUSB0",
                "baud_rate": 19200, "parity": "E", "data_bits": 8,
                "stop_bits": 1, "unit_id": 7, "timeout": 1.5,
                "rts_mode": "none", "engine": "c",
                "bindings": [{
                    "point_id": "point-rtu-1", "function": 3,
                    "address": 10, "count": 1, "data_type": "uint16",
                }],
            },
        )
        core.repository.save(instance)
        adapter = core.driver_manager._build_modbus_rtu_adapter(core, instance)
        assert captured["protocol"] == "modbus-rtu"
        assert captured["worker_mode"] == "C_LIBMODBUS_READ_ONLY"
        assert captured["config"]["serial_port"] == instance.config["serial_port"]
        assert captured["config"]["baud_rate"] == 19200
        assert captured["config"]["parity"] == "E"
        assert captured["bindings"][0]["point_id"] == "point-rtu-1"
        assert captured["worker_command"][0].endswith("avic-modbus-c-worker" + (".exe" if os.name == "nt" else ""))
    finally:
        core.close()


@pytest.mark.parametrize("overrides", [
    {"parity": "X"},
    {"baud_rate": 12345},
    {"data_bits": 9},
    {"stop_bits": 3},
    {"unit_id": 248},
    {"rts_mode": "automatic"},
    {"timeout": 0.01},
])
def test_modbus_rtu_manager_rejects_invalid_line_configuration(tmp_path, monkeypatch, overrides):
    core, station, _ = _core_with_project(tmp_path, monkeypatch)
    config = {
        "serial_port": "/dev/ttyUSB0", "baud_rate": 9600,
        "parity": "N", "data_bits": 8, "stop_bits": 1,
        "unit_id": 1, "timeout": 2.0, "rts_mode": "none",
        "bindings": [{
            "point_id": "point-1", "function": 3,
            "address": 0, "count": 1, "data_type": "uint16",
        }],
    }
    config.update(overrides)
    instance = DriverInstance(
        name="Invalid RTU", station_id=station.id,
        driver_id="modbus-rtu", protocol="Modbus RTU", config=config,
    )
    try:
        with pytest.raises(ValueError):
            core.driver_manager._build_modbus_rtu_adapter(core, instance)
    finally:
        core.close()


def test_modbus_rtu_manager_rejects_non_c_engine(tmp_path, monkeypatch):
    core, station, _ = _core_with_project(tmp_path, monkeypatch)
    instance = DriverInstance(
        name="Wrong engine", station_id=station.id,
        driver_id="modbus-rtu", protocol="Modbus RTU",
        config={
            "engine": "python", "serial_port": "/dev/ttyUSB0",
            "bindings": [{
                "point_id": "point-1", "function": 3,
                "address": 0, "count": 1, "data_type": "uint16",
            }],
        },
    )
    try:
        with pytest.raises(ValueError, match="libmodbus C Worker"):
            core.driver_manager._build_modbus_rtu_adapter(core, instance)
    finally:
        core.close()


def test_modbus_rtu_point_adapter_polls_through_c_worker_contract(tmp_path, monkeypatch):
    from avic_core.domain.models import Device, Point, PointQuality
    from avic_core.drivers import rust_point_adapter as adapter_module

    calls = {}

    class FakeWorker:
        def __init__(self, command, **kwargs):
            calls["command"] = command
            calls["identity"] = kwargs
            self.started = False

        def start(self, config):
            calls["config"] = config
            self.started = True

        def read(self, request):
            calls["read"] = request
            return {"transport_ok": True, "result": {"function": 3, "values": [231]}}

        def diagnostics(self):
            return {"started": self.started}

        def close(self):
            self.started = False

    monkeypatch.setattr(adapter_module, "RustDriverWorker", FakeWorker)
    core = CoreApplication(tmp_path / "runtime")
    platform = Platform(name="AVIC Platform")
    project = Project(name="RTU runtime", platform_id=platform.id)
    station = Station(name="RS485", project_id=project.id)
    core.repository.save(platform)
    core.repository.save(project)
    core.repository.save(station)
    driver = core.driver_manager.create_instance(station.id, "modbus-rtu", "RTU worker")
    device = Device(
        name="RTU device", station_id=station.id, protocol="modbus/rtu",
        address="/dev/ttyUSB0", driver_instance_id=driver["id"],
    )
    point = Point(
        name="Supply temperature", device_id=device.id, data_type="analog-input",
        native_identity="modbus:hr:10", source_ref="modbus-rtu://hr/10",
        value=None, quality=PointQuality.UNCERTAIN,
    )
    core.repository.save(device)
    core.repository.save(point)
    from avic_core.drivers.rust_point_adapter import RustDriverPointAdapter
    adapter = RustDriverPointAdapter(
        worker_command=["/opt/avic/avic-modbus-c-worker"], core=core,
        driver_instance_id=driver["id"], protocol="modbus-rtu",
        config={
            "serial_port": "/dev/ttyUSB0", "baud_rate": 19200,
            "parity": "E", "data_bits": 8, "stop_bits": 1,
            "unit_id": 7, "timeout": 1.5, "rts_mode": "none",
        },
        bindings=[{
            "point_id": point.id, "function": 3, "address": 10,
            "count": 1, "data_type": "uint16",
        }],
        installation_id="installation", project_id=project.id,
        station_id=station.id, generation=1,
        worker_mode="C_LIBMODBUS_READ_ONLY",
    )
    try:
        result = adapter.poll_once()
        assert result["results"][0]["ok"] is True
        assert result["results"][0]["value"] == 231
        assert result["results"][0]["quality"] == "GOOD"
        assert calls["config"]["protocol"] == "modbus-rtu"
        assert calls["read"] == {
            "protocol": "modbus-rtu", "unit_id": 7, "timeout_ms": 1500,
            "function": 3, "address": 10, "count": 1,
            "serial_port": "/dev/ttyUSB0", "baud_rate": 19200,
            "parity": "E", "data_bits": 8, "stop_bits": 1, "rts_mode": "none",
        }
    finally:
        adapter.close()
        core.close()


def test_serial_port_lease_is_exclusive_across_processes(tmp_path):
    import subprocess
    import sys
    from avic_core.drivers.serial_port_lease import SerialPortLease

    port = str(tmp_path / "virtual-rs485")
    lease = SerialPortLease(port).acquire()
    code = (
        "import sys; "
        "from avic_core.drivers.serial_port_lease import SerialPortLease, SerialPortBusyError; "
        "p=sys.argv[1]; "
        "try_acquire=None; "
        "\ntry:\n SerialPortLease(p).acquire()\n"
        "except SerialPortBusyError:\n sys.exit(0)\n"
        "sys.exit(5)\n"
    )
    try:
        result = subprocess.run(
            [sys.executable, "-c", code, port],
            capture_output=True, text=True, timeout=10,
        )
        assert result.returncode == 0, result.stderr
    finally:
        lease.release()
    with SerialPortLease(port):
        pass


def test_driver_manager_holds_and_releases_rtu_serial_lease(tmp_path):
    from avic_core.drivers.serial_port_lease import SerialPortBusyError, SerialPortLease

    core, station = _core_with_project(tmp_path, monkeypatch=None)
    port = str(tmp_path / "managed-rs485")
    class Adapter:
        def poll_once(self):
            return {"results": []}
        def close(self):
            pass

    instance = DriverInstance(
        name="Managed RS485", station_id=station.id,
        driver_id="modbus-rtu", protocol="Modbus RTU",
        config={"serial_port": port, "poll_interval_seconds": 0.1},
    )
    core.repository.save(instance)
    core.driver_manager.register_adapter_factory("modbus-rtu", lambda _core, _item: Adapter())
    try:
        core.driver_manager.start_instance(instance.id)
        with pytest.raises(SerialPortBusyError):
            SerialPortLease(port).acquire()
        core.driver_manager.stop_instance(instance.id)
        with SerialPortLease(port):
            pass
    finally:
        core.close()
