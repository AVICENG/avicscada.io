from fastapi.testclient import TestClient

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV84 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV84 Station")


def test_shared_left_navigation_is_present_on_every_workspace(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    for route in ("/", "/logic", "/graphics", "/repository"):
        response = client.get(route)
        assert response.status_code == 200
        html = response.text
        assert "avic-global-rail" in html
        assert 'aria-label="Общая навигация AVIC"' in html
        assert 'href="/logic"' in html or 'data-rail-page="logic"' in html
        assert 'href="/repository"' in html or 'data-rail-page="repository"' in html


def test_engineering_point_catalog_exposes_protocol_and_native_identity_for_fbd(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    device = Device(
        name="AHU Trend Controller", station_id=station["id"], protocol="bacnet/ip",
        address="192.0.2.20", native_identity="bacnet:device:1001@192.0.2.20",
        manufacturer="Trend", model="IQ4",
    )
    client.app.state.core.repository.save(device)
    point = Point(
        name="Supply Air Temperature", device_id=device.id, data_type="analog-input",
        unit="°C", native_identity="bacnet:object:0:1", source_ref="bacnet:object:0:1",
        object_type="analog-input", value=22.678, quality=PointQuality.GOOD,
    )
    client.app.state.core.repository.save(point)

    response = client.get("/api/engineering/points", params={"station_id": station["id"]})
    assert response.status_code == 200
    item = response.json()["points"][0]
    assert item["id"] == point.id
    assert item["protocol"] == "bacnet/ip"
    assert item["device_name"] == "AHU Trend Controller"
    assert item["device_address"] == "192.0.2.20"
    assert item["native_identity"] == "bacnet:object:0:1"
    assert item["object_type"] == "analog-input"


def test_fbd_external_binding_keeps_source_identity_and_display_precision_contract():
    from pathlib import Path
    html = Path("avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "function pointBindingForFbd(p)" in html
    assert "schema:'avic.external-point-binding'" in html
    assert "nativeIdentity:p.nativeIdentity" in html
    assert "function formatFbdDisplayValue(v,precision=2)" in html
    assert "v.toFixed" in html
