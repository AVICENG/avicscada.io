from fastapi.testclient import TestClient
from avic_core.application.container import CoreApplication
from avic_core.ui.project_station import ProjectStationService
from avic_core.graphics import GraphicsService
from avic_core.web_pages import WebPagesService


def setup(tmp_path):
    core = CoreApplication(tmp_path)
    ps = ProjectStationService(core)
    project = ps.create_project('Web project')
    station = ps.create_station(project['id'], 'Main station')
    return core, station


def test_site_folder_page_tree_and_url_are_persistent(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Главный объект', 'site')
    folder = svc.create(station['id'], 'Вентиляция', 'folder', site['id'])
    page = svc.create(station['id'], 'Приточная установка', 'page', folder['id'], 'supply-air')
    assert page['url'] == '/ventilyatsiya/supply-air'
    tree = svc.list_tree(station['id'])
    assert tree['nodes'][0]['children'][0]['children'][0]['id'] == page['id']
    assert WebPagesService(core).get(page['id'])['slug'] == 'supply-air'


def test_duplicate_slug_in_same_folder_is_rejected(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Site', 'site')
    svc.create(station['id'], 'Page 1', 'page', site['id'], 'overview')
    try:
        svc.create(station['id'], 'Page 2', 'page', site['id'], 'overview')
        assert False, 'duplicate slug must be rejected'
    except ValueError as exc:
        assert 'уже существует' in str(exc)


def test_move_prevents_cycles_and_duplicate_routes(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Site', 'site')
    folder = svc.create(station['id'], 'Folder', 'folder', site['id'])
    page = svc.create(station['id'], 'Page', 'page', site['id'], 'same')
    try:
        svc.move(site['id'], folder['id'])
        assert False, 'cycle must be rejected'
    except ValueError as exc:
        assert 'циклическую' in str(exc)
    other = svc.create(station['id'], 'Other', 'page', folder['id'], 'same')
    try:
        svc.move(page['id'], folder['id'])
        assert False, 'duplicate route after move must be rejected'
    except ValueError as exc:
        assert 'уже есть узел' in str(exc)
    svc.update(other['id'], other['revision'], slug='other')
    svc.move(page['id'], folder['id'])
    assert svc.get(page['id'])['url'] == '/folder/same'


def test_page_content_uses_optimistic_revision_and_recursive_delete(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Site', 'site')
    folder = svc.create(station['id'], 'Folder', 'folder', site['id'])
    page = svc.create(station['id'], 'Page', 'page', folder['id'], 'home')
    saved = svc.update(page['id'], page['revision'], html='<h1>AVIC</h1>', css='h1{color:teal}', javascript='console.log("preview")')
    assert saved['revision'] == page['revision'] + 1
    assert saved['html'] == '<h1>AVIC</h1>'
    try:
        svc.update(page['id'], page['revision'], html='stale')
        assert False, 'stale revision must be rejected'
    except ValueError as exc:
        assert 'CONCURRENCY_CONFLICT' in str(exc)
    result = svc.delete(site['id'], site['revision'])
    assert result['deleted_descendants'] == 2
    assert svc.list_tree(station['id'])['flat'] == []


def test_graphic_assignment_requires_same_station(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Site', 'site')
    page = svc.create(station['id'], 'Page', 'page', site['id'], 'home')
    graphic = GraphicsService(core).create(station['id'], 'AHU')
    assigned = svc.assign_graphic(page['id'], graphic['id'], page['revision'])
    assert assigned['graphic_ids'] == [graphic['id']]
    other_project = ProjectStationService(core).create_project('Other')
    other_station = ProjectStationService(core).create_station(other_project['id'], 'Other station')
    other_graphic = GraphicsService(core).create(other_station['id'], 'Other graphic')
    try:
        svc.assign_graphic(page['id'], other_graphic['id'], assigned['revision'])
        assert False, 'cross-station graphic assignment must fail'
    except ValueError as exc:
        assert 'другой станции' in str(exc)


def test_web_pages_http_editor_and_crud(tmp_path):
    from avic_core.ui.app import create_ui_app
    client = TestClient(create_ui_app(data_dir=str(tmp_path / 'http-data')))
    assert client.get('/pages').status_code == 200
    project = client.post('/api/projects', json={'name': 'HTTP Project'}).json()
    station = client.post('/api/stations', json={'name': 'HTTP Station', 'project_id': project['id']}).json()
    site = client.post('/api/web-pages', json={'station_id': station['id'], 'name': 'Site', 'kind': 'site'})
    assert site.status_code == 201
    page = client.post('/api/web-pages', json={'station_id': station['id'], 'name': 'Home', 'kind': 'page', 'parent_id': site.json()['id'], 'slug': 'home'})
    assert page.status_code == 201 and page.json()['url'] == '/home'
    tree = client.get(f"/api/stations/{station['id']}/web-pages")
    assert tree.status_code == 200 and len(tree.json()['flat']) == 2
    saved = client.put(f"/api/web-pages/{page.json()['id']}", json={'expected_revision': 1, 'html': '<h1>hello</h1>'})
    assert saved.status_code == 200 and saved.json()['html'] == '<h1>hello</h1>'


def test_folder_slug_collision_and_root_page_are_rejected(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    try:
        svc.create(station['id'], 'Orphan page', 'page', None, 'orphan')
        assert False, 'a page must belong to a site or folder'
    except ValueError as exc:
        assert 'создайте сайт' in str(exc)
    site = svc.create(station['id'], 'Site', 'site')
    svc.create(station['id'], 'Вентиляция', 'folder', site['id'])
    try:
        svc.create(station['id'], 'Вентиляция 2', 'folder', site['id'], 'ventilyatsiya')
        assert False, 'folder URL collision must be rejected'
    except ValueError as exc:
        assert 'URL уже существует' in str(exc)


def test_page_layout_cannot_reference_unassigned_or_cross_station_graphics(tmp_path):
    core, station = setup(tmp_path)
    svc = WebPagesService(core)
    site = svc.create(station['id'], 'Site', 'site')
    page = svc.create(station['id'], 'Page', 'page', site['id'], 'home')
    try:
        svc.update(page['id'], page['revision'], layout=[{'graphic_id': 'c0000000-0000-4000-8000-000000000000', 'x': 0, 'y': 0}])
        assert False, 'unassigned graphics cannot be placed on page'
    except ValueError as exc:
        assert 'не назначенную странице' in str(exc)
