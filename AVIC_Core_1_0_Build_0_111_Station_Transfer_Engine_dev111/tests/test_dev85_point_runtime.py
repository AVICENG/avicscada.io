from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from avic_core.domain.models import Device, Point, PointDirection, PointQuality
from avic_core.ui import create_ui_app


def _setup(tmp_path, *, direction=PointDirection.INPUT, data_type="analog-input"):
    app = create_ui_app(data_dir=str(tmp_path))
    client = TestClient(app)
    project = app.state.project_station.create_project("DEV85 Project")
    station = app.state.project_station.create_station(project["id"], "DEV85 Station")
    device = Device(name="Trend Controller", station_id=station["id"], protocol="bacnet/ip",
                    address="192.0.2.10", driver_instance_id="driver-dev85")
    app.state.core.repository.save(device)
    point = Point(name="Supply temperature", device_id=device.id, data_type=data_type,
                  direction=direction, unit="°C", native_identity="bacnet:analog-input:1",
                  source_ref="bacnet:device:1001/analog-input:1", value=None,
                  quality=PointQuality.UNCERTAIN)
    app.state.core.repository.save(point)
    return app, client, station, device, point


def test_point_runtime_publish_read_snapshot_and_subscribe(tmp_path):
    app, _, station, device, point = _setup(tmp_path)
    seen = []
    token = app.state.core.point_runtime.subscribe(point.id, seen.append)
    stamp = datetime.now(timezone.utc)
    live = app.state.core.point_runtime.publish(
        point.id, 22.678, quality=PointQuality.GOOD, timestamp=stamp,
        source_driver_id="driver-dev85",
    )
    assert live.value == 22.678
    assert live.quality == "GOOD"
    assert live.timestamp == stamp
    assert seen == [live]
    assert app.state.core.point_runtime.read(point.id).value == 22.678
    assert app.state.core.point_runtime.snapshot(station_id=station["id"])[0].point_id == point.id
    assert app.state.core.point_runtime.unsubscribe(point.id, token) is True
    app.state.core.close()


def test_point_runtime_rejects_wrong_driver_and_wrong_value_type(tmp_path):
    app, _, _, _, point = _setup(tmp_path)
    with pytest.raises(ValueError, match="не совпадает"):
        app.state.core.point_runtime.publish(point.id, 20.0, source_driver_id="another-driver")
    with pytest.raises(ValueError, match="конечное число"):
        app.state.core.point_runtime.publish(point.id, float("nan"))
    app.state.core.close()


def test_point_runtime_rejects_driver_publish_to_output_point(tmp_path):
    app, _, _, _, point = _setup(tmp_path, direction=PointDirection.OUTPUT, data_type="analog-output")
    with pytest.raises(ValueError, match="OUTPUT-точку"):
        app.state.core.point_runtime.publish(point.id, 1.0)
    app.state.core.close()


def test_point_runtime_api_returns_shared_value(tmp_path):
    app, client, station, _, point = _setup(tmp_path)
    app.state.core.point_runtime.publish(point.id, 19.25, quality="GOOD")
    response = client.get(f"/api/points/{point.id}/runtime")
    assert response.status_code == 200
    assert response.json()["value"] == 19.25
    snapshot = client.get("/api/engineering/points/runtime", params={"station_id": station["id"]})
    assert snapshot.status_code == 200
    assert snapshot.json()["count"] == 1
    app.state.core.close()


def test_fbd_simulation_reads_current_point_runtime_value(tmp_path):
    app, _, station, _, point = _setup(tmp_path)
    app.state.core.point_runtime.publish(point.id, 24.125, quality="GOOD")
    doc = app.state.fbd.create(station["id"], "Live point simulation")
    doc = app.state.fbd.add_point_node(doc["id"], point.id)
    result = app.state.fbd.simulate(doc["id"])
    node = next(n for n in doc["nodes"] if n["type"] == "POINT_INPUT")
    assert result["node_values"][f'{node["id"]}:OUT'] == 24.125
    app.state.core.close()


def test_fbd_simulation_rejects_non_good_live_quality(tmp_path):
    app, _, station, _, point = _setup(tmp_path)
    app.state.core.point_runtime.publish(point.id, 24.125, quality="STALE")
    doc = app.state.fbd.create(station["id"], "Stale point simulation")
    app.state.fbd.add_point_node(doc["id"], point.id)
    with pytest.raises(ValueError, match="качество STALE"):
        app.state.fbd.simulate(doc["id"])
    app.state.core.close()
