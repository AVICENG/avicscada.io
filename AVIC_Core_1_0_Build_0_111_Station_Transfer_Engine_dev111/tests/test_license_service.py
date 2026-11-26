import pytest
from avic_core.licensing import (
    InstallationLicenseService, LicenseLimitExceeded, LicenseStatus,
)

class Identity:
    def get_host_id(self): return "AVIC-11111111-22222222-33333333-44444444"

class Manager:
    def verify(self, license_file, host_id):
        assert host_id.startswith("AVIC-")
        return LicenseStatus(True, "OK", host_id, "Customer", 2, (), "license-id")

def test_service_uses_installation_host_id(tmp_path):
    service = InstallationLicenseService(tmp_path, Manager(), Identity())
    state = service.inspect("ignored.aviclic")
    assert state.host_id.startswith("AVIC-")
    assert state.status.valid

def test_point_limit_counts_unique_ids_and_allows_existing_id(tmp_path):
    service = InstallationLicenseService(tmp_path, Manager(), Identity())
    status = LicenseStatus(True, "OK", point_limit=2)
    service.assert_can_create_point(status, ["p1", "p2"], "p2")
    with pytest.raises(LicenseLimitExceeded):
        service.assert_can_create_point(status, ["p1", "p2"], "p3")

def test_invalid_license_blocks_new_point_only(tmp_path):
    service = InstallationLicenseService(tmp_path, Manager(), Identity())
    status = LicenseStatus(False, "INVALID_SIGNATURE")
    with pytest.raises(LicenseLimitExceeded):
        service.assert_can_create_point(status, [], "p1")

def test_core_object_service_enforces_limit_atomically(tmp_path):
    from avic_core.repository import SQLiteRepository
    from avic_core.domain.service import CoreObjectService
    from avic_core.domain.models import Platform, Project, Station, Device, Point

    class Gate:
        def inspect(self, license_file):
            from types import SimpleNamespace
            return SimpleNamespace(status=LicenseStatus(True, "OK", point_limit=1))
        def assert_can_create_point(self, status, existing_ids, new_id):
            if new_id not in existing_ids and len(set(existing_ids)) >= status.point_limit:
                raise LicenseLimitExceeded("point limit")

    repo = SQLiteRepository(tmp_path / "core.db")
    service = CoreObjectService(repo, license_service=Gate(), license_file="signed.aviclic")
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    point1 = __import__("avic_core.domain.models", fromlist=["Point"]).Point("P1", device_id=device.id)
    service.save_graph([platform, project, station, device, point1])
    point2 = Point("P2", device_id=device.id)
    with pytest.raises(LicenseLimitExceeded):
        service.save_graph([point2])
    assert len(repo.list_records(entity_type="Point")) == 1


def test_point_usage_separates_project_total_and_licensed_points():
    from avic_core.licensing import summarize_point_usage
    records = [
        {"entity_type": "Point", "entity_id": "physical-1", "payload": {"point_type": "physical"}},
        {"entity_type": "Point", "entity_id": "calc-draft", "payload": {"point_type": "calculated", "published": False, "licensed_active": False}},
        {"entity_type": "Point", "entity_id": "calc-live", "payload": {"point_type": "calculated", "published": True, "licensed_active": True}},
        {"entity_type": "Point", "entity_id": "manual-1", "payload": {"point_type": "manual", "licensed_active": True}},
        {"entity_type": "FbdSignal", "entity_id": "wire-1", "payload": {}},
        {"entity_type": "Point", "entity_id": "physical-1", "payload": {"point_type": "physical"}},
    ]
    result = summarize_point_usage(records, point_limit=3)
    assert result["project_total_points"] == 4
    assert result["licensed_active_points"] == 3
    assert result["remaining_points"] == 0
    assert result["warning"] == "LIMIT_REACHED"
    assert result["by_type"] == {"physical": 1, "calculated": 2, "software": 0, "manual": 1}


def test_feature_entitlement_requires_valid_signed_feature():
    service = InstallationLicenseService(".", Manager(), Identity())
    valid = LicenseStatus(True, "OK", features=("driver.bacnet-ip",))
    service.assert_feature_enabled(valid, "driver.bacnet-ip")
    with pytest.raises(PermissionError, match="не включена"):
        service.assert_feature_enabled(valid, "driver.modbus-tcp")
    invalid = LicenseStatus(False, "LICENSE_EXPIRED", features=("driver.bacnet-ip",))
    with pytest.raises(PermissionError, match="недействительна"):
        service.assert_feature_enabled(invalid, "driver.bacnet-ip")


def test_core_application_wires_license_service_into_point_creation(tmp_path):
    from avic_core.application.container import CoreApplication
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from types import SimpleNamespace

    class Gate:
        def inspect(self, license_file):
            return SimpleNamespace(status=LicenseStatus(True, "OK", point_limit=1))
        def assert_can_create_point(self, status, existing_ids, new_id):
            if new_id not in existing_ids and len(set(existing_ids)) >= status.point_limit:
                raise LicenseLimitExceeded("point limit")

    core = CoreApplication(tmp_path, license_service=Gate(), license_file="signed.aviclic")
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    first = Point("P1", device_id=device.id)
    core.objects.save_graph([platform, project, station, device, first])
    with pytest.raises(LicenseLimitExceeded):
        core.objects.save_graph([Point("P2", device_id=device.id)])
    assert len(core.repository.list_records(entity_type="Point")) == 1
    core.close()


def test_workbench_loads_installation_license_from_explicit_environment(tmp_path, monkeypatch):
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from avic_core.ui.app import create_ui_app

    public_key = tmp_path / "avic-license-public.pem"
    private = Ed25519PrivateKey.generate()
    public_key.write_bytes(private.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ))
    license_file = tmp_path / "customer.aviclic"
    license_file.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("AVIC_LICENSE_PUBLIC_KEY", str(public_key))
    monkeypatch.setenv("AVIC_LICENSE_FILE", str(license_file))
    app = create_ui_app(data_dir=str(tmp_path / "workbench"))
    assert app.state.core.installation_license_service is not None
    assert app.state.core.license_file == license_file
    app.state.core.close()


def test_workbench_rejects_partial_license_configuration(tmp_path, monkeypatch):
    from avic_core.ui.app import create_ui_app
    monkeypatch.setenv("AVIC_LICENSE_PUBLIC_KEY", str(tmp_path / "public.pem"))
    monkeypatch.delenv("AVIC_LICENSE_FILE", raising=False)
    with pytest.raises(RuntimeError, match="задайте одновременно"):
        create_ui_app(data_dir=str(tmp_path / "workbench"))

def test_workbench_license_status_endpoint_is_safe_and_reports_capacity(tmp_path):
    from fastapi.testclient import TestClient
    from types import SimpleNamespace
    from avic_core.application.container import CoreApplication
    from avic_core.ui.app import create_ui_app

    class Entitlements:
        def inspect(self, license_file):
            return SimpleNamespace(
                host_id="AVIC-HOST-TEST",
                status=LicenseStatus(True, "OK", "AVIC-HOST-TEST", "Test Customer",
                                     12, ("driver.bacnet-ip",), "LIC-123"),
            )

    app = create_ui_app(data_dir=str(tmp_path / "api"))
    app.state.core.close()
    core = CoreApplication(tmp_path / "api", license_service=Entitlements(),
                           license_file=tmp_path / "api" / "customer.aviclic")
    app.state.core = core
    payload = TestClient(app).get("/api/licensing/status").json()
    assert payload == {
        "configured": True, "valid": True, "reason": "OK",
        "customer": "Test Customer", "license_id": "LIC-123",
        "host_id": "AVIC-HOST-TEST", "point_limit": 12,
        "licensed_active_points": 0, "remaining_points": 12,
        "features": ["driver.bacnet-ip"],
    }
    assert "private_key" not in payload and "license_file" not in payload
    core.close()


def test_workbench_license_status_reports_unconfigured_development_mode(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    app = create_ui_app(data_dir=str(tmp_path / "api"))
    payload = TestClient(app).get("/api/licensing/status").json()
    assert payload["configured"] is False
    assert payload["valid"] is None
    assert payload["reason"] == "LICENSE_NOT_CONFIGURED"
    assert payload["remaining_points"] is None
    app.state.core.close()

def test_workbench_can_require_license_for_commercial_installation(tmp_path, monkeypatch):
    from avic_core.ui.app import create_ui_app
    monkeypatch.setenv("AVIC_LICENSE_REQUIRED", "true")
    monkeypatch.delenv("AVIC_LICENSE_PUBLIC_KEY", raising=False)
    monkeypatch.delenv("AVIC_LICENSE_FILE", raising=False)
    with pytest.raises(RuntimeError, match="Коммерческий режим требует"):
        create_ui_app(data_dir=str(tmp_path / "commercial"))



def test_inactive_discovered_points_do_not_consume_license_capacity(tmp_path):
    from avic_core.repository import SQLiteRepository
    from avic_core.domain.service import CoreObjectService
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from types import SimpleNamespace

    class Gate:
        def inspect(self, license_file):
            return SimpleNamespace(status=LicenseStatus(True, "OK", point_limit=1))
        def assert_can_create_point(self, status, existing_ids, new_id):
            if new_id not in existing_ids and len(set(existing_ids)) >= status.point_limit:
                raise LicenseLimitExceeded("point limit")

    repo = SQLiteRepository(tmp_path / "draft-points.db")
    service = CoreObjectService(repo, license_service=Gate(), license_file="signed.aviclic")
    platform = Platform("P")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    discovered = Point("Discovered", device_id=device.id, licensed_active=False)
    service.save_graph([platform, project, station, device, discovered])
    active = Point("Active", device_id=device.id)
    service.save_graph([active])
    assert len(repo.list_records(entity_type="Point")) == 2


def test_activating_existing_draft_point_consumes_capacity_atomically(tmp_path):
    from avic_core.repository import SQLiteRepository
    from avic_core.domain.service import CoreObjectService
    from avic_core.domain.models import Platform, Project, Station, Device, Point
    from types import SimpleNamespace

    class Gate:
        def inspect(self, license_file):
            return SimpleNamespace(status=LicenseStatus(True, "OK", point_limit=1))
        def assert_can_create_point(self, status, existing_ids, new_id):
            if new_id not in existing_ids and len(set(existing_ids)) >= status.point_limit:
                raise LicenseLimitExceeded("point limit")

    repo = SQLiteRepository(tmp_path / "activate-point.db")
    service = CoreObjectService(repo, license_service=Gate(), license_file="signed.aviclic")
    platform = Platform("P")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    draft = Point("Draft", device_id=device.id, licensed_active=False)
    service.save_graph([platform, project, station, device, draft])
    active = Point("Active", device_id=device.id)
    service.save_graph([active])
    draft.licensed_active = True
    with pytest.raises(LicenseLimitExceeded):
        service.save_graph([draft], expected_versions={draft.id: 1})
    stored = next(r for r in repo.list_records(entity_type="Point") if r["entity_id"] == draft.id)
    assert stored["payload"]["licensed_active"] is False


def test_calculated_point_requires_publication_and_activation_to_be_licensed():
    from avic_core.licensing import summarize_point_usage
    records = [
        {"entity_type": "Point", "entity_id": "calc-draft",
         "payload": {"point_type": "calculated", "published": False, "licensed_active": True}},
        {"entity_type": "Point", "entity_id": "calc-live",
         "payload": {"point_type": "calculated", "published": True, "licensed_active": True}},
        {"entity_type": "Point", "entity_id": "discovered",
         "payload": {"point_type": "physical", "licensed_active": False}},
    ]
    result = summarize_point_usage(records, point_limit=1)
    assert result["licensed_active_points"] == 1
    assert result["licensed_active_point_ids"] == ["calc-live"]



def test_alarm_rule_configuration_activates_and_releases_its_point_usage(tmp_path):
    from avic_core.repository import SQLiteRepository
    from avic_core.domain.service import CoreObjectService
    from avic_core.domain.models import Platform, Project, Station, Device, Point, Alarm

    repo = SQLiteRepository(tmp_path / "alarm-usage.db")
    service = CoreObjectService(repo)
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    point = Point("High temperature", device_id=device.id, licensed_active=False)
    alarm = Alarm("High temperature alarm", station_id=station.id, source_object_id=point.id)

    versions = service.save_graph([platform, project, station, device, point, alarm])
    stored = repo.get_record(point.id)["payload"]
    assert stored["licensed_active"] is True
    assert stored["licensed_usage"] == [f"alarm:{alarm.id}"]

    alarm.source_object_id = ""
    service.save_graph([alarm], expected_versions={alarm.id: versions[alarm.id]})
    stored = repo.get_record(point.id)["payload"]
    assert stored["licensed_active"] is False
    assert stored["licensed_usage"] == []


def test_deleting_alarm_rule_releases_only_alarm_usage(tmp_path):
    from avic_core.repository import SQLiteRepository
    from avic_core.domain.service import CoreObjectService
    from avic_core.domain.models import Platform, Project, Station, Device, Point, Alarm

    repo = SQLiteRepository(tmp_path / "alarm-delete-usage.db")
    service = CoreObjectService(repo)
    platform = Platform("Platform")
    project = Project("Project", platform_id=platform.id)
    station = Station("Station", project_id=project.id)
    device = Device("Device", station_id=station.id)
    point = Point("Pressure", device_id=device.id, licensed_active=False)
    alarm = Alarm("Low pressure", station_id=station.id, source_object_id=point.id)
    versions = service.save_graph([platform, project, station, device, point, alarm])

    service.delete_graph({alarm.id: versions[alarm.id]})
    stored = repo.get_record(point.id)["payload"]
    assert stored["licensed_active"] is False
    assert stored["licensed_usage"] == []
