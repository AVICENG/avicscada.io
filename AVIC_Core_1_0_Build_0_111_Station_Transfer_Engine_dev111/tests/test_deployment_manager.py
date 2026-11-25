from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from avic_core.deployment import DeploymentError, DeploymentManager


def make_project(root: Path) -> Path:
    (root / "station" / "graphics").mkdir(parents=True)
    (root / "station" / "logic").mkdir(parents=True)
    (root / "station" / "logic" / "ahu.fbd.json").write_text('{"nodes":[],"links":[]}', encoding="utf-8")
    (root / "station" / "graphics" / "ahu.svg").write_text('<svg/>', encoding="utf-8")
    (root / "station" / "page.json").write_text('{"graphic":"ahu"}', encoding="utf-8")
    (root / ".env").write_text("PASSWORD=should-not-export", encoding="utf-8")
    (root / "secrets").mkdir()
    (root / "secrets" / "bacnet.json").write_text('{"password":"no"}', encoding="utf-8")
    return root


def test_export_excludes_secrets_and_inspect_reports_manifest(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110", required_modules=["bacnet", "graphics"])
    preview = manager.inspect_package(package, target_core_version="1.0.0.dev110", installed_modules=["bacnet", "graphics"])
    assert preview.compatible is True
    assert preview.file_count == 3
    assert "station/logic/ahu.fbd.json" in preview.files
    assert all("secret" not in f.lower() and not f.startswith(".env") for f in preview.files)
    with zipfile.ZipFile(package) as zf:
        assert ".env" not in zf.namelist()
        manifest = json.loads(zf.read(manager.MANIFEST))
        assert manifest["security"]["secrets_included"] is False
        assert manifest["site_profile"]["included"] is False


def test_stage_import_requires_compatible_target_and_preserves_active_target(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110", required_modules=["bacnet"])
    preview = manager.inspect_package(package)
    target = tmp_path / "target"
    target.mkdir()
    (target / "active.txt").write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(DeploymentError, match="new or empty"):
        manager.stage_import(package, target, expected_package_id=preview.package_id,
            target_core_version="1.0.0.dev110", installed_modules=["bacnet"])
    assert (target / "active.txt").read_text(encoding="utf-8") == "do not overwrite"
    with pytest.raises(DeploymentError, match="not compatible"):
        manager.stage_import(package, tmp_path / "bad-target", expected_package_id=preview.package_id,
            target_core_version="1.0.0.dev999", installed_modules=[])


def test_stage_import_writes_staged_record_and_keeps_site_profile_separate(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110")
    preview = manager.inspect_package(package)
    target = manager.stage_import(package, tmp_path / "imported", expected_package_id=preview.package_id,
        target_core_version="1.0.0.dev110", site_profile={"bacnet_device_id": 12001, "udp_port": 47808})
    assert (target / "station" / "logic" / "ahu.fbd.json").is_file()
    record = json.loads((target / ".avic-deployment.json").read_text(encoding="utf-8"))
    assert record["activation"] == "STAGED_NOT_ACTIVATED"
    assert record["site_profile"]["bacnet_device_id"] == 12001


def test_import_rejects_credentials_in_site_profile(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110")
    preview = manager.inspect_package(package)
    with pytest.raises(DeploymentError, match="SecretStore"):
        manager.stage_import(package, tmp_path / "target", expected_package_id=preview.package_id,
            target_core_version="1.0.0.dev110", site_profile={"bacnet_password": "secret"})


def test_package_detects_tampered_payload(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110")
    tampered = tmp_path / "tampered.avicpkg"
    with zipfile.ZipFile(package) as src, zipfile.ZipFile(tampered, "w") as dst:
        for item in src.infolist():
            data = src.read(item.filename)
            if item.filename.endswith("ahu.fbd.json"):
                data += b" "
            dst.writestr(item, data)
    with pytest.raises(DeploymentError, match="Integrity check failed"):
        manager.inspect_package(tampered)


def test_package_rejects_traversal_entries(tmp_path):
    manager = DeploymentManager()
    package = tmp_path / "evil.avicpkg"
    manifest = {"format":"AVIC_PROJECT_PACKAGE", "format_version":1, "project":{"id":"x","name":"x"},
        "source_core_version":"1.0", "required_modules":[], "security":{"secrets_included":False},
        "file_count":1, "total_bytes":1, "files":{"../evil.txt":{"sha256":"2d711642b726b04401627ca9fbac32f5c8530fb1903cc4db02258717921a4881","size":1}}}
    with zipfile.ZipFile(package, "w") as zf:
        zf.writestr(manager.MANIFEST, json.dumps(manifest))
        zf.writestr("payload/../evil.txt", b"x")
    with pytest.raises(DeploymentError):
        manager.inspect_package(package)


def test_core_application_exposes_deployment_manager(tmp_path):
    from avic_core.application.container import CoreApplication
    core = CoreApplication(tmp_path / "core-data")
    try:
        assert isinstance(core.deployment, DeploymentManager)
    finally:
        core.close()


def test_site_profile_rejects_nested_values(tmp_path):
    manager = DeploymentManager()
    source = make_project(tmp_path / "source")
    package = manager.export_project(source, tmp_path / "ahu.avicpkg", project_id="p-1",
        project_name="AHU project", source_core_version="1.0.0.dev110")
    preview = manager.inspect_package(package)
    with pytest.raises(DeploymentError, match="flat object"):
        manager.stage_import(package, tmp_path / "target", expected_package_id=preview.package_id,
            target_core_version="1.0.0.dev110", site_profile={"network": {"auth": "secret"}})
