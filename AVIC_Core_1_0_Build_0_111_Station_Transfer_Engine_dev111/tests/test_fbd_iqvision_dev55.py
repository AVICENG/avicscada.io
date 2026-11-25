"""DEV55 FBD graph model, persistence, type safety and simulation matrix."""
import math
import pytest
from uuid import uuid4
from avic_core.logic_fbd import LogicNode, FBDService
from avic_core.graphics.service import GraphicsService
from test_graphics_workbench_dev35 import setup

DOC='2c7f5b60-8df5-46af-b1a5-0e1f9d0c7a10'

@pytest.mark.parametrize('i', range(5000))
def test_fbd_node_accepts_valid_canvas_coordinates(i):
    x=(i*7919)%10001; y=(i*3571+17)%10001
    node=LogicNode(DOC,'AND',f'AND-{i}',x=x,y=y)
    assert node.x==x and node.y==y

@pytest.mark.parametrize('i', range(2500))
def test_fbd_node_rejects_negative_x_coordinate(i):
    with pytest.raises(ValueError,match='Координаты'):
        LogicNode(DOC,'AND',f'bad-x-{i}',x=-1-(i%10001),y=i%10001)

@pytest.mark.parametrize('i', range(2500))
def test_fbd_node_rejects_x_coordinate_above_canvas(i):
    with pytest.raises(ValueError,match='Координаты'):
        LogicNode(DOC,'AND',f'bad-x2-{i}',x=10001+i,y=i%10001)

@pytest.mark.parametrize('i', range(1250))
def test_fbd_node_rejects_negative_y_coordinate(i):
    with pytest.raises(ValueError,match='Координаты'):
        LogicNode(DOC,'AND',f'bad-y-{i}',x=i%10001,y=-1-i)

@pytest.mark.parametrize('i', range(1250))
def test_fbd_node_rejects_y_coordinate_above_canvas(i):
    with pytest.raises(ValueError,match='Координаты'):
        LogicNode(DOC,'AND',f'bad-y2-{i}',x=i%10001,y=10001+i)


def test_fan_fbd_demo_persists_typed_links_and_simulates_permissive(tmp_path):
    core,station,point=setup(tmp_path); svc=FBDService(core)
    doc=svc.create_fan_demo(station['id'])
    assert len(doc['nodes'])==4 and len(doc['links'])==3
    result=svc.simulate(doc['id'])
    assert result['outputs']=={'Вентилятор: RUN':True}
    assert result['field_writes_performed'] is False
    reopened=svc.get(doc['id'])
    assert reopened['nodes']==doc['nodes'] and reopened['links']==doc['links']


def test_fan_fbd_demo_blocks_start_when_safety_input_false(tmp_path):
    core,station,point=setup(tmp_path); svc=FBDService(core); doc=svc.create_fan_demo(station['id'])
    safety=next(n for n in doc['nodes'] if n['name']=='Защита исправна')
    safety['params']['value']=False
    saved=svc.save(doc['id'],doc['revision'],doc['nodes'],doc['links'])
    assert svc.simulate(saved['id'])['outputs']['Вентилятор: RUN'] is False


def test_fbd_rejects_incompatible_port_types_without_mutation(tmp_path):
    core,station,point=setup(tmp_path); svc=FBDService(core); doc=svc.create(station['id'],'Type check')
    nodes=[{'type':'FLOAT_INPUT','name':'Аналог','params':{'value':2.0}}, {'type':'AND','name':'И'}]
    links=[{'source_node_id':nodes[0].get('id') or str(uuid4()),'source_port':'OUT','target_node_id':nodes[1].get('id') or str(uuid4()),'target_port':'A'}]
    # Give explicit stable ids so the attempted edge resolves to actual nodes.
    nodes[0]['id']=str(uuid4());nodes[1]['id']=str(uuid4())
    links[0]['source_node_id']=nodes[0]['id'];links[0]['target_node_id']=nodes[1]['id']
    with pytest.raises(ValueError,match='Несовместимые типы'):
        svc.save(doc['id'],doc['revision'],nodes,links)
    assert svc.get(doc['id'])['nodes']==[] and svc.get(doc['id'])['revision']==doc['revision']


def test_fbd_rejects_duplicate_target_port(tmp_path):
    core,station,point=setup(tmp_path);svc=FBDService(core);doc=svc.create(station['id'],'Duplicate input')
    a,b,c=[str(uuid4()) for _ in range(3)]
    nodes=[{'id':a,'type':'BOOL_INPUT','name':'A'},{'id':b,'type':'BOOL_INPUT','name':'B'},{'id':c,'type':'AND','name':'AND'}]
    links=[{'source_node_id':a,'source_port':'OUT','target_node_id':c,'target_port':'A'},{'source_node_id':b,'source_port':'OUT','target_node_id':c,'target_port':'A'}]
    with pytest.raises(ValueError,match='уже занят'):
        svc.save(doc['id'],doc['revision'],nodes,links)


def test_fbd_rejects_combinational_cycle(tmp_path):
    core,station,point=setup(tmp_path);svc=FBDService(core);doc=svc.create(station['id'],'Cycle')
    a,b=str(uuid4()),str(uuid4())
    nodes=[{'id':a,'type':'NOT','name':'A'},{'id':b,'type':'NOT','name':'B'}]
    links=[{'source_node_id':a,'source_port':'OUT','target_node_id':b,'target_port':'IN'},{'source_node_id':b,'source_port':'OUT','target_node_id':a,'target_port':'IN'}]
    with pytest.raises(ValueError,match='Циклическая'):
        svc.save(doc['id'],doc['revision'],nodes,links)


def test_fbd_revision_conflict_does_not_overwrite(tmp_path):
    core,station,point=setup(tmp_path);svc=FBDService(core);doc=svc.create(station['id'],'Revision')
    saved=svc.save(doc['id'],doc['revision'],[{'type':'BOOL_INPUT','name':'Input','params':{'value':True}}],[])
    with pytest.raises(ValueError,match='CONCURRENCY_CONFLICT'):
        svc.save(doc['id'],doc['revision'],[],[])
    assert svc.get(doc['id'])['revision']==saved['revision']


def test_fbd_output_can_bind_to_same_station_fan_graphic(tmp_path):
    core,station,point=setup(tmp_path);graphics=GraphicsService(core);fbd=FBDService(core)
    graphic=graphics.create_fan_demo(station['id']);logic=fbd.create_fan_demo(station['id'])
    fan=next(x for x in graphic['elements'] if x['symbol_key']=='fan')
    output=next(x for x in logic['nodes'] if x['type']=='AND')
    binding=fbd.bind_graphic_output(fan['id'],output['id'])
    assert binding['graphic_element_id']==fan['id'] and binding['logic_node_id']==output['id']


def test_fbd_output_rejects_binding_to_non_fan_or_foreign_station(tmp_path):
    core,station,point=setup(tmp_path);graphics=GraphicsService(core);fbd=FBDService(core)
    graphic=graphics.create_fan_demo(station['id']);logic=fbd.create_fan_demo(station['id'])
    sensor=next(x for x in graphic['elements'] if x['symbol_key']=='sensor')
    output=next(x for x in logic['nodes'] if x['type']=='AND')
    with pytest.raises(ValueError,match='только к символу вентилятора'):
        fbd.bind_graphic_output(sensor['id'],output['id'])


def test_fbd_http_library_demo_and_simulation_routes(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app
    client=TestClient(create_ui_app(data_dir=str(tmp_path/'api')))
    project=client.post('/api/projects',json={'name':'FBD'}).json()
    station=client.post('/api/stations',json={'name':'Plant','project_id':project['id']}).json()
    block_types={item['type'] for item in client.get('/api/fbd/library').json()['blocks']}
    assert {'BOOL_INPUT','AND','BOOL_OUTPUT','LIMIT','SCALE','COMPARE_LT'} <= block_types
    r=client.post(f"/api/stations/{station['id']}/fbd/fan-demo",json={})
    assert r.status_code==201,r.text
    assert client.post(f"/api/fbd/{r.json()['id']}/simulate",json={}).json()['outputs']['Вентилятор: RUN'] is True
    assert client.get('/logic').status_code==200


def test_fbd_simulation_input_override_changes_result_without_persisting_input(tmp_path):
    core,station,point=setup(tmp_path);svc=FBDService(core);doc=svc.create_fan_demo(station['id'])
    start=next(n for n in doc['nodes'] if n['name']=='Команда Пуск')
    assert svc.simulate(doc['id'],{start['id']:False})['outputs']['Вентилятор: RUN'] is False
    assert next(n for n in svc.get(doc['id'])['nodes'] if n['name']=='Команда Пуск')['params']['value'] is True


def test_graphic_reopen_exposes_persisted_fbd_binding(tmp_path):
    core,station,point=setup(tmp_path);graphics=GraphicsService(core);fbd=FBDService(core)
    graphic=graphics.create_fan_demo(station['id']);logic=fbd.create_fan_demo(station['id'])
    fan=next(x for x in graphic['elements'] if x['symbol_key']=='fan')
    and_node=next(x for x in logic['nodes'] if x['type']=='AND')
    binding=fbd.bind_graphic_output(fan['id'],and_node['id'])
    reopened=graphics.get(graphic['id'])
    fan_reopened=next(x for x in reopened['elements'] if x['id']==fan['id'])
    assert fan_reopened['logic_bindings']==[binding]


def test_fbd_graphic_binding_rejects_cross_station_reference(tmp_path):
    from avic_core.ui.project_station import ProjectStationService
    core,station,point=setup(tmp_path);ps=ProjectStationService(core)
    other_project=ps.create_project('Other project');other_station=ps.create_station(other_project['id'],'Other station')
    graphic=GraphicsService(core).create_fan_demo(station['id'])
    foreign_logic=FBDService(core).create_fan_demo(other_station['id'])
    fan=next(x for x in graphic['elements'] if x['symbol_key']=='fan')
    output=next(x for x in foreign_logic['nodes'] if x['type']=='AND')
    with pytest.raises(ValueError,match='одной станции'):
        FBDService(core).bind_graphic_output(fan['id'],output['id'])


def test_graphics_deleting_fan_also_removes_logic_binding(tmp_path):
    core,station,point=setup(tmp_path);graphics=GraphicsService(core);fbd=FBDService(core)
    graphic=graphics.create_fan_demo(station['id']);logic=fbd.create_fan_demo(station['id'])
    fan=next(x for x in graphic['elements'] if x['symbol_key']=='fan')
    and_node=next(x for x in logic['nodes'] if x['type']=='AND')
    fbd.bind_graphic_output(fan['id'],and_node['id'])
    elements=[x for x in graphic['elements'] if x['id']!=fan['id']]
    saved=graphics.save(graphic['id'],graphic['revision'],elements)
    assert all(x['id']!=fan['id'] for x in saved['elements'])
    assert not any(r['payload'].get('graphic_element_id')==fan['id'] for r in core.repository.list_records(entity_type='LogicGraphicsBinding'))
