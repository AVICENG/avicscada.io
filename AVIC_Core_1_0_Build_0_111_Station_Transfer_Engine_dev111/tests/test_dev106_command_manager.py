import pytest
from fastapi.testclient import TestClient

from avic_core.domain.models import Device, Point, PointDirection, PointQuality
from avic_core.ui import create_ui_app


def setup(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    client = TestClient(app)
    project = app.state.project_station.create_project("Command project")
    station = app.state.project_station.create_station(project["id"], "Command station")
    device = Device(name="Simulated AHU", station_id=station["id"], protocol="simulation", address="SIM-1")
    app.state.core.repository.save(device)
    output = Point(name="Fan command", device_id=device.id, data_type="bool", direction=PointDirection.OUTPUT,
                   quality=PointQuality.UNCERTAIN, native_identity="sim:fan-command")
    permissive = Point(name="Safety permissive", device_id=device.id, data_type="bool", direction=PointDirection.INPUT,
                       quality=PointQuality.UNCERTAIN, value=True, native_identity="sim:permissive")
    app.state.core.repository.save(output); app.state.core.repository.save(permissive)
    return app, client, station, output, permissive


def test_access_lease_command_and_simulated_feedback_do_not_write_point_runtime(tmp_path):
    app, client, station, output, permissive = setup(tmp_path)
    lease = client.post(f"/api/stations/{station['id']}/control/access-lease", json={"duration_seconds": 120})
    assert lease.status_code == 200, lease.text
    app.state.core.point_runtime.publish(permissive.id, True, quality=PointQuality.GOOD)
    payload = {"point_id": output.id, "lease_id": lease.json()["lease_id"], "command": "START",
               "reason": "Проверка вентилятора", "interlock_point_ids": [permissive.id]}
    response = client.post(f"/api/stations/{station['id']}/control/commands", json=payload)
    assert response.status_code == 202, response.text
    command = response.json()
    assert command["state"] == "SIMULATED_ACCEPTED"
    assert command["execution_mode"] == "SIMULATION_ONLY"
    assert command["field_write_performed"] is False
    feedback = client.post(f"/api/control/commands/{command['command_id']}/simulated-feedback", json={"value": True})
    assert feedback.status_code == 200
    assert feedback.json()["state"] == "SIMULATED_CONFIRMED"
    assert feedback.json()["feedback_quality"] == "GOOD"
    assert app.state.core.point_runtime.read(output.id).value is None
    revoked = client.delete(f"/api/control/access-lease/{lease.json()['lease_id']}")
    assert revoked.status_code == 200 and revoked.json()["active"] is False
    app.state.core.close()


def test_command_rejects_bad_or_false_interlock(tmp_path):
    app, client, station, output, permissive = setup(tmp_path)
    lease = client.post(f"/api/stations/{station['id']}/control/access-lease", json={}).json()
    app.state.core.point_runtime.publish(permissive.id, False, quality=PointQuality.GOOD)
    response = client.post(f"/api/stations/{station['id']}/control/commands", json={
        "point_id": output.id, "lease_id": lease["lease_id"], "command": "START",
        "reason": "Interlock test", "interlock_point_ids": [permissive.id]})
    assert response.status_code == 409
    assert "разрешающее условие" in response.json()["detail"]
    app.state.core.close()


def test_command_requires_output_point_and_active_lease(tmp_path):
    app, client, station, output, permissive = setup(tmp_path)
    lease = client.post(f"/api/stations/{station['id']}/control/access-lease", json={}).json()
    response = client.post(f"/api/stations/{station['id']}/control/commands", json={
        "point_id": permissive.id, "lease_id": lease["lease_id"], "command": "START", "reason": "Wrong direction"})
    assert response.status_code == 409
    assert "OUTPUT/INOUT" in response.json()["detail"]
    response = client.post(f"/api/stations/{station['id']}/control/commands", json={
        "point_id": output.id, "lease_id": "00000000-0000-0000-0000-000000000000", "command": "START", "reason": "No lease"})
    assert response.status_code == 409
    app.state.core.close()


def test_interlock_requires_good_quality_and_boolean_output_only(tmp_path):
    app, client, station, output, permissive = setup(tmp_path)
    lease = client.post(f"/api/stations/{station['id']}/control/access-lease", json={}).json()
    response = client.post(f"/api/stations/{station['id']}/control/commands", json={
        "point_id": output.id, "lease_id": lease["lease_id"], "command": "START", "reason": "Bad quality",
        "interlock_point_ids": [permissive.id]})
    assert response.status_code == 409
    assert "требуется GOOD" in response.json()["detail"]
    app.state.core.close()


def test_command_reason_and_lease_duration_validation(tmp_path):
    app, client, station, output, _ = setup(tmp_path)
    assert client.post(f"/api/stations/{station['id']}/control/access-lease", json={"duration_seconds": 901}).status_code == 422
    lease = client.post(f"/api/stations/{station['id']}/control/access-lease", json={}).json()
    response = client.post(f"/api/stations/{station['id']}/control/commands", json={
        "point_id": output.id, "lease_id": lease["lease_id"], "command": "START", "reason": " "})
    assert response.status_code == 409
    assert "причина" in response.json()["detail"]
    app.state.core.close()
