from uuid import uuid4
from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def _graph():
    point_id = str(uuid4())
    data = {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Runtime points",
        "pages": [{"id": "page-main", "name": "Основная", "code": "P1", "modules": [
            {"id": "start", "type": "BOOL_INPUT", "name": "Пуск", "x": 20, "y": 30,
             "params": {"value": True}, "ins": [], "outs": [{"id": "start-out", "name": "OUT", "type": "bool"}]},
            {"id": "safe", "type": "BOOL_INPUT", "name": "Защита", "x": 20, "y": 150,
             "params": {"value": True}, "ins": [], "outs": [{"id": "safe-out", "name": "OUT", "type": "bool"}]},
            {"id": "and", "type": "AND", "name": "Разрешение вентилятора", "x": 220, "y": 80,
             "params": {}, "ins": [{"id": "and-a", "name": "A", "type": "bool"}, {"id": "and-b", "name": "B", "type": "bool"}],
             "outs": [{"id": "and-out", "name": "OUT", "type": "bool"}]},
            {"id": "out", "type": "BOOL_OUTPUT", "name": "RUN", "x": 420, "y": 80,
             "params": {}, "ins": [{"id": "out-in", "name": "IN", "type": "bool"}], "outs": []},
        ]}],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:start:0", "to": "in:and:0", "signalType": "bool"},
            {"id": "l2", "pageId": "page-main", "from": "out:safe:0", "to": "in:and:1", "signalType": "bool"},
            {"id": "l3", "pageId": "page-main", "from": "out:and:0", "to": "in:out:0", "signalType": "bool"},
        ],
        "references": [],
        "fbdPoints": [{"id": point_id, "tag": "AHU_FAN_RUN", "name": "Разрешение вентилятора",
                       "path": "AHU-01/FBD/AHU_FAN_RUN", "dataType": "digital", "unit": "",
                       "direction": "output", "source": {"pageId": "page-main", "moduleId": "and",
                       "portIndex": 0, "portId": "and-out", "portName": "OUT"},
                       "license": {"status": "pending_core_registration"}}],
    }
    return data, point_id


def test_compiled_fbd_exposed_output_becomes_live_virtual_point_and_tree_value(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'DEV103'}).json()
        station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'AHU-01'}).json()
        data, point_id = _graph()
        created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={"name": "AHU logic", "data": data})
        assert created.status_code == 201, created.text
        source = created.json()
        compiled = client.post(f"/api/fbd-studio/{source['id']}/compile", json={"expected_revision": source['revision']})
        assert compiled.status_code == 200, compiled.text
        result = compiled.json()
        assert result['registered_fbd_points'] == 1
        core_id = result['core_document']['id']

        # FBD point is visible through the same Point Runtime API and tree catalog.
        before = client.get(f'/api/points/{point_id}/runtime')
        assert before.status_code == 200, before.text
        assert before.json()['quality'] == 'UNCERTAIN'
        tree = client.get('/api/engineering/tree').json()
        station_node = tree['projects'][0]['stations'][0]
        fbd_point = station_node['fbd_projects'][0]['points'][0]
        assert fbd_point['id'] == point_id
        assert fbd_point['value'] is None
        assert fbd_point['quality'] == 'UNCERTAIN'

        started = client.post(f'/api/fbd-runtime/{core_id}/start', json={'interval_ms': 100, 'background': False})
        assert started.status_code == 200, started.text
        tick = client.post(f'/api/fbd-runtime/{core_id}/tick', json={})
        assert tick.status_code == 200, tick.text
        assert tick.json()['runtime_published'] is True
        assert tick.json()['result']['published_fbd_points'] == 1
        live = client.get(f'/api/points/{point_id}/runtime').json()
        assert live['value'] is True
        assert live['quality'] == 'GOOD'

        # A changed virtual BOOL_INPUT is re-evaluated by the cyclic Core FBD runtime.
        start_node = next(n for n in result['core_document']['nodes'] if n['params'].get('_studio_module_id') == 'start')
        tick_off = client.post(f'/api/fbd-runtime/{core_id}/tick', json={'inputs': {start_node['id']: False}})
        assert tick_off.status_code == 200, tick_off.text
        live_off = client.get(f'/api/points/{point_id}/runtime').json()
        assert live_off['value'] is False and live_off['quality'] == 'GOOD'

        catalog = client.get(f"/api/engineering/points?station_id={station['id']}").json()
        row = next(p for p in catalog['points'] if p['id'] == point_id)
        assert row['value'] is False and row['quality'] == 'GOOD'

        tree = client.get('/api/engineering/tree').json()
        fbd_point = tree['projects'][0]['stations'][0]['fbd_projects'][0]['points'][0]
        assert fbd_point['value'] is False and fbd_point['quality'] == 'GOOD'

        # Graphics can bind the virtual output point by its stable Core ID.
        graphic = client.post(f'/api/stations/{station["id"]}/graphics', json={"name": "AHU mimic"}).json()
        from uuid import uuid4
        element_id = str(uuid4())
        saved = client.put(f'/api/graphics/{graphic["id"]}', json={
            "expected_revision": graphic["revision"],
            "elements": [{"id": element_id, "name": "Supply fan", "symbol_key": "fan",
                "x": 100, "y": 100, "width": 160, "height": 120, "rotation": 0, "layer": 1,
                "bindings": [{"point_id": point_id, "role": "feedback", "binding_type": "value", "target_property": "animation", "settings": {}}]}]
        })
        assert saved.status_code == 200, saved.text
        evaluated = client.get(f'/api/graphics/{graphic["id"]}/bindings/evaluate').json()
        binding = next(iter(evaluated['bindings'].values()))
        assert binding['value'] is False and binding['quality'] == 'GOOD'

        stopped = client.post(f'/api/fbd-runtime/{core_id}/stop')
        assert stopped.status_code == 200
        assert client.get(f'/api/points/{point_id}/runtime').json()['quality'] == 'STALE'


def test_graphics_editor_accepts_tree_point_drag_and_tree_polls_values():
    from pathlib import Path
    from avic_core.ui import app as ui_module
    graphics = (Path(ui_module.__file__).parent / 'static' / 'graphics.html').read_text(encoding='utf-8')
    assert 'bindDroppedPoint(pointId,target)' in graphics
    assert "getData('point')||e.dataTransfer.getData('fbd-point')" in graphics
    assert "targetProperty=fan?'animation':'value'" in graphics
    source = Path(ui_module.__file__).read_text(encoding='utf-8')
    assert 'refreshPointValues' in source
    assert 'window.setInterval(refreshPointValues,2000)' in source


def test_physical_point_live_value_is_visible_in_engineering_tree(tmp_path):
    from avic_core.domain.models import Device, Point
    app = create_ui_app(data_dir=str(tmp_path))
    with TestClient(app) as client:
        project = client.post('/api/projects', json={'name': 'Live tree'}).json()
        station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'Station'}).json()
        device = Device(name='Trend controller', station_id=station['id'], protocol='bacnet/ip',
                        address='192.0.2.10', network_id='test-net')
        app.state.core.repository.save(device)
        point = Point(name='Supply air temperature', device_id=device.id, data_type='float', unit='°C')
        app.state.core.repository.save(point)
        app.state.core.point_runtime.publish(point.id, 21.75, quality='GOOD')
        tree = client.get('/api/engineering/tree').json()
        node = tree['projects'][0]['stations'][0]['networks'][0]['channels'][0]['devices'][0]['points'][0]
        assert node['id'] == point.id
        assert node['value'] == 21.75
        assert node['unit'] == '°C'
        assert node['quality'] == 'GOOD'
        assert node['timestamp']
