from fastapi.testclient import TestClient

from avic_core.domain.models import Device, Point, PointQuality
from avic_core.ui.app import create_ui_app


def _station(client):
    project = client.post('/api/projects', json={'name': 'Площадка DEV38'}).json()
    station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'Котельная'}).json()
    return project, station


def test_entity_inspector_returns_device_and_point_properties(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _station(client)
        device = Device(name='Trend IQ3', station_id=station['id'], address='10.10.10.2',
                        protocol='bacnet/ip', manufacturer='Trend', model='IQ3')
        app.state.core.repository.save(device)
        point = Point(name='Supply Temperature', device_id=device.id, value=23.5,
                      unit='°C', quality=PointQuality.GOOD, native_identity='analogInput:1')
        app.state.core.repository.save(point)

        d = client.get(f'/api/engineering/entities/{device.id}')
        p = client.get(f'/api/engineering/entities/{point.id}')
        assert d.status_code == 200
        assert d.json()['properties']['manufacturer'] == 'Trend'
        assert p.status_code == 200
        assert p.json()['properties']['value'] == 23.5
        assert p.json()['properties']['quality'] == 'GOOD'


def test_device_removal_removes_only_avic_device_and_imported_points(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _station(client)
        device = Device(name='Trend IQ3', station_id=station['id'], address='10.10.10.2', protocol='bacnet/ip')
        app.state.core.repository.save(device)
        point = Point(name='Supply Temperature', device_id=device.id, native_identity='analogInput:1')
        app.state.core.repository.save(point)

        response = client.delete(f'/api/engineering/entities/{device.id}')
        assert response.status_code == 200
        assert response.json()['field_device_unchanged'] is True
        assert app.state.core.repository.list_records(entity_type='Device', station_id=station['id']) == []
        assert app.state.core.repository.list_records(entity_type='Point') == []


def test_station_and_project_cannot_be_deleted_through_entity_endpoint(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project, station = _station(client)
        assert client.delete(f"/api/engineering/entities/{station['id']}").status_code == 400
        assert client.delete(f"/api/engineering/entities/{project['id']}").status_code == 400


def test_point_can_be_removed_without_removing_device(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _station(client)
        device = Device(name='Trend IQ3', station_id=station['id'])
        app.state.core.repository.save(device)
        point = Point(name='Supply Temperature', device_id=device.id)
        app.state.core.repository.save(point)
        response = client.delete(f'/api/engineering/entities/{point.id}')
        assert response.status_code == 200
        assert app.state.core.repository.get_record(device.id)['entity_type'] == 'Device'
        assert app.state.core.repository.list_records(entity_type='Point') == []


def test_engineering_tree_projects_saved_point_value_and_quality(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        _, station = _station(client)
        device = Device(name='Trend IQ3', station_id=station['id'], address='10.10.10.2', protocol='bacnet/ip')
        app.state.core.repository.save(device)
        point = Point(name='Supply Temperature', device_id=device.id, value=22.75,
                      unit='°C', quality=PointQuality.GOOD, native_identity='analogInput:1')
        app.state.core.repository.save(point)
        tree = client.get('/api/engineering/tree').json()
        point_node = tree['projects'][0]['stations'][0]['networks'][0]['channels'][0]['devices'][0]['points'][0]
        assert point_node['value'] == 22.75
        assert point_node['unit'] == '°C'
        assert point_node['quality'] == 'GOOD'
