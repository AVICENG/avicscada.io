from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _create_station(app, project_name="Project", station_name="AHU-01"):
    project = app.state.project_station.create_project(project_name)
    station = app.state.project_station.create_station(project["id"], station_name)
    return project, station


def test_station_transfer_workbench_safe_clone_flow(tmp_path):
    source_app = create_ui_app(data_dir=str(tmp_path / "source"))
    target_app = create_ui_app(data_dir=str(tmp_path / "target"))
    _, source_station = _create_station(source_app, "Source Project", "AHU-01")
    target_project, _ = _create_station(target_app, "Target Project", "Existing")
    try:
        with TestClient(source_app) as source_client, TestClient(target_app) as target_client:
            page = target_client.get("/station-transfer")
            assert page.status_code == 200
            assert "Подпись издателя не проверена" in page.text
            assert "Подтвердить и выполнить" in page.text
            catalog = target_client.get("/api/station-transfer/catalog").json()
            assert any(row["id"] == target_project["id"] for row in catalog["projects"])

            exported = source_client.post("/api/station-transfer/export", json={
                "station_id": source_station["id"]})
            assert exported.status_code == 200
            assert exported.headers["content-type"].startswith("application/vnd.avic.station+zip")

            inspected = target_client.post("/api/station-transfer/inspect",
                content=exported.content,
                headers={"content-type": "application/octet-stream"})
            assert inspected.status_code == 200
            preview = inspected.json()
            assert preview["compatible"] is True
            assert preview["trust_status"] == "UNSIGNED_UNVERIFIED"
            assert preview["requires_unsigned_acknowledgement"] is True

            refused = target_client.post("/api/station-transfer/stage", json={
                "upload_token": preview["upload_token"], "package_id": preview["package_id"],
                "acknowledge_unsigned": False})
            assert refused.status_code == 400

            staged = target_client.post("/api/station-transfer/stage", json={
                "upload_token": preview["upload_token"], "package_id": preview["package_id"],
                "acknowledge_unsigned": True})
            assert staged.status_code == 200
            assert staged.json()["state"] == "STAGED_NOT_ACTIVATED"

            bad_confirmation = target_client.post("/api/station-transfer/commit", json={
                "stage_token": staged.json()["stage_token"], "package_id": preview["package_id"],
                "target_project_id": target_project["id"], "mode": "clone",
                "clone_station_name": "AHU Clone", "confirmation": "IMPORT"})
            assert bad_confirmation.status_code == 400

            committed = target_client.post("/api/station-transfer/commit", json={
                "stage_token": staged.json()["stage_token"], "package_id": preview["package_id"],
                "target_project_id": target_project["id"], "mode": "clone",
                "clone_station_name": "AHU Clone", "confirmation": "CLONE"})
            assert committed.status_code == 200
            result = committed.json()
            assert result["cloned"] is True
            assert result["activation"] == "NOT_ACTIVATED"
            assert target_app.state.core.repository.get_record(result["station_id"])["name"] == "AHU Clone"
            assert target_app.state.core.runtime.get(result["station_id"]).state.value == "STOPPED"
            assert result["site_binding_required"] is True
    finally:
        source_app.state.core.close()
        target_app.state.core.close()


def test_station_transfer_export_refuses_running_station(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "app"))
    _, station = _create_station(app)
    try:
        app.state.core.start_station(station["id"])
        with TestClient(app) as client:
            response = client.post("/api/station-transfer/export", json={
                "station_id": station["id"]})
            assert response.status_code == 409
            assert "STOPPED" in response.json()["detail"]
    finally:
        app.state.core.close()


def test_station_transfer_rejects_invalid_or_empty_upload(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "app"))
    try:
        with TestClient(app) as client:
            empty = client.post("/api/station-transfer/inspect", content=b"",
                headers={"content-type": "application/octet-stream"})
            invalid = client.post("/api/station-transfer/inspect", content=b"not a zip",
                headers={"content-type": "application/octet-stream"})
            assert empty.status_code == 400
            assert invalid.status_code == 400
            assert app.state.station_transfer_tokens == {}
    finally:
        app.state.core.close()
