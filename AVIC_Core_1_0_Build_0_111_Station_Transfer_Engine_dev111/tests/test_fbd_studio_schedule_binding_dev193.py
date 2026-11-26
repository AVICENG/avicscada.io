from pathlib import Path

from avic_core.logic_fbd_studio import FBDStudioService
from test_graphics_workbench_dev35 import setup


def _document(name, modules, links=None):
    return {
        "format": "AVIC-FBD-STRATEGY",
        "version": "1.1.1",
        "project": name,
        "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": modules}],
        "links": links or [],
        "references": [],
        "fbdPoints": [],
    }


def test_legacy_private_schedule_is_not_silently_treated_as_core_schedule(tmp_path):
    core, station, _ = setup(tmp_path)
    studio = FBDStudioService(core)
    created = studio.create(
        station["id"],
        "Legacy local schedule",
        _document("Legacy", [{
            "id": "schedule", "type": "SCHEDULE", "name": "Legacy Schedule",
            "params": {"schedule": {
                "enabled": True, "timezone": "Europe/Moscow", "valueType": "bool",
                "defaultValue": 0, "weeklyEvents": [], "exceptions": [],
            }},
            "ins": [], "outs": [{"id": "schedule-out", "name": "OUT", "type": "bool"}],
        }]),
    )

    preview = studio.compile_preview(created["id"], created["revision"])

    assert preview["compilable"] is False
    assert any("локальное расписание редактора" in issue for issue in preview["issues"])
    core.close()


def test_studio_schedule_block_compiles_against_persistent_station_schedule(tmp_path):
    core, station, _ = setup(tmp_path)
    schedule = core.schedules.create(
        station_id=station["id"], name="AHU Occupancy",
        value_type="BOOLEAN", default_value=False, timezone_name="Europe/Moscow",
    )
    studio = FBDStudioService(core)
    created = studio.create(
        station["id"],
        "Core schedule reference",
        _document("Core schedule", [{
            "id": "schedule", "type": "SCHEDULE", "name": "AHU Occupancy",
            "params": {"schedule_id": schedule["id"], "schedule_value_type": "BOOLEAN"},
            "ins": [], "outs": [{"id": "schedule-out", "name": "OUT", "type": "bool"}],
        }, {
            "id": "result", "type": "BOOL_OUTPUT", "name": "Result",
            "params": {}, "ins": [{"id": "result-in", "name": "IN", "type": "bool"}], "outs": [],
        }], [{
            "id": "link-1", "pageId": "page-main",
            "from": "out:schedule:0", "to": "in:result:0", "signalType": "bool",
        }]),
    )

    preview = studio.compile_preview(created["id"], created["revision"])
    assert preview["compilable"] is True, preview["issues"]

    compiled = studio.compile_to_core(created["id"], created["revision"])
    schedule_node = next(node for node in compiled["core_document"]["nodes"] if node["type"] == "SCHEDULE")
    assert schedule_node["params"]["schedule_id"] == schedule["id"]
    assert compiled["field_writes_enabled"] is False
    assert compiled["runtime_published"] is False
    core.close()


def test_fbd_schedule_editor_uses_core_scheduler_and_live_core_evaluation():
    path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
    html = path.read_text(encoding="utf-8")

    assert "async function editModuleDialog(m)" in html
    assert "fbdCoreSchedule" in html
    assert "/api/stations/\u0024{encodeURIComponent(studioStationId)}/schedules" in html
    assert "runtimeState?.coreSchedule" in html
    assert "/api/schedules/' + encodeURIComponent(id) + '/evaluate" in html or "'/api/schedules/'+encodeURIComponent(id)+'/evaluate'" in html
    assert "'Расписания':['SCHEDULE']" in html
    assert "AVICFBDLogic.evaluateSchedule(m.params.schedule" not in html
