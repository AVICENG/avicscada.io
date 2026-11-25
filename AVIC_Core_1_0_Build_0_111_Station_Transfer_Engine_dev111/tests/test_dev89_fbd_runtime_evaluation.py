import pytest
from avic_core.domain.models import PointQuality
from avic_core.logic_fbd import FBDService
from test_graphics_workbench_dev35 import setup


def test_simulation_returns_per_node_diagnostics_and_station_provenance(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "analog-value"
    point.value = 22.75
    point.quality = PointQuality.GOOD
    _, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)
    service = FBDService(core)
    doc = service.create(station["id"], "DEV89 diagnostics")
    doc = service.add_point_node(doc["id"], point.id)
    node = next(n for n in doc["nodes"] if n["type"] == "POINT_INPUT")
    result = service.simulate(doc["id"])
    detail = result["node_diagnostics"][node["id"]]
    assert detail["status"] == "GOOD"
    assert detail["value"] == 22.75
    assert detail["source"]["kind"] == "station_point"
    assert detail["source"]["point_id"] == point.id
    assert result["runtime_published"] is False
    assert result["field_writes_performed"] is False
    core.close()


def test_simulation_cannot_override_bad_quality_station_point(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "analog-value"
    point.value = 22.75
    point.quality = PointQuality.STALE
    _, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)
    service = FBDService(core)
    doc = service.create(station["id"], "DEV89 quality override")
    doc = service.add_point_node(doc["id"], point.id)
    node = next(n for n in doc["nodes"] if n["type"] == "POINT_INPUT")
    with pytest.raises(ValueError, match="POINT_INPUT недоступен"):
        service.simulate(doc["id"], {node["id"]: 99.0})
    core.close()


def test_simulation_rejects_wrong_virtual_input_type_and_nan(tmp_path):
    core, station, _ = setup(tmp_path)
    service = FBDService(core)
    doc = service.create_fan_demo(station["id"])
    start = next(n for n in doc["nodes"] if n["name"] == "Команда Пуск")
    with pytest.raises(ValueError, match="требуется BOOL"):
        service.simulate(doc["id"], {start["id"]: 1})
    core.close()


def test_simulation_rejects_unknown_input_override(tmp_path):
    core, station, _ = setup(tmp_path)
    service = FBDService(core)
    doc = service.create_fan_demo(station["id"])
    with pytest.raises(ValueError, match="POINT_INPUT"):
        service.simulate(doc["id"], {"not-a-node": True})
    core.close()
