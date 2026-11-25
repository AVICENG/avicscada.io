from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from avic_core.application.container import CoreApplication
from avic_core.domain.models import PhysicalNetwork, ProtocolChannel, DriverInstance, Device, Point, PointQuality
from avic_core.engineering.workflow import EngineeringWorkflowService
from avic_core.graphics import GraphicsService
from avic_core.logic_fbd import FBDService
from avic_core.ui.project_station import ProjectStationService


def setup(tmp_path):
    core = CoreApplication(tmp_path)
    ps = ProjectStationService(core)
    project = ps.create_project('Площадка')
    station = ps.create_station(project['id'], 'Станция 1')
    return core, station


def test_empty_station_reports_all_missing_stages(tmp_path):
    core, station = setup(tmp_path)
    result = EngineeringWorkflowService(core).inspect(station['id'])
    assert result['completed_stages'] == 0
    assert result['completion_percent'] == 0
    assert [x['id'] for x in result['stages']] == ['network', 'drivers', 'points', 'logic', 'graphics']
    assert all(x['next_action'] for x in result['stages'])
    assert result['publish_ready'] is False
    assert result['safety']['field_writes_enabled'] is False


def test_non_station_target_is_rejected(tmp_path):
    core, station = setup(tmp_path)
    project = core.repository.list_records(entity_type='Project')[0]
    with pytest.raises(ValueError, match='не является станцией'):
        EngineeringWorkflowService(core).inspect(project['entity_id'])


def test_network_stage_requires_actual_network_or_channel(tmp_path):
    core, station = setup(tmp_path)
    svc = EngineeringWorkflowService(core)
    core.repository.save(PhysicalNetwork(name='LAN', station_id=station['id'], interface_id='if-1'))
    result = svc.inspect(station['id'])
    assert result['stages'][0]['complete'] is False
    assert result['stages'][0]['counts']['networks'] == 1
    core.repository.save(ProtocolChannel(name='BACnet/IP', station_id=station['id'], network_id=core.repository.list_records(entity_type='PhysicalNetwork')[0]['entity_id']))
    assert svc.inspect(station['id'])['stages'][0]['complete'] is True


def test_driver_stage_detects_missing_driver_reference(tmp_path):
    core, station = setup(tmp_path)
    device = Device(name='Контроллер без драйвера', station_id=station['id'], address='192.0.2.10', protocol='bacnet/ip')
    core.repository.save(device)
    stage = EngineeringWorkflowService(core).inspect(station['id'])['stages'][1]
    assert stage['complete'] is False
    assert stage['issues'][0]['code'] == 'DEVICE_DRIVER_MISSING'


@pytest.mark.parametrize('mode', ['active', 'write', '', 'unknown'])
def test_driver_stage_rejects_non_readonly_or_ambiguous_mode(tmp_path, mode):
    core, station = setup(tmp_path)
    driver = DriverInstance(name='BACnet', station_id=station['id'], package_id='bacnet-ip',
                            configuration={'mode': mode}, state='STOPPED')
    core.repository.save(driver)
    device = Device(name='Контроллер', station_id=station['id'], driver_instance_id=driver.id,
                    address='192.0.2.10', protocol='bacnet/ip')
    core.repository.save(device)
    stage = EngineeringWorkflowService(core).inspect(station['id'])['stages'][1]
    assert stage['complete'] is False
    assert any(x['code'] == 'DRIVER_MODE_UNSAFE' for x in stage['issues'])


def test_driver_stage_rejects_unexpected_driver_state(tmp_path):
    core, station = setup(tmp_path)
    driver = DriverInstance(name='BACnet', station_id=station['id'], package_id='bacnet-ip',
                            configuration={'mode': 'read_only'}, state='RUNNING')
    core.repository.save(driver)
    core.repository.save(Device(name='Контроллер', station_id=station['id'], driver_instance_id=driver.id))
    stage = EngineeringWorkflowService(core).inspect(station['id'])['stages'][1]
    assert stage['complete'] is False
    assert any(x['code'] == 'DRIVER_STATE_UNEXPECTED' for x in stage['issues'])


def test_point_stage_counts_only_points_owned_by_station_devices(tmp_path):
    core, station = setup(tmp_path)
    driver = DriverInstance(name='BACnet', station_id=station['id'], configuration={'mode': 'read_only'})
    core.repository.save(driver)
    device = Device(name='Контроллер', station_id=station['id'], driver_instance_id=driver.id)
    core.repository.save(device)
    point = Point(name='Температура', device_id=device.id, quality=PointQuality.UNCERTAIN)
    core.repository.save(point)
    stage = EngineeringWorkflowService(core).inspect(station['id'])['stages'][2]
    assert stage['complete'] is True and stage['counts']['points'] == 1


def test_full_offline_engineering_chain_is_reported_without_claiming_publish(tmp_path):
    core, station = setup(tmp_path)
    network = PhysicalNetwork(name='LAN', station_id=station['id'], interface_id='eth0')
    core.repository.save(network)
    core.repository.save(ProtocolChannel(name='BACnet/IP', station_id=station['id'], network_id=network.id))
    driver = DriverInstance(name='BACnet/IP', station_id=station['id'], package_id='bacnet-ip',
                            configuration={'mode': 'read_only'}, state='STOPPED')
    core.repository.save(driver)
    device = Device(name='Trend IQ3', station_id=station['id'], driver_instance_id=driver.id,
                    address='192.0.2.20', protocol='bacnet/ip')
    core.repository.save(device)
    core.repository.save(Point(name='Подача', device_id=device.id, quality=PointQuality.UNCERTAIN))
    FBDService(core).create_fan_demo(station['id'])
    GraphicsService(core).create_fan_demo(station['id'])
    result = EngineeringWorkflowService(core).inspect(station['id'])
    assert result['completed_stages'] == 5
    assert result['completion_percent'] == 100
    assert result['engineering_ready'] is True
    assert result['publish_ready'] is False
    assert result['safety']['driver_autostart'] is False
    assert result['safety']['field_writes_enabled'] is False


def test_workflow_http_endpoint_and_unknown_station(tmp_path):
    from avic_core.ui.app import create_ui_app
    client = TestClient(create_ui_app(data_dir=str(tmp_path / 'api')))
    project = client.post('/api/projects', json={'name': 'API'}).json()
    station = client.post('/api/stations', json={'name': 'S1', 'project_id': project['id']}).json()
    response = client.get(f"/api/stations/{station['id']}/engineering-workflow")
    assert response.status_code == 200
    assert response.json()['total_stages'] == 5
    assert 'Инженерный маршрут станции' in client.get('/').text
    assert client.get(f"/api/stations/{uuid4()}/engineering-workflow").status_code == 404
