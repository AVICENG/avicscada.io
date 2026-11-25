from fastapi.testclient import TestClient
from avic_core.ui.app import create_ui_app
from avic_core.domain.models import Device, Point

def test_station_delete_preview_and_cascade_is_transactional(tmp_path):
    app=create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project=client.post('/api/projects',json={'name':'P'}).json()
        station=client.post('/api/stations',json={'project_id':project['id'],'name':'S'}).json()
        device=Device(name='Controller',station_id=station['id']); app.state.core.repository.save(device)
        point=Point(name='Temperature',device_id=device.id); app.state.core.repository.save(point)
        preview=client.get(f"/api/engineering/objects/{station['id']}/delete-preview")
        assert preview.status_code==200
        assert preview.json()['counts']['Station']==1
        assert preview.json()['counts']['Device']==1
        assert preview.json()['counts']['Point']==1
        refused=client.delete(f"/api/engineering/objects/{station['id']}")
        assert refused.status_code==409
        deleted=client.delete(f"/api/engineering/objects/{station['id']}?cascade=true")
        assert deleted.status_code==200
        assert app.state.core.repository.list_records(entity_type='Station')==[]
        assert app.state.core.repository.list_records(entity_type='Device')==[]
        assert app.state.core.repository.list_records(entity_type='Point')==[]
        assert app.state.core.repository.get_record(project['id'])['entity_type']=='Project'

def test_project_delete_cascades_all_station_configuration(tmp_path):
    app=create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project=client.post('/api/projects',json={'name':'P'}).json()
        station=client.post('/api/stations',json={'project_id':project['id'],'name':'S'}).json()
        device=Device(name='Controller',station_id=station['id']); app.state.core.repository.save(device)
        Point(name='Temperature',device_id=device.id)
        preview=client.get(f"/api/engineering/objects/{project['id']}/delete-preview").json()
        assert preview['counts']['Project']==1 and preview['counts']['Station']==1
        response=client.delete(f"/api/engineering/objects/{project['id']}?cascade=true")
        assert response.status_code==200
        assert app.state.core.repository.list_records(entity_type='Project')==[]
        assert app.state.core.repository.list_records(entity_type='Station')==[]
