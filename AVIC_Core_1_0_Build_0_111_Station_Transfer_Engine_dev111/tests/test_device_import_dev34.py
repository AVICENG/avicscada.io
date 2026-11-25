from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def test_device_and_selected_points_import_is_idempotent(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    service = app.state.project_station
    project = service.create_project("P")
    station = service.create_station(project["id"], "S")
    inspection = {
        "address": "10.10.10.2", "network_id": "lan",
        "device_identity": {"device_instance": 1001, "vendor_id": 91,
            "manufacturer": "Trend Control Systems", "model": "IQ3xcite",
            "firmware_revision": "IQ3xcite96 Iss2.00 Apr 23 2008",
            "identity_sources": {"manufacturer": "BACnet Vendor ID 91"}},
        "objects": [
            {"type_name": "analog-output", "instance": 1, "object_name": "D1-Driver 1", "native_identity": "bacnet:object:1:1"},
            {"type_name": "binary-input", "instance": 1, "object_name": "I1-Digital Input 1", "native_identity": "bacnet:object:3:1"},
        ]}
    first = app.state.device_import.import_bacnet(station["id"], inspection,
        selected_native_ids=["bacnet:object:3:1"])
    second = app.state.device_import.import_bacnet(station["id"], inspection,
        selected_native_ids=["bacnet:object:3:1"])
    tree = app.state.device_import.station_tree(station["id"])
    assert first["device_created"] is True
    assert second["device_created"] is False
    assert len(tree["devices"]) == 1
    assert len(tree["devices"][0]["points"]) == 1
    assert tree["devices"][0]["points"][0]["native_identity"] == "bacnet:object:3:1"


def test_workbench_exposes_device_tree_endpoint(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.post("/api/projects", json={"name": "P"}).json()
    station = client.post("/api/stations", json={"project_id": project["id"], "name": "S"}).json()
    response = client.get(f"/api/stations/{station['id']}/device-tree")
    assert response.status_code == 200
    assert response.json() == {"station_id": station["id"], "devices": []}
