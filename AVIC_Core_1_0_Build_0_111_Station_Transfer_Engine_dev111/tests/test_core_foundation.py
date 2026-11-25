import json
import tempfile
import unittest
from pathlib import Path

from avic_core.config.manager import ConfigurationManager, NewerSchemaError, ConfigError
from avic_core.runtime.manager import RuntimeManager, RuntimeState, InvalidTransition
from avic_core.security.rbac import AuthorizationService, Principal, Scope, AccessDenied
from avic_core.domain.models import Project, Station, Point, PointQuality
from avic_core.audit.service import AuditService
from avic_core.api.public import CorePublicAPI

class CoreFoundationTests(unittest.TestCase):
    def test_config_roundtrip_snapshot_and_migration(self):
        with tempfile.TemporaryDirectory() as td:
            manager = ConfigurationManager(td, current_schema=2)
            manager.register_migration(1, lambda p: {**p, "migrated": True})
            path = Path(td) / "station.json"
            # Valid version 1 document generated with a v1 manager.
            v1 = ConfigurationManager(td, current_schema=1)
            v1.save("station-1", {"points": []}, path=path)
            loaded = manager.load(path)
            self.assertEqual(loaded.schema_version, 2)
            self.assertTrue(loaded.payload["migrated"])
            snapshots = list((Path(td) / "snapshots").glob("*.json"))
            self.assertTrue(snapshots)
            # Roll back to the version-1 snapshot; source schema is preserved exactly.
            manager.restore_snapshot(snapshots[0], path)
            restored = ConfigurationManager(td, current_schema=2).load(path, migrate=False)
            self.assertEqual(restored.schema_version, 1)

    def test_newer_schema_and_corrupt_checksum_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "future.json"
            future = {"schema_version": 9, "core_api_version": "9", "entity_id": "x", "revision": 1, "payload": {}}
            import hashlib
            future["checksum"] = hashlib.sha256(json.dumps({k:v for k,v in future.items()}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            path.write_text(json.dumps(future), encoding="utf-8")
            before = path.read_bytes()
            with self.assertRaises(NewerSchemaError): ConfigurationManager(td).load(path)
            self.assertEqual(path.read_bytes(), before)
            broken = Path(td) / "broken.json"
            broken.write_text('{"schema_version":1}', encoding="utf-8")
            with self.assertRaises(ConfigError): ConfigurationManager(td).save("broken", {}, path=broken)

    def test_runtime_station_isolation_and_idempotence(self):
        manager = RuntimeManager()
        a = manager.start("A")
        manager.start("A")
        b = manager.start("B")
        manager.stop("A")
        self.assertEqual(a.state, RuntimeState.STOPPED)
        self.assertEqual(b.state, RuntimeState.RUNNING)
        with self.assertRaises(InvalidTransition): a.transition(RuntimeState.RUNNING)

    def test_rbac_scope_and_license_policy(self):
        auth = AuthorizationService()
        user = Principal("u", frozenset({"station.start"}), station_ids=frozenset({"s1"}))
        auth.require(user, "station.start", scope=Scope.STATION, station_id="s1")
        with self.assertRaises(AccessDenied): auth.require(user, "station.start", scope=Scope.STATION, station_id="s2")

    def test_public_api_checks_permissions_per_command(self):
        from avic_core.runtime.manager import RuntimeManager
        runtimes = RuntimeManager()
        runtimes.register("s1")
        api = CorePublicAPI(runtimes, AuthorizationService())
        allowed = Principal("engineer", frozenset({"station.start"}), station_ids=frozenset({"s1"}))
        self.assertEqual(api.start_station(allowed, "s1").state, "RUNNING")
        denied = Principal("viewer", frozenset({"station.read"}), station_ids=frozenset({"s1"}))
        with self.assertRaises(AccessDenied): api.stop_station(denied, "s1")
        self.assertEqual(runtimes.get("s1").state, RuntimeState.RUNNING)

    def test_domain_ids_quality_and_audit(self):
        project = Project("Building")
        station = Station("Main", project_id=project.id)
        point = Point("Supply temperature", device_id="device", unit="°C")
        point.update_value(24.5, PointQuality.GOOD)
        point.quality = PointQuality.STALE
        self.assertEqual(point.value, 24.5)
        self.assertEqual(point.quality, PointQuality.STALE)
        with tempfile.TemporaryDirectory() as td:
            audit = AuditService(Path(td) / "audit.db")
            record = audit.append(actor_id="u", action="station.start", resource_type="station", resource_id=station.id)
            self.assertEqual(record.action, "station.start")

if __name__ == "__main__": unittest.main()

class FoundationHardeningRegressionTests(unittest.TestCase):
    def test_config_rejects_path_traversal_and_non_object_payload(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "root"
            root.mkdir()
            escaped = Path(td) / "escaped.json"
            manager = ConfigurationManager(root)
            with self.assertRaises(ConfigError):
                manager.save("../escaped", {"ok": True})
            with self.assertRaises(ConfigError):
                manager.save("valid", ["not", "an", "object"])
            with self.assertRaises(ConfigError):
                manager.save("valid", {"value": float("nan")})
            self.assertFalse(escaped.exists())

    def test_config_custom_path_must_stay_inside_root(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as outside:
            manager = ConfigurationManager(td)
            with self.assertRaises(ConfigError):
                manager.save("valid", {"ok": True}, path=Path(outside) / "outside.json")

    def test_repository_rejects_entity_type_change_for_existing_id(self):
        from avic_core.repository.sqlite_repository import SQLiteRepository, RepositoryError
        from avic_core.domain.models import Project, Platform
        with tempfile.TemporaryDirectory() as td:
            repo = SQLiteRepository(Path(td) / "repo.db")
            project = Project("Project")
            version = repo.save(project)
            platform = Platform("Platform", id=project.id)
            with self.assertRaises(RepositoryError):
                repo.save(platform, expected_version=version)
            stored, stored_version = repo.get(project.id, Project)
            self.assertEqual(stored.name, "Project")
            self.assertEqual(stored_version, 1)
