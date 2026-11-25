from fastapi.testclient import TestClient

from avic_core.ui import app as ui_module
from avic_core.ui.app import create_ui_app


def _project_station(client):
    project = client.post('/api/projects', json={'name': 'Здание А'}).json()
    station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'Station_Main'}).json()
    return project, station


def test_physical_network_and_protocol_channel_are_persisted_in_hierarchy(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_module, 'get_interface', lambda interface_id: {
        'id': 'ethernet-test', 'name': 'Ethernet Test', 'ipv4': '192.0.2.10',
        'subnet_cidr': '192.0.2.0/24', 'kind': 'ethernet', 'mac': '00:11:22:33:44:55'
    })
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _project_station(client)
        network = client.post(f"/api/stations/{station['id']}/networks", json={
            'station_id': station['id'], 'name': 'BMS Ethernet', 'interface_id': 'ethernet-test'
        })
        assert network.status_code == 201, network.text
        channel = client.post(f"/api/network/{network.json()['id']}/channels", json={
            'station_id': station['id'], 'network_id': network.json()['id'],
            'protocol': 'bacnet/ip', 'name': 'BACnet/IP'
        })
        assert channel.status_code == 201, channel.text
        tree = client.get('/api/engineering/tree').json()
        n = tree['projects'][0]['stations'][0]['networks'][0]
        assert n['id'] == network.json()['id']
        assert n['interface_name'] == 'Ethernet Test'
        assert n['channels'][0]['id'] == channel.json()['id']
        assert n['channels'][0]['configured'] is True


def test_network_and_channel_deletion_respects_dependencies(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_module, 'get_interface', lambda interface_id: {
        'id': 'ethernet-test', 'name': 'Ethernet Test', 'ipv4': '192.0.2.10',
        'subnet_cidr': '192.0.2.0/24', 'kind': 'ethernet', 'mac': None
    })
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _project_station(client)
        network = client.post(f"/api/stations/{station['id']}/networks", json={
            'station_id': station['id'], 'name': 'LAN', 'interface_id': 'ethernet-test'
        }).json()
        channel = client.post(f"/api/network/{network['id']}/channels", json={
            'station_id': station['id'], 'network_id': network['id'], 'protocol': 'bacnet/ip', 'name': 'BACnet/IP'
        }).json()
        assert client.delete(f"/api/engineering/entities/{network['id']}").status_code == 409
        assert client.delete(f"/api/engineering/entities/{channel['id']}").status_code == 200
        assert client.delete(f"/api/engineering/entities/{network['id']}").status_code == 200


def test_protocol_channel_rejects_unsupported_protocol(tmp_path, monkeypatch):
    monkeypatch.setattr(ui_module, 'get_interface', lambda interface_id: {
        'id': 'ethernet-test', 'name': 'Ethernet Test', 'ipv4': '192.0.2.10',
        'subnet_cidr': '192.0.2.0/24', 'kind': 'ethernet', 'mac': None
    })
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _project_station(client)
        network = client.post(f"/api/stations/{station['id']}/networks", json={
            'station_id': station['id'], 'name': 'LAN', 'interface_id': 'ethernet-test'
        }).json()
        response = client.post(f"/api/network/{network['id']}/channels", json={
            'station_id': station['id'], 'network_id': network['id'], 'protocol': 'mqtt', 'name': 'MQTT'
        })
        assert response.status_code == 400


def test_workbench_tree_has_compact_right_expanding_navigation_and_context_actions():
    from pathlib import Path
    html = (Path(ui_module.__file__).parent / 'static' / 'index.html').read_text(encoding='utf-8')
    assert 'data-context-action' in html
    assert 'new-network' in html and 'new-channel' in html
    assert 'BACnet Discovery' in html
    assert 'text-overflow:ellipsis' in html
    assert 'height:27px' in html
    assert 'row-reverse' in html
    assert 'networkModal' in html
    assert 'Главное меню AVIC' in html
    assert 'empty-workspace' in html
    assert 'Создать физическую сеть' in html
