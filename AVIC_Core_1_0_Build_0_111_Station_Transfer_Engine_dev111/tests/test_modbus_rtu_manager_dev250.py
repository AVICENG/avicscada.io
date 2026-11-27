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
