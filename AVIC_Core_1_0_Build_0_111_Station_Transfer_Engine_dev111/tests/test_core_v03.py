import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from avic_core.config import ProjectBackupManager, BackupError, MigrationRegistry, MigrationSpec, MigrationError, ConfigurationManager, RevisionConflict, ConfigError
from avic_core.repository import SQLiteRepository, ConcurrencyConflict, EntityNotFound
from avic_core.domain.service import CoreObjectService, DomainIntegrityError
from avic_core.domain.models import Project, Station, Device, Point, PointQuality, Component, Link, Platform


class RepositoryTests(unittest.TestCase):
    def test_optimistic_versioning_and_filtering(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            project = Project("Office")
            self.assertEqual(repo.save(project), 1)
            project.name = "Office HQ"
            self.assertEqual(repo.save(project, expected_version=1), 2)
            with self.assertRaises(ConcurrencyConflict):
                repo.save(project, expected_version=1)
            station = Station("Main", project_id=project.id)
            repo.save(station)
            point = Point("Supply temp", device_id="device-id", unit="°C")
            point.update_value(21.5, PointQuality.GOOD)
            repo.save(point)
            self.assertEqual(len(repo.list_records(entity_type="Station", project_id=project.id)), 1)
            self.assertEqual(repo.get_record(project.id)["version"], 2)

    def test_multi_entity_transaction_rolls_back(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            a, b = Project("A"), Project("B")
            with self.assertRaises(RuntimeError):
                with repo.transaction() as connection:
                    repo.save(a, connection=connection)
                    repo.save(b, connection=connection)
                    raise RuntimeError("abort")
            self.assertEqual(repo.list_records(), [])


    def test_typed_hydration_restores_enum_and_datetime(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            point = Point("Supply", device_id="device-id", unit="°C")
            point.update_value(22.25, PointQuality.GOOD)
            repo.save(point)
            restored, version = repo.get(point.id, Point)
            self.assertEqual(version, 1)
            self.assertEqual(restored.quality, PointQuality.GOOD)
            self.assertEqual(restored.timestamp, point.timestamp)
            self.assertEqual(restored.value, 22.25)

    def test_delete_requires_current_version(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            project = Project("P")
            repo.save(project)
            with self.assertRaises(ConcurrencyConflict):
                repo.delete(project.id, expected_version=2)
            repo.delete(project.id, expected_version=1)
            with self.assertRaises(EntityNotFound):
                repo.get_record(project.id)



class ObjectGraphTests(unittest.TestCase):
    def test_related_objects_commit_as_one_valid_graph(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            service = CoreObjectService(repo)
            platform = Platform("Installation")
            project = Project("Office", platform_id=platform.id)
            station = Station("Main", project_id=project.id)
            driver = __import__("avic_core.domain.models", fromlist=["DriverInstance"]).DriverInstance("Modbus", station_id=station.id)
            device = Device("AHU", station_id=station.id, driver_instance_id=driver.id)
            point = Point("Supply temperature", device_id=device.id, unit="°C")
            component = Component("Supply fan", station_id=station.id, component_type="hvac.fan")
            link = Link("Temperature to display", station_id=station.id, source_object_id=point.id, target_object_id=component.id)
            versions = service.save_graph([platform, project, station, driver, device, point, component, link])
            self.assertEqual(len(versions), 8)
            self.assertEqual(len(repo.list_records()), 8)

    def test_invalid_reference_rejects_entire_graph(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            service = CoreObjectService(repo)
            project = Project("Office")
            station = Station("Main", project_id=project.id)
            bad_device = Device("AHU", station_id="not-a-station")
            with self.assertRaises(DomainIntegrityError):
                service.save_graph([project, station, bad_device])
            self.assertEqual(repo.list_records(), [])

    def test_parent_cannot_be_deleted_while_child_remains(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            service = CoreObjectService(repo)
            project = Project("Office")
            station = Station("Main", project_id=project.id)
            versions = service.save_graph([project, station])
            with self.assertRaises(DomainIntegrityError):
                service.delete_graph({project.id: versions[project.id]})
            self.assertEqual(len(repo.list_records()), 2)
            service.delete_graph({station.id: versions[station.id], project.id: versions[project.id]})
            self.assertEqual(repo.list_records(), [])

    def test_link_cannot_cross_station_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "core.db")
            service = CoreObjectService(repo)
            project = Project("Campus")
            s1, s2 = Station("Building A", project_id=project.id), Station("Building B", project_id=project.id)
            d1, d2 = Device("Device A", station_id=s1.id), Device("Device B", station_id=s2.id)
            p1, p2 = Point("Point A", device_id=d1.id), Point("Point B", device_id=d2.id)
            link = Link("Cross-station", station_id=s1.id, source_object_id=p1.id, target_object_id=p2.id)
            with self.assertRaises(DomainIntegrityError):
                service.save_graph([project, s1, s2, d1, d2, p1, p2, link])
            self.assertEqual(repo.list_records(), [])


class BackupAndMigrationTests(unittest.TestCase):

    def test_configuration_optimistic_revision_and_schema_validation(self):
        with tempfile.TemporaryDirectory() as td:
            manager = ConfigurationManager(td, current_schema=1)
            manager.register_validator(1, lambda payload: (_ for _ in ()).throw(ValueError("points must be a list")) if not isinstance(payload.get("points"), list) else None)
            path = manager.save("station-1", {"points": []})
            with self.assertRaises(RevisionConflict):
                manager.save("station-1", {"points": [1]}, path=path)
            manager.save("station-1", {"points": [1]}, expected_revision=1, revision=2, path=path)
            with self.assertRaises(RevisionConflict):
                manager.save("station-1", {"points": [2]}, expected_revision=1, revision=3, path=path)
            with self.assertRaises(ConfigError):
                manager.save("station-1", {"points": "not-a-list"})

    def test_project_backup_preview_restore_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            root.mkdir()
            (root / "project.json").write_text('{"name":"A"}', encoding="utf-8")
            (root / "station").mkdir()
            (root / "station" / "config.json").write_text('{"points":[]}', encoding="utf-8")
            backup = Path(td) / "backup.zip"
            manager = ProjectBackupManager()
            manager.create_backup(root, backup)
            preview = manager.preview(backup)
            self.assertEqual(preview.file_count, 2)
            (root / "project.json").write_text('{"name":"BROKEN"}', encoding="utf-8")
            manager.restore(backup, root, expected_backup_id=preview.backup_id)
            self.assertEqual((root / "project.json").read_text(encoding="utf-8"), '{"name":"A"}')
            self.assertTrue((Path(td) / "project.pre_restore" / "project.json").exists())

    def test_restore_refuses_changed_backup_after_preview(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "project"
            root.mkdir()
            (root / "a.txt").write_text("a")
            backup = Path(td) / "backup.zip"
            manager = ProjectBackupManager()
            manager.create_backup(root, backup)
            preview = manager.preview(backup)
            backup.write_bytes(b"not a zip")
            with self.assertRaises(BackupError):
                manager.restore(backup, root, expected_backup_id=preview.backup_id)

    def test_migration_preview_returns_diff_without_journaling(self):
        with tempfile.TemporaryDirectory() as td:
            registry = MigrationRegistry(Path(td) / "migrations.db")
            registry.register(MigrationSpec("add-unit", 1, 2, "Add unit", lambda p: {**p, "unit": "°C"}))
            preview = registry.preview({"points": []}, 1, 2)
            self.assertEqual(preview.changed_paths, ("unit",))
            self.assertEqual(preview.before, {"points": []})
            self.assertEqual(preview.after["unit"], "°C")
            self.assertEqual(registry.history("preview-only"), [])

    def test_migration_registry_journals_only_successful_chain(self):
        with tempfile.TemporaryDirectory() as td:
            registry = MigrationRegistry(Path(td) / "migrations.db")
            registry.register(MigrationSpec("add-unit", 1, 2, "Add unit", lambda p: {**p, "unit": "°C"}))
            result = registry.migrate_payload("station-1", {"points": []}, 1, 2)
            self.assertEqual(result["unit"], "°C")
            self.assertEqual(registry.history("station-1")[0]["migration_id"], "add-unit")
            registry.register(MigrationSpec("fail", 2, 3, "Fail", lambda p: 1 / 0))
            with self.assertRaises(MigrationError):
                registry.migrate_payload("station-2", {"points": []}, 1, 3)
            self.assertEqual(registry.history("station-2"), [])


if __name__ == "__main__":
    unittest.main()

class ProjectTransactionCoordinatorTests(unittest.TestCase):
    def setUp(self):
        import tempfile
        from pathlib import Path
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        from avic_core.transactions import ProjectTransactionCoordinator
        self.coordinator = ProjectTransactionCoordinator(self.root / "core.db", self.root / "project")

    def tearDown(self):
        self.temp.cleanup()

    def test_db_and_files_commit_as_one_recoverable_unit(self):
        def mutate(db):
            db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            db.execute("INSERT INTO settings VALUES('mode','engineering')")
        result = self.coordinator.commit(file_updates={"station/config.json": b'{"schema":1}'}, db_mutation=mutate)
        self.assertEqual(result.state, "COMMITTED")
        self.assertEqual((self.root / "project/station/config.json").read_bytes(), b'{"schema":1}')
        self.assertEqual(self.coordinator.pending_count(), 0)

    def test_recovery_replays_db_committed_file_set(self):
        import json, hashlib, uuid
        from pathlib import Path
        txid = str(uuid.uuid4())
        stage = self.coordinator.journal_root / f"tx-{txid}-crash"
        staged = stage / "new" / "station" / "config.json"
        staged.parent.mkdir(parents=True)
        payload = b'{"after_crash":true}'
        staged.write_bytes(payload)
        manifest = {"station/config.json": {"sha256": hashlib.sha256(payload).hexdigest(), "size": len(payload)}}
        with closing(self.coordinator._connect()) as db:
            db.execute("INSERT INTO avic_project_transactions(transaction_id,state,stage_dir,file_manifest) VALUES(?,?,?,?)",
                       (txid, "DB_COMMITTED", str(stage), json.dumps(manifest)))
        recovered = self.coordinator.recover()
        self.assertEqual(recovered[0].state, "RECOVERED")
        self.assertEqual((self.root / "project/station/config.json").read_bytes(), payload)
        self.assertEqual(self.coordinator.pending_count(), 0)

    def test_unsafe_path_rejected_before_database_mutation(self):
        called = []
        with self.assertRaises(Exception):
            self.coordinator.commit(file_updates={"../escape.txt": b"bad"}, db_mutation=lambda db: called.append(True))
        self.assertEqual(called, [])

    def test_concurrent_commits_are_serialized_across_file_and_db(self):
        import threading, time
        from concurrent.futures import ThreadPoolExecutor
        with closing(self.coordinator._connect()) as db:
            db.execute("CREATE TABLE state (id INTEGER PRIMARY KEY CHECK(id=1), value TEXT NOT NULL)")
            db.execute("INSERT INTO state VALUES(1,'initial')")
        original_apply = self.coordinator._apply_files
        first_apply_entered = threading.Event()
        release_first_apply = threading.Event()
        calls = {"count": 0}
        calls_lock = threading.Lock()

        def delayed_apply(stage, manifest):
            with calls_lock:
                calls["count"] += 1
                call_number = calls["count"]
            if call_number == 1:
                first_apply_entered.set()
                release_first_apply.wait(timeout=5)
            return original_apply(stage, manifest)

        self.coordinator._apply_files = delayed_apply
        def run(value):
            def mutate(db):
                db.execute("UPDATE state SET value=? WHERE id=1", (value,))
            return self.coordinator.commit(file_updates={"station/state.txt": value.encode()}, db_mutation=mutate)

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(run, "A")
            self.assertTrue(first_apply_entered.wait(timeout=5))
            second = pool.submit(run, "B")
            time.sleep(0.2)
            self.assertFalse(second.done(), "second commit must wait while first is applying files")
            release_first_apply.set()
            first.result(timeout=5)
            second.result(timeout=5)
        with closing(self.coordinator._connect()) as db:
            db_value = db.execute("SELECT value FROM state WHERE id=1").fetchone()[0]
        file_value = (self.root / "project/station/state.txt").read_text()
        self.assertEqual(db_value, "B")
        self.assertEqual(file_value, "B")
