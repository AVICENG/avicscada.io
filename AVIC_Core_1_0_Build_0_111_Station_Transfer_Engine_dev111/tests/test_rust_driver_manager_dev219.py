from __future__ import annotations

from pathlib import Path

from avic_core.application import CoreApplication
from avic_core.domain.models import Platform, Project, Station
from avic_core.drivers import manager as manager_module
from avic_core.drivers.manager import DriverInstance


def test_core_configures_rust_worker_and_driver_manager_selects_rust_backend(tmp_path, monkeypatch):
    executable = tmp_path / ("avic-driver-worker.exe" if __import__("os").name == "nt" else "avic-driver-worker")
    executable.write_bytes(b"test placeholder")
    if __import__("os").name != "nt":
        executable.chmod(0o755)

    captured = {}
    class FakeRustAdapter:
        def __init__(self, **kwargs):
            captured.update(kwargs)
        def poll_once(self):
            return {"results": []}
        def close(self):
            pass
        def diagnostics(self):
            return {"mode": "RUST_WORKER_READ_ONLY"}

    monkeypatch.setattr(manager_module, "RustDriverPointAdapter", FakeRustAdapter)

    with CoreApplication(tmp_path / "data", rust_worker_command=executable) as core:
        platform = Platform(name="AVIC Platform")
        project = Project(name="Project A", platform_id=platform.id)
        station = Station(name="Station A", project_id=project.id)
        core.repository.save(platform)
        core.repository.save(project)
        core.repository.save(station)

        instance = DriverInstance(
            name="Modbus Rust", station_id=station.id,
            driver_id="modbus-tcp", protocol="Modbus TCP",
            config={
                "engine": "rust", "host": "192.0.2.10", "port": 502,
                "unit_id": 1, "timeout": 2.0,
                "bindings": [{
                    "point_id": "point-1", "function": 3,
                    "address": 0, "count": 1, "data_type": "uint16",
                }],
            },
        )
        core.repository.save(instance)

        adapter = core.driver_manager._build_modbus_adapter(core, instance)
        assert isinstance(adapter, FakeRustAdapter)
        assert captured["worker_command"] == [str(executable.resolve())]
        assert captured["installation_id"] == platform.installation_id
        assert captured["project_id"] == project.id
        assert captured["station_id"] == station.id
        assert captured["protocol"] == "modbus-tcp"
        assert captured["bindings"][0]["point_id"] == "point-1"


def test_rust_worker_path_must_be_absolute_and_exist(tmp_path):
    with CoreApplication(tmp_path / "data") as core:
        import pytest
        with pytest.raises(ValueError, match="absolute"):
            core.driver_manager.register_rust_worker_command("avic-driver-worker")
