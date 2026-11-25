from uuid import uuid4

import pytest

from avic_core.logic_fbd import FBDService
from avic_core.runtime.fbd_execution import FBDExecutionService
from test_graphics_workbench_dev35 import setup


def _graph_with_schedule(core, station_id, schedule_id, output_type="BOOL_OUTPUT"):
    fbd = FBDService(core)
    doc = fbd.create(station_id, "Schedule integration")
    schedule_node = str(uuid4())
    output_node = str(uuid4())
    saved = fbd.save(doc["id"], doc["revision"], [
        {"id": schedule_node, "type": "SCHEDULE", "name": "Рабочий график",
         "params": {"schedule_id": schedule_id}},
        {"id": output_node, "type": output_type, "name": "Результат расписания"},
    ], [{"source_node_id": schedule_node, "source_port": "OUT",
         "target_node_id": output_node, "target_port": "IN"}])
    return fbd, saved, schedule_node


def test_fbd_schedule_block_reads_persistent_core_schedule_without_writing_points(tmp_path):
    core, station, _ = setup(tmp_path)
    schedule = core.schedules.create(station_id=station["id"], name="AHU Week",
                                     value_type="BOOLEAN", default_value=True,
                                     timezone_name="Europe/Moscow")
    fbd, doc, schedule_node = _graph_with_schedule(core, station["id"], schedule["id"])

    result = fbd.simulate(doc["id"])

    assert result["outputs"]["Результат расписания"] is True
    diagnostic = result["node_diagnostics"][schedule_node]
    assert diagnostic["source"]["kind"] == "station_schedule"
    assert diagnostic["source"]["schedule_id"] == schedule["id"]
    assert diagnostic["source"]["timezone"] == "Europe/Moscow"
    assert diagnostic["source"]["output_mode"] == "INTENT_ONLY_NO_FIELD_WRITE"
    assert result["field_writes_performed"] is False
    assert result["runtime_published"] is False
    core.close()


def test_fbd_schedule_block_is_evaluated_on_each_cyclic_runtime_tick(tmp_path):
    core, station, _ = setup(tmp_path)
    schedule = core.schedules.create(station_id=station["id"], name="AHU Enable",
                                     value_type="BOOLEAN", default_value=False)
    fbd, doc, _ = _graph_with_schedule(core, station["id"], schedule["id"])
    runtime = FBDExecutionService(core)
    runtime.start(doc["id"], background=False)

    tick = runtime.tick_once(doc["id"])

    assert tick["result"]["outputs"]["Результат расписания"] is False
    assert tick["field_writes_performed"] is False
    assert runtime.status(doc["id"])["tick_count"] == 1
    runtime.stop(doc["id"])
    runtime.close()
    core.close()


def test_fbd_schedule_block_rejects_cross_station_schedule_at_save(tmp_path):
    core, station, _ = setup(tmp_path)
    other_project = __import__("avic_core.ui.project_station", fromlist=["ProjectStationService"]).ProjectStationService(core).create_project("Other")
    other_station = __import__("avic_core.ui.project_station", fromlist=["ProjectStationService"]).ProjectStationService(core).create_station(other_project["id"], "Other station")
    schedule = core.schedules.create(station_id=other_station["id"], name="Foreign", value_type="BOOLEAN", default_value=False)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Isolation")
    with pytest.raises(ValueError, match="другой станции"):
        fbd.save(doc["id"], doc["revision"], [
            {"id": str(uuid4()), "type": "SCHEDULE", "name": "Чужое расписание",
             "params": {"schedule_id": schedule["id"]}},
        ], [])
    core.close()


def test_fbd_schedule_block_rejects_missing_schedule_reference(tmp_path):
    core, station, _ = setup(tmp_path)
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Missing schedule")
    with pytest.raises(ValueError, match="выберите сохранённое расписание"):
        fbd.save(doc["id"], doc["revision"], [
            {"id": str(uuid4()), "type": "SCHEDULE", "name": "Не настроено", "params": {}},
        ], [])
    core.close()


def test_numeric_schedule_can_feed_fbd_analog_output(tmp_path):
    core, station, _ = setup(tmp_path)
    schedule = core.schedules.create(station_id=station["id"], name="Supply Setpoint",
                                     value_type="NUMERIC", default_value=21.5)
    fbd, doc, schedule_node = _graph_with_schedule(core, station["id"], schedule["id"], "FLOAT_OUTPUT")
    result = fbd.simulate(doc["id"])
    assert result["outputs"]["Результат расписания"] == 21.5
    assert result["node_diagnostics"][schedule_node]["source"]["value_type"] == "NUMERIC"
    core.close()


def test_fbd_library_advertises_core_schedule_block(tmp_path):
    core, station, _ = setup(tmp_path)
    block = next(item for item in FBDService(core).library() if item["type"] == "SCHEDULE")
    assert block["label"] == "Расписание станции"
    assert block["category"] == "Schedule"
    assert block["outputs"] == {"OUT": "any"}
    core.close()
