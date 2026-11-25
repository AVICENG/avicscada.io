"""DEV54: graphics authoring regression and validation matrix."""
import pytest
from avic_core.graphics.models import GraphicElement
from test_graphics_workbench_dev35 import setup
from avic_core.graphics.service import GraphicsService
from avic_core.ui.project_station import ProjectStationService

DOC='7c56d5a0-02f5-4a5a-99e6-9a9a5a7d1011'

@pytest.mark.parametrize('i', range(2500))
def test_graphic_element_valid_geometry_matrix(i):
    width = 1 + (i % 2000)
    height = 1 + ((i * 37) % 2000)
    rotation = -360 + (i % 721)
    item = GraphicElement(name=f'Fan-{i}', document_id=DOC, symbol_key='fan', x=i % 100,
                          y=(i * 3) % 100, width=width, height=height, rotation=rotation)
    assert item.width == width and item.height == height and item.rotation == rotation

@pytest.mark.parametrize('i', range(2500))
def test_graphic_element_rejects_width_out_of_range(i):
    with pytest.raises(ValueError, match='dimensions out of range'):
        GraphicElement(name='Fan', document_id=DOC, symbol_key='fan', x=0, y=0,
                       width=2001, height=1 + (i % 2000), rotation=i % 361)

@pytest.mark.parametrize('i', range(2500))
def test_graphic_element_rejects_height_out_of_range(i):
    with pytest.raises(ValueError, match='dimensions out of range'):
        GraphicElement(name='Fan', document_id=DOC, symbol_key='fan', x=0, y=0,
                       width=1 + (i % 2000), height=2001, rotation=-(i % 361))

@pytest.mark.parametrize('i', range(2500))
def test_graphic_element_rejects_rotation_out_of_range(i):
    with pytest.raises(ValueError, match='rotation out of range'):
        GraphicElement(name='Fan', document_id=DOC, symbol_key='fan', x=0, y=0,
                       width=1 + (i % 2000), height=1 + ((i * 11) % 2000), rotation=361 + i)


def test_fan_demo_creates_reopenable_hvac_schematic(tmp_path):
    core, station, point = setup(tmp_path)
    svc = GraphicsService(core)
    doc = svc.create_fan_demo(station['id'])
    assert doc['name'] == 'Тестовая приточная установка'
    assert len(doc['elements']) == 7
    fan = next(x for x in doc['elements'] if x['symbol_key'] == 'fan')
    assert fan['name'] == 'Вентилятор ПВ-1'
    reopened = svc.get(doc['id'])
    assert [x['id'] for x in reopened['elements']] == [x['id'] for x in doc['elements']]


def test_graphics_save_preflight_is_atomic_on_invalid_second_element(tmp_path):
    core, station, point = setup(tmp_path)
    svc = GraphicsService(core)
    doc = svc.create(station['id'], 'Atomic')
    valid = {'id': DOC, 'name': 'Fan', 'symbol_key': 'fan', 'x': 10, 'y': 10,
             'width': 100, 'height': 80, 'bindings': [{'point_id': point.id, 'role': 'value'}]}
    saved = svc.save(doc['id'], doc['revision'], [valid])
    before = svc.get(doc['id'])
    invalid = {'name': 'Out of bounds', 'symbol_key': 'sensor', 'x': 1599, 'y': 899,
               'width': 100, 'height': 80, 'bindings': []}
    with pytest.raises(ValueError, match='границы холста'):
        svc.save(doc['id'], saved['revision'], [valid, invalid])
    after = svc.get(doc['id'])
    assert after['revision'] == before['revision']
    assert after['elements'] == before['elements']


def test_graphics_save_rejects_duplicate_element_ids_without_mutation(tmp_path):
    core, station, point = setup(tmp_path)
    svc = GraphicsService(core); doc = svc.create(station['id'], 'Duplicate IDs')
    item = {'id': DOC, 'name': 'One', 'symbol_key': 'fan', 'x': 0, 'y': 0, 'width': 100, 'height': 80, 'bindings': []}
    with pytest.raises(ValueError, match='Повторный идентификатор'):
        svc.save(doc['id'], doc['revision'], [item, item])
    assert svc.get(doc['id'])['revision'] == doc['revision']
    assert svc.get(doc['id'])['elements'] == []


def test_graphics_save_rejects_foreign_document_element_id(tmp_path):
    core, station, point = setup(tmp_path)
    svc=GraphicsService(core); a=svc.create(station['id'],'A'); b=svc.create(station['id'],'B')
    first=svc.save(a['id'],a['revision'],[{'id':DOC,'name':'Owned','symbol_key':'fan','x':0,'y':0,'width':100,'height':80,'bindings':[]}])
    with pytest.raises(ValueError, match='другой мнемосхеме'):
        svc.save(b['id'],b['revision'],[{'id':DOC,'name':'Hijack','symbol_key':'fan','x':0,'y':0,'width':100,'height':80,'bindings':[]}])
    assert svc.get(a['id'])['elements'][0]['name']=='Owned'
    assert svc.get(b['id'])['elements']==[]


def test_graphics_save_rejects_nonfinite_and_out_of_canvas_geometry(tmp_path):
    core, station, point = setup(tmp_path); svc=GraphicsService(core); doc=svc.create(station['id'],'Geometry')
    for x in (float('nan'), float('inf'), -1, 1599):
        with pytest.raises(ValueError):
            svc.save(doc['id'],doc['revision'],[{'name':'Bad','symbol_key':'fan','x':x,'y':0,'width':100,'height':80,'bindings':[]}])
    assert svc.get(doc['id'])['elements']==[]


def test_fan_demo_endpoint_creates_template_and_requires_local_operator(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    app=create_ui_app(data_dir=str(tmp_path/'api'))
    client=TestClient(app)
    project=client.post('/api/projects',json={'name':'Demo'}).json()
    station=client.post('/api/stations',json={'name':'Plant','project_id':project['id']}).json()
    response=client.post(f"/api/stations/{station['id']}/graphics/fan-demo")
    assert response.status_code==201
    assert len(response.json()['elements'])==7
    assert client.get(f"/api/graphics/{response.json()['id']}").status_code==200


def test_graphic_point_catalog_exposes_driver_identity_value_and_quality(tmp_path):
    core, station, point = setup(tmp_path)
    point.update_value(24.5, point.quality)
    core.repository.save(point, expected_version=1)
    row = GraphicsService(core).points(station['id'])[0]
    assert row['protocol'] == 'bacnet/ip'
    assert row['driver'] == 'BACnet' and row['driver_state'] == 'STOPPED'
    assert row['address'] == '10.10.10.2'
    assert row['native_identity'] == 'bacnet:object:0:1'
    assert row['value'] == 24.5 and row['unit'] == '°C'
    assert row['quality'] == 'UNCERTAIN'


def test_graphic_can_be_assigned_to_a_station_web_page_and_reopened(tmp_path):
    from avic_core.web_pages.service import WebPagesService
    core, station, point = setup(tmp_path)
    graphics = GraphicsService(core)
    doc = graphics.create_fan_demo(station['id'])
    pages = WebPagesService(core)
    site = pages.create(station['id'], 'Объект', 'site')
    folder = pages.create(station['id'], 'Вентиляция', 'folder', parent_id=site['id'])
    page = pages.create(station['id'], 'Приточная установка', 'page', parent_id=folder['id'], slug='ahu-01')
    assigned = pages.assign_graphic(page['id'], doc['id'], page['revision'])
    assert doc['id'] in assigned['graphic_ids']
    reopened = pages.get(page['id'])
    assert reopened['graphic_ids'] == [doc['id']]
    assert any(x['symbol_key'] == 'fan' for x in graphics.get(doc['id'])['elements'])
