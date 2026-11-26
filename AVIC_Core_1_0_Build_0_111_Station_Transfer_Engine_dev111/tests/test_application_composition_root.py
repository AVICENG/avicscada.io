from pathlib import Path

import pytest

from avic_core.application import CoreApplication, CoreClosedError
from avic_core.runtime.manager import RuntimeState


def test_composition_root_initializes_services_and_health(tmp_path):
    with CoreApplication(tmp_path / "data") as core:
        assert core.repository is not None
        assert core.configuration is not None
        assert core.alarms is not None
        assert core.engineering_lifecycle is not None
        stages = core.engineering_lifecycle.initialize_project("project-from-core", created_by="test")
        assert len(stages) == 14
        report = core.health_report()
        assert report.status == "OK"
        assert {item.name for item in report.checks} == {"data_directory", "audit_chain", "runtime"}


def test_station_lifecycles_are_independent(tmp_path):
    core = CoreApplication(tmp_path / "data")
    core.start_station("station-a")
    core.start_station("station-b")
    core.stop_station("station-a")
    assert core.runtime.get("station-a").state == RuntimeState.STOPPED
    assert core.runtime.get("station-b").state == RuntimeState.RUNNING
    core.close()
    assert core.runtime.get("station-b").state == RuntimeState.STOPPED


def test_failed_station_start_does_not_stop_other_station(tmp_path):
    core = CoreApplication(tmp_path / "data")
    core.start_station("good")
    with pytest.raises(RuntimeError):
        core.start_station("bad", start_hook=lambda: (_ for _ in ()).throw(RuntimeError("driver init failed")))
    assert core.runtime.get("good").state == RuntimeState.RUNNING
    assert core.runtime.get("bad").state == RuntimeState.ERROR
    assert core.health_report().status == "ERROR"
    core.close()


def test_closed_core_rejects_new_operations(tmp_path):
    core = CoreApplication(tmp_path / "data")
    core.close()
    with pytest.raises(CoreClosedError):
        core.register_station("station")


def test_project_backup_requires_preview_id_and_restores(tmp_path):
    core = CoreApplication(tmp_path / "data")
    source = tmp_path / "project"
    source.mkdir()
    (source / "project.json").write_text('{"name":"demo"}', encoding="utf-8")
    backup = core.create_backup(source)
    preview = core.backups.preview(backup)
    target = tmp_path / "restored"
    core.restore_backup(backup, target, expected_backup_id=preview.backup_id)
    assert (target / "project.json").read_text(encoding="utf-8") == '{"name":"demo"}'
    with pytest.raises(ValueError):
        core.restore_backup(backup, target, expected_backup_id="wrong")
    core.close()



def test_core_shutdown_preview_is_read_only_and_close_stops_owned_fbd_service(tmp_path):
    core = CoreApplication(tmp_path / "data")
    core.start_station("station-active")
    preview = core.shutdown_preview()
    assert preview["core_state"] == "RUNNING"
    assert [item["station_id"] for item in preview["active_stations"]] == ["station-active"]
    assert preview["field_writes_enabled"] is False
    assert core.closed is False

    core.close()
    assert core.closed is True
    assert core.runtime.get("station-active").state == RuntimeState.STOPPED
    assert core.fbd_execution._closed is True
    core.close()  # shutdown is idempotent
