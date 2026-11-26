from avic_core.domain.models import PointQuality
from avic_core.logic_fbd_studio import FBDStudioService
from test_graphics_workbench_dev35 import setup


def _studio_document(project, pages, links, references=()):
    return {
        "format": "AVIC-FBD-STRATEGY",
        "version": "1.1.1",
        "project": project,
        "pages": pages,
        "links": links,
        "references": list(references),
        "fbdPoints": [],
    }


def test_studio_compiler_resolves_point_input_type_through_cross_page_connective(tmp_path):
    core, station, point = setup(tmp_path)
    point.data_type = "binary-input"
    point.value = True
    point.quality = PointQuality.GOOD
    _, version = core.repository.get(point.id, type(point))
    core.repository.save(point, expected_version=version)

    source_page = {
        "id": "page-source", "name": "Источник", "code": "P1",
        "modules": [
            {"id": "point-source", "type": "POINT_INPUT", "name": "Разрешение",
             "x": 20, "y": 20, "params": {"pointRef": {"id": point.id}},
             "ins": [], "outs": [{"id": "point-out", "name": "OUT", "type": "bool"}]},
            {"id": "to-marker", "type": "TO_CONNECTIVE", "name": "To Connective",
             "x": 200, "y": 20, "params": {"referenceId": "ref-1"},
             "ins": [{"id": "marker-in", "name": "OUT", "type": "bool"}], "outs": []},
        ],
    }
    target_page = {
        "id": "page-target", "name": "Потребитель", "code": "P2",
        "modules": [
            {"id": "proxy", "type": "CONNECTIVE", "name": "Connective",
             "x": 20, "y": 20, "params": {"referenceId": "ref-1"},
             "ins": [], "outs": [{"id": "proxy-out", "name": "OUT", "type": "bool"}]},
            {"id": "result", "type": "BOOL_OUTPUT", "name": "Результат",
             "x": 220, "y": 20, "params": {},
             "ins": [{"id": "result-in", "name": "IN", "type": "bool"}], "outs": []},
        ],
    }
    references = [{
        "id": "ref-1", "sourcePageId": "page-source", "sourceModuleId": "point-source",
        "sourcePort": 0, "targetPageId": "page-target", "proxyModuleId": "proxy",
        "toModuleId": "to-marker",
    }]
    links = [{"id": "link-1", "pageId": "page-target",
              "from": "out:proxy:0", "to": "in:result:0", "signalType": "bool"}]

    studio = FBDStudioService(core)
    created = studio.create(station["id"], "Typed point connective",
                            _studio_document("Typed point", [source_page, target_page], links, references))
    preview = studio.compile_preview(created["id"], created["revision"])
    assert preview["compilable"] is True, preview["issues"]

    compiled = studio.compile_to_core(created["id"], created["revision"])
    assert compiled["compiled_blocks"] == 2
    assert compiled["compiled_links"] == 1
    assert compiled["field_writes_enabled"] is False
    assert compiled["runtime_published"] is False
    core.close()


def test_studio_compiler_resolves_numeric_schedule_output_before_link_validation(tmp_path):
    core, station, _ = setup(tmp_path)
    schedule = core.schedules.create(
        station_id=station["id"], name="Numeric setpoint",
        value_type="NUMERIC", default_value=21.5,
    )
    page = {
        "id": "page-main", "name": "Основная", "code": "P1",
        "modules": [
            {"id": "schedule", "type": "SCHEDULE", "name": "Задание",
             "x": 20, "y": 20, "params": {"schedule_id": schedule["id"]},
             "ins": [], "outs": [{"id": "schedule-out", "name": "OUT", "type": "float"}]},
            {"id": "result", "type": "FLOAT_OUTPUT", "name": "Результат",
             "x": 220, "y": 20, "params": {},
             "ins": [{"id": "result-in", "name": "IN", "type": "float"}], "outs": []},
        ],
    }
    links = [{"id": "link-1", "pageId": "page-main",
              "from": "out:schedule:0", "to": "in:result:0", "signalType": "float"}]
    studio = FBDStudioService(core)
    created = studio.create(station["id"], "Typed schedule",
                            _studio_document("Typed schedule", [page], links))
    preview = studio.compile_preview(created["id"], created["revision"])
    assert preview["compilable"] is True, preview["issues"]

    compiled = studio.compile_to_core(created["id"], created["revision"])
    assert compiled["compiled_blocks"] == 2
    assert compiled["compiled_links"] == 1
    core.close()
