from avic_core.application.container import CoreApplication
from avic_core.ui.project_station import ProjectStationService
from avic_core.ui.device_import import DeviceImportService
from avic_core.graphics import GraphicsService
from avic_core.domain.models import Device, Point, PointQuality


def setup(tmp_path):
    core=CoreApplication(tmp_path)
    ps=ProjectStationService(core)
    project=ps.create_project('P')
    station=ps.create_station(project['id'],'S')
    driver=__import__('avic_core.domain.models',fromlist=['DriverInstance']).DriverInstance(name='BACnet',station_id=station['id'])
    core.repository.save(driver)
    device=Device(name='IQ3',station_id=station['id'],driver_instance_id=driver.id,address='10.10.10.2',protocol='bacnet/ip',native_identity='bacnet:device:1001@10.10.10.2')
    core.repository.save(device)
    point=Point(name='Supply temperature',device_id=device.id,native_identity='bacnet:object:0:1',object_type='analog-input',unit='°C',quality=PointQuality.UNCERTAIN)
    core.repository.save(point)
    return core,station,point


def test_graphic_document_persists_elements_and_stable_point_binding(tmp_path):
    core,station,point=setup(tmp_path); svc=GraphicsService(core)
    doc=svc.create(station['id'],'AHU-01')
    element={'id':'7c56d5a0-02f5-4a5a-99e6-9a9a5a7d1011','name':'Насос P-1','symbol_key':'pump','x':120,'y':90,'width':100,'height':80,'bindings':[{'point_id':point.id,'role':'value'}]}
    saved=svc.save(doc['id'],doc['revision'],[element])
    assert saved['revision']==2
    assert saved['elements'][0]['bindings'][0]['point_id']==point.id
    reopened=svc.get(doc['id'])
    assert reopened['elements'][0]['name']=='Насос P-1'
    assert reopened['elements'][0]['bindings'][0]['point_name']=='Supply temperature'


def test_graphic_binding_rejects_point_from_another_station(tmp_path):
    core,station,point=setup(tmp_path); svc=GraphicsService(core)
    other_project=ProjectStationService(core).create_project('Other')
    other_station=ProjectStationService(core).create_station(other_project['id'],'Other station')
    doc=svc.create(other_station['id'],'Invalid')
    element={'id':'7c56d5a0-02f5-4a5a-99e6-9a9a5a7d1012','name':'Sensor','symbol_key':'sensor','x':0,'y':0,'bindings':[{'point_id':point.id,'role':'value'}]}
    try:
        svc.save(doc['id'],doc['revision'],[element])
        assert False, 'cross-station binding must be rejected'
    except ValueError as exc:
        assert 'another station' in str(exc)


def test_command_binding_is_not_available(tmp_path):
    core,station,point=setup(tmp_path); svc=GraphicsService(core)
    doc=svc.create(station['id'],'No writes')
    element={'id':'7c56d5a0-02f5-4a5a-99e6-9a9a5a7d1013','name':'Valve','symbol_key':'valve','x':0,'y':0,'bindings':[{'point_id':point.id,'role':'command'}]}
    try:
        svc.save(doc['id'],doc['revision'],[element])
        assert False, 'command binding must be rejected'
    except ValueError as exc:
        assert 'not enabled' in str(exc)


def test_graphics_http_workspace_and_api(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    app=create_ui_app(data_dir=str(tmp_path/'http-data'))
    client=TestClient(app)
    assert client.get('/graphics').status_code==200
    project=client.post('/api/projects',json={'name':'HTTP Project'}).json()
    station=client.post('/api/stations',json={'name':'HTTP Station','project_id':project['id']}).json()
    response=client.post(f"/api/stations/{station['id']}/graphics",json={'name':'HTTP Mimic'})
    assert response.status_code==201
    doc=response.json()
    assert doc['station_id']==station['id'] and doc['write_enabled'] is False
    assert client.get(f"/api/graphics/{doc['id']}").status_code==200


def test_graphic_document_optimistic_concurrency_rejects_stale_revision(tmp_path):
    core,station,point=setup(tmp_path); svc=GraphicsService(core)
    doc=svc.create(station['id'],'Concurrency')
    svc.save(doc['id'],doc['revision'],[])
    try:
        svc.save(doc['id'],doc['revision'],[])
        assert False, 'stale revision must be rejected'
    except ValueError as exc:
        assert 'CONCURRENCY_CONFLICT' in str(exc)
