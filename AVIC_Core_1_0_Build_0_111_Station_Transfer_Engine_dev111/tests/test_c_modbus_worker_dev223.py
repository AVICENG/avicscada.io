from __future__ import annotations

import os

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
        status = worker.get_status()
        assert status["state"] == "RUNNING"
        assert status["write_supported"] is False
    finally:
        worker.close()
    assert worker.diagnostics()["process_alive"] is False
