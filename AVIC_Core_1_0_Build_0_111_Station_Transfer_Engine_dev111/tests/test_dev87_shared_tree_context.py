from fastapi.testclient import TestClient
from avic_core.ui.app import create_ui_app


def test_shared_navigation_removes_duplicate_home_and_fbd_tree(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    home = client.get('/').text
    logic = client.get('/logic').text
    assert '.avic-workspace-home .layout>.left{display:none!important}' in home
    assert '.avic-workspace-logic .core-left{display:none!important}' in logic
    assert 'avic-shared-tree' in home and 'avic-shared-tree' in logic


def test_shared_tree_context_menu_create_and_rename_project_station(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    home = client.get('/').text
    assert 'data-kind="root"' in home
    assert 'data-kind="project"' in home
    assert 'Создать проект' in home and 'Создать станцию' in home
    project = client.post('/api/projects', json={'name':'Проект тест','description':''})
    assert project.status_code == 201
    p = project.json()
    station = client.post('/api/stations', json={'project_id':p['id'],'name':'Станция тест','description':''})
    assert station.status_code == 201
    st = station.json()
    renamed = client.patch(f"/api/stations/{st['id']}", json={'expected_version':st['version'],'name':'Станция новая'})
    assert renamed.status_code == 200
    assert renamed.json()['name'] == 'Станция новая'
