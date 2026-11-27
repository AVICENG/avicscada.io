import pytest

from avic_core.application.container import CoreApplication
from avic_core.domain.models import Device, Point, PointQuality
from avic_core.ui.project_station import ProjectStationService


def _two_stations(tmp_path):
    core = CoreApplication(tmp_path)
    projects = ProjectStationService(core)
    project_a = projects.create_project("History A")
    station_a = projects.create_station(project_a["id"], "Station A")
    project_b = projects.create_project("History B")
    station_b = projects.create_station(project_b["id"], "Station B")
    device = Device(
        name="Controller A", station_id=station_a["id"],
        protocol="bacnet/ip", address="192.0.2.10:47808",
    )
    core.repository.save(device)
    point = Point(
        name="Temperature A", device_id=device.id, data_type="float",
        value=21.5, quality=PointQuality.GOOD,
    )
    core.repository.save(point)
    return core, station_a, station_b, point


def test_history_append_rejects_cross_station_point_and_accepts_owner_station(tmp_path):
    core, station_a, station_b, point = _two_stations(tmp_path)
    with pytest.raises(ValueError, match="Точка принадлежит другой станции"):
        core.history.append(station_b["id"], point.id, 99.0)

    sample = core.history.append(station_a["id"], point.id, 21.5)
    assert sample.station_id == station_a["id"]
    assert sample.point_id == point.id
    assert sample.quality == "GOOD"
    assert core.history.query(station_a["id"], point.id) == [sample]
    with pytest.raises(ValueError, match="Точка принадлежит другой станции"):
        core.history.query(station_b["id"], point.id)
    core.close()


def test_history_append_rejects_non_point_entity(tmp_path):
    core, station_a, _, _ = _two_stations(tmp_path)
    with pytest.raises(ValueError, match="только инженерные точки"):
        core.history.append(station_a["id"], station_a["id"], 1)
    core.close()
