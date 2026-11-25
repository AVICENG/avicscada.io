from fastapi.testclient import TestClient

from avic_core.domain.models import Device, DriverInstance, Point, PointQuality
from avic_core.ui import app as ui_module
from avic_core.ui.app import create_ui_app


class FakeBacnetClient:
    def __init__(self, config, policy):
        self.config = config

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read_property(self, address, device_instance, object_type, object_instance,
                      property_id, timeout_seconds=None, array_index=None):
        if property_id == 85:
            return 22.75
        if property_id == 117:
            return 62
        raise AssertionError(f"unexpected property id: {property_id}")


def test_explicit_bacnet_read_updates_point_value_quality_and_timestamp(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_module, "get_interface", lambda interface_id: {
        "name": "Ethernet", "ipv4": "10.10.10.100", "subnet_cidr": "10.10.10.0/24"
    })
    monkeypatch.setattr(ui_module, "BacnetIpClient", FakeBacnetClient)
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'P'}).json()
        station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'S'}).json()
        driver = DriverInstance(name='BACnet/IP', station_id=station['id'], package_id='bacnet-ip',
            configuration={'interface_id': 'eth0', 'network_id': 'lan', 'udp_port': 47808})
        app.state.core.repository.save(driver)
        device = Device(name='Trend IQ3', station_id=station['id'], driver_instance_id=driver.id,
            address='10.10.10.2', protocol='bacnet/ip', network_id='lan',
            native_identity='bacnet:device:1001@10.10.10.2')
        app.state.core.repository.save(device)
        point = Point(name='Supply temperature', device_id=device.id,
            native_identity='bacnet:object:0:1', unit='')
        app.state.core.repository.save(point)

        response = client.post(f'/api/engineering/devices/{device.id}/read-values')
        assert response.status_code == 200
        assert response.json()['write_enabled'] is False
        stored, _ = app.state.core.repository.get(point.id, Point)
        assert stored.value == 22.75
        assert stored.unit == '°C'
        assert stored.quality == PointQuality.GOOD
        assert stored.timestamp is not None


def test_tree_ui_labels_manual_refresh_and_value_badges():
    from pathlib import Path
    html = (Path(ui_module.__file__).parent / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'point-value' in html
    assert 'readSelectedDeviceValues' in html
    assert 'Опросить сейчас' in html
    assert 'Автоопрос · 30 с' in html
    assert 'setInterval' in html
    assert 'COMM_LOST' in html
