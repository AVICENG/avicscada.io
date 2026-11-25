from __future__ import annotations

import sqlite3

import pytest

from avic_core.application.container import CoreApplication
from avic_core.backup import SystemBackupError
from avic_core.ui.project_station import ProjectStationService


PASSPHRASE = "AVIC-system-backup-test-passphrase"


def test_encrypted_system_backup_inspect_and_restore(tmp_path):
    source_root = tmp_path / "source"
    target_root = tmp_path / "restored"
    with CoreApplication(source_root) as core:
        project = ProjectStationService(core).create_project("Backup integration project")
        core.repository.save_graph([])
        backup = core.create_system_backup(tmp_path / "system.avicbackup", passphrase=PASSPHRASE)
        assert backup.is_file()
        assert backup.read_bytes().startswith(core.system_backups.MAGIC)

        preview = core.inspect_system_backup(backup, passphrase=PASSPHRASE)
        assert preview.checksum_valid is True
        assert preview.file_count > 0
        assert "databases/objects.sqlite3" in preview.databases
        assert preview.backup_id

        restored = core.restore_system_backup(
            backup, target_root, passphrase=PASSPHRASE, expected_backup_id=preview.backup_id
        )
        assert restored == target_root
        assert (target_root / "databases" / "objects.sqlite3").is_file()
        with CoreApplication(target_root) as recovered:
            assert recovered.repository.get_record(project["id"])["payload"]["name"] == "Backup integration project"


def test_system_backup_rejects_wrong_passphrase(tmp_path):
    with CoreApplication(tmp_path / "source") as core:
        backup = core.create_system_backup(tmp_path / "system.avicbackup", passphrase=PASSPHRASE)
        with pytest.raises(SystemBackupError, match="Неверный пароль"):
            core.inspect_system_backup(backup, passphrase="incorrect-system-backup-passphrase")


def test_system_backup_requires_all_stations_stopped(tmp_path):
    core = CoreApplication(tmp_path / "source")
    core.start_station("running-station")
    try:
        with pytest.raises(SystemBackupError, match="остановите все станции"):
            core.create_system_backup(tmp_path / "system.avicbackup", passphrase=PASSPHRASE)
    finally:
        core.close()


def test_system_backup_restore_requires_empty_target(tmp_path):
    with CoreApplication(tmp_path / "source") as core:
        backup = core.create_system_backup(tmp_path / "system.avicbackup", passphrase=PASSPHRASE)
        preview = core.inspect_system_backup(backup, passphrase=PASSPHRASE)
        target = tmp_path / "occupied"
        target.mkdir()
        (target / "keep.txt").write_text("keep", encoding="utf-8")
        with pytest.raises(SystemBackupError, match="новый или пустой каталог"):
            core.restore_system_backup(
                backup, target, passphrase=PASSPHRASE, expected_backup_id=preview.backup_id
            )
        assert (target / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_system_backup_rejects_short_passphrase_before_writing(tmp_path):
    with CoreApplication(tmp_path / "source") as core:
        with pytest.raises(SystemBackupError, match="не менее 12"):
            core.create_system_backup(tmp_path / "system.avicbackup", passphrase="short")
        assert not (tmp_path / "system.avicbackup").exists()
