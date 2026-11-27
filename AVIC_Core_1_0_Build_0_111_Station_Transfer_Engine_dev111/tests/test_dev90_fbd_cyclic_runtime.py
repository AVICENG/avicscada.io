import time
import pytest
from avic_core.logic_fbd import FBDService
from avic_core.runtime.fbd_execution import FBDExecutionService
from test_graphics_workbench_dev35 import setup


def test_cyclic_runtime_manual_ticks_and_stop_are_isolated(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create_fan_demo(station['id'])
    runtime = FBDExecutionService(core)
    configured = runtime.configure(doc['id'], interval_ms=250)
    assert configured['state'] == 'STOPPED'
    started = runtime.start(doc['id'], background=False)
    assert started['state'] == 'RUNNING'
    first = runtime.tick_once(doc['id'])
    second = runtime.tick_once(doc['id'])
    assert first['tick'] == 1 and second['tick'] == 2
    assert second['result']['outputs']['Вентилятор: RUN'] is True
    assert second['field_writes_performed'] is False
    assert second['runtime_published'] is False
    stopped = runtime.stop(doc['id'])
    assert stopped['state'] == 'STOPPED'
    assert stopped['tick_count'] == 2
    assert [e['event'] for e in runtime.events(doc['id'])].count('TICK_OK') == 2
    runtime.close(); core.close()


def test_cyclic_runtime_rejects_bad_interval_and_live_reconfigure(tmp_path):
    core, station, _ = setup(tmp_path)
    doc = FBDService(core).create_fan_demo(station['id'])
    runtime = FBDExecutionService(core)
    with pytest.raises(ValueError, match='Интервал'):
        runtime.configure(doc['id'], interval_ms=1)
    runtime.start(doc['id'], background=False)
    with pytest.raises(RuntimeError, match='работающей стратегии'):
        runtime.configure(doc['id'], interval_ms=500)
    runtime.stop(doc['id']); runtime.close(); core.close()


def test_cyclic_runtime_faults_closed_on_evaluation_error(tmp_path):
    core, station, _ = setup(tmp_path)
    doc = FBDService(core).create_fan_demo(station['id'])
    runtime = FBDExecutionService(core)
    runtime.start(doc['id'], background=False)
    # Corrupt the graph after start: runtime must stop on a failed evaluation.
    original = runtime.fbd.simulate
    runtime.fbd.simulate = lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError('test fault'))
    with pytest.raises(ValueError, match='test fault'):
        runtime.tick_once(doc['id'])
    status = runtime.status(doc['id'])
    assert status['state'] == 'ERROR'
    assert 'test fault' in status['last_error']
    assert runtime.events(doc['id'])[-1]['event'] == 'TICK_ERROR'
    runtime.fbd.simulate = original
    runtime.close(); core.close()


def test_background_scheduler_executes_and_stops(tmp_path):
    core, station, _ = setup(tmp_path)
    doc = FBDService(core).create_fan_demo(station['id'])
    runtime = FBDExecutionService(core)
    runtime.start(doc['id'], interval_ms=100, background=True)
    deadline = time.monotonic() + 2
    while runtime.status(doc['id'])['tick_count'] < 2 and time.monotonic() < deadline:
        time.sleep(0.02)
    status = runtime.stop(doc['id'])
    assert status['tick_count'] >= 2
    assert status['state'] == 'STOPPED'
    runtime.close(); core.close()


def test_fbd_runtime_cannot_publish_or_change_quality_of_foreign_station_virtual_point(tmp_path):
    from avic_core.points.runtime import FBDExposedPoint
    from avic_core.ui.project_station import ProjectStationService

    core, station_a, _ = setup(tmp_path)
    projects = ProjectStationService(core)
    project_b = projects.create_project("Foreign FBD output")
    station_b = projects.create_station(project_b["id"], "Foreign station")
    doc = FBDService(core).create_fan_demo(station_a["id"])
    foreign = FBDExposedPoint(
        name="Foreign exposed point", station_id=station_b["id"],
        fbd_document_id=doc["id"], source_module_id="not-a-module",
        data_type="bool",
    )
    core.repository.save(foreign)

    with pytest.raises(ValueError, match="виртуальная точка принадлежит другой станции"):
        core.point_runtime.publish_fbd(
            foreign.id, True, station_id=station_a["id"], quality="GOOD"
        )
    with pytest.raises(ValueError, match="виртуальная точка принадлежит другой станции"):
        core.point_runtime.mark_fbd_quality(
            foreign.id, "STALE", station_id=station_a["id"]
        )

    runtime = FBDExecutionService(core)
    runtime.start(doc["id"], background=False)
    with pytest.raises(ValueError, match="виртуальная точка принадлежит другой станции"):
        runtime.tick_once(doc["id"])
    persisted, _ = core.repository.get(foreign.id, FBDExposedPoint)
    assert persisted.value is None
    assert persisted.quality == "UNCERTAIN"
    runtime.close()
    core.close()
