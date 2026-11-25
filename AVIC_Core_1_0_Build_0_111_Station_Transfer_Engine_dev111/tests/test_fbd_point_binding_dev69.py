import pytest
from avic_core.logic_fbd import FBDService
from avic_core.domain.models import PointQuality
from test_graphics_workbench_dev35 import setup


def test_station_point_can_be_drag_drop_source_in_fbd(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "analog-value"
    point.value = 21.5
    point.quality = PointQuality.GOOD
    row, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Point source")
    added = svc.add_point_node(doc["id"], point.id, x=180, y=120)
    node = next(n for n in added["nodes"] if n["type"] == "POINT_INPUT")
    assert node["params"]["point_id"] == point.id
    assert node["params"]["data_type"] == "float"
    assert node["x"] == 180 and node["y"] == 120


def test_station_point_source_rejects_cross_station_point(tmp_path):
    core, station, point = setup(tmp_path)
    from avic_core.ui.project_station import ProjectStationService
    ps = ProjectStationService(core)
    other_project = ps.create_project("Other")
    other = ps.create_station(other_project["id"], "Other station")
    svc = FBDService(core)
    doc = svc.create(other["id"], "Wrong station")
    with pytest.raises(ValueError, match="не принадлежит станции"):
        svc.add_point_node(doc["id"], point.id)


def test_point_source_blocks_simulation_when_quality_not_good(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "analog-value"
    point.value = 18.0
    point.quality = PointQuality.UNCERTAIN
    _, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Quality gate")
    doc = svc.add_point_node(doc["id"], point.id)
    with pytest.raises(ValueError, match="качество UNCERTAIN"):
        svc.simulate(doc["id"])


def test_station_point_fbd_http_endpoint(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    from avic_core.ui.project_station import ProjectStationService
    from avic_core.domain.models import Device, Point, PointQuality
    app = create_ui_app(data_dir=str(tmp_path / "http"))
    client = TestClient(app)
    ps = ProjectStationService(app.state.core)
    project = ps.create_project("HTTP")
    station = ps.create_station(project["id"], "Station")
    device = Device(name="IQ3", station_id=station["id"], address="10.0.0.2", protocol="bacnet/ip")
    app.state.core.repository.save(device)
    point = Point(name="Outside temperature", device_id=device.id, data_type="float",
                  value=12.5, quality=PointQuality.GOOD, unit="°C")
    app.state.core.repository.save(point)
    created = client.post(f"/api/stations/{station['id']}/fbd", json={"name": "HTTP strategy"})
    assert created.status_code == 201, created.text
    doc = created.json()
    response = client.post(f"/api/fbd/{doc['id']}/points/{point.id}", json={"page_id": doc["pages"][0]["id"], "x": 160, "y": 90})
    assert response.status_code == 201, response.text
    assert response.json()["nodes"][0]["params"]["point_id"] == point.id


def test_point_block_uses_physical_point_type_for_link_validation(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "binary-input"
    point.value = True
    point.quality = PointQuality.GOOD
    _, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)
    svc = FBDService(core)
    doc = svc.create(station["id"], "Typed physical point")
    doc = svc.add_point_node(doc["id"], point.id)
    source = next(n for n in doc["nodes"] if n["type"] == "POINT_INPUT")
    target_id = "f3b0e1a8-4b21-4e23-8a0b-9b3a1f0a0001"
    with pytest.raises(ValueError, match="Несовместимые типы портов"):
        svc.save(doc["id"], doc["revision"], doc["nodes"] + [
            {"id": target_id, "type": "ADD", "name": "Wrong numeric target"}
        ], [{"source_node_id": source["id"], "source_port": "OUT",
             "target_node_id": target_id, "target_port": "A"}])
