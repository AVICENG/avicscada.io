from fastapi.testclient import TestClient

from avic_core.ui.app import create_ui_app


def test_unified_engineering_tree_projects_and_stations(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'Площадка А'}).json()
        station = client.post('/api/stations', json={
            'project_id': project['id'], 'name': 'Котельная'
        }).json()

        response = client.get('/api/engineering/tree')
        assert response.status_code == 200
        tree = response.json()
        assert tree['schema_version'] == 1
        assert tree['read_only'] is True
        assert tree['discovery_is_separate'] is True
        assert tree['counts'] == {'projects': 1, 'stations': 1, 'devices': 0, 'points': 0}
        assert tree['projects'][0]['id'] == project['id']
        assert tree['projects'][0]['stations'][0]['id'] == station['id']
        assert tree['projects'][0]['stations'][0]['networks'] == []


def test_unified_engineering_tree_hides_archived_project_by_default(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'Архив'}).json()
        client.patch(f"/api/projects/{project['id']}", json={
            'expected_version': 1, 'archived': True
        })
        assert client.get('/api/engineering/tree').json()['counts']['projects'] == 0
        assert client.get('/api/engineering/tree?include_archived=true').json()['counts']['projects'] == 1
