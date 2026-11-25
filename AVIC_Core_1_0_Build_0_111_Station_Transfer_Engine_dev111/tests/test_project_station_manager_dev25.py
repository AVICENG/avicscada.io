from fastapi.testclient import TestClient

from avic_core.ui.app import create_ui_app


def test_project_station_create_tree_and_restart_persistence(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'Объект А', 'description': 'BMS'} )
        assert project.status_code == 201
        project_data = project.json()
        assert project_data['version'] == 1
        station = client.post('/api/stations', json={'project_id': project_data['id'], 'name': 'Station 01'})
        assert station.status_code == 201
        station_data = station.json()
        tree = client.get('/api/projects/tree').json()
        assert [x['name'] for x in tree['projects']] == ['Объект А']
        assert tree['stations'][0]['project_id'] == project_data['id']
        assert station_data['project_id'] == project_data['id']
    # A new application instance must read the same persisted Core Repository.
    app2 = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app2) as client:
        tree = client.get('/api/projects/tree').json()
        assert len(tree['projects']) == 1
        assert len(tree['stations']) == 1


def test_project_station_rename_archive_and_restore(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        p = client.post('/api/projects', json={'name': 'Project'}).json()
        renamed = client.patch(f"/api/projects/{p['id']}", json={'expected_version': 1, 'name': 'Renamed'})
        assert renamed.status_code == 200
        assert renamed.json()['name'] == 'Renamed'
        stale = client.patch(f"/api/projects/{p['id']}", json={'expected_version': 1, 'name': 'Stale'})
        assert stale.status_code == 409
        archived = client.patch(f"/api/projects/{p['id']}", json={'expected_version': 2, 'archived': True})
        assert archived.status_code == 200 and archived.json()['archived'] is True
        assert client.get('/api/projects/tree').json()['projects'] == []
        assert len(client.get('/api/projects/tree?include_archived=true').json()['projects']) == 1
        restored = client.patch(f"/api/projects/{p['id']}", json={'expected_version': 3, 'archived': False})
        assert restored.status_code == 200 and restored.json()['archived'] is False


def test_station_requires_existing_active_project(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        missing = client.post('/api/stations', json={'project_id': '00000000-0000-0000-0000-000000000001', 'name': 'Station'})
        assert missing.status_code == 404
        p = client.post('/api/projects', json={'name': 'Project'}).json()
        archived = client.patch(f"/api/projects/{p['id']}", json={'expected_version': 1, 'archived': True}).json()
        denied = client.post('/api/stations', json={'project_id': p['id'], 'name': 'Station'})
        assert denied.status_code == 409


def test_project_station_mutations_are_loopback_guarded(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app, client=('203.0.113.10', 12345)) as client:
        response = client.post('/api/projects', json={'name': 'Remote'})
        assert response.status_code == 403


def test_project_station_changes_are_audited(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        p = client.post('/api/projects', json={'name': 'Audited'}).json()
        client.patch(f"/api/projects/{p['id']}", json={'expected_version': 1, 'name': 'Audited 2'})
    ok, count = app.state.core.audit.verify_chain()
    assert ok is True
    assert count >= 3  # core init + project create + project update
