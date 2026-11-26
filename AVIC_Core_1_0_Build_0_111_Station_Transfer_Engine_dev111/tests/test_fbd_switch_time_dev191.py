from datetime import datetime, timezone
from uuid import uuid4

from fastapi.testclient import TestClient

from avic_core.logic_fbd import FBDService
from avic_core.ui import create_ui_app
from test_graphics_workbench_dev35 import setup


TIME_OUTPUTS = [
    "CURRENT_TIME", "MINUTES_PAST_MIDNIGHT", "DAY", "MONTH", "WEEKDAY",
    "DAY_BIT_5", "DAY_BIT_6", "DAY_BIT_7", "SECOND_PULSE", "MINUTE_PULSE",
    "PULSE_5_MIN", "PULSE_10_MIN", "PULSE_15_MIN", "PULSE_20_MIN",
    "PULSE_30_MIN", "PULSE_60_MIN", "PULSE_6_HOUR", "PULSE_24_HOUR",
    "WEEKLY_PULSE", "MONTHLY_PULSE", "YEARLY_PULSE", "UTC_OFFSET",
]


def _uid():
    return str(uuid4())


def test_time_module_uses_station_timezone_and_emits_calendar_and_pulses(tmp_path):
    core, station, _ = setup(tmp_path)
    core.time_management.configure_station(station["id"], "UTC")
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Time and switch")
    page_id = doc["pages"][0]["id"]
    time_id, switch_id, clock_out, minute_out, switch_out = (_uid() for _ in range(5))
    nodes = [
        {"id": time_id, "type": "TIME", "name": "Station clock", "params": {}, "page_id": page_id},
        {"id": switch_id, "type": "SWITCH", "name": "Manual override",
         "params": {"value": True, "user_level": 7}, "page_id": page_id},
        {"id": clock_out, "type": "FLOAT_OUTPUT", "name": "Clock", "params": {}, "page_id": page_id},
        {"id": minute_out, "type": "BOOL_OUTPUT", "name": "Minute pulse", "params": {}, "page_id": page_id},
        {"id": switch_out, "type": "BOOL_OUTPUT", "name": "Switch status", "params": {}, "page_id": page_id},
    ]
    links = [
        {"source_node_id": time_id, "source_port": "CURRENT_TIME", "target_node_id": clock_out, "target_port": "IN"},
        {"source_node_id": time_id, "source_port": "MINUTE_PULSE", "target_node_id": minute_out, "target_port": "IN"},
        {"source_node_id": switch_id, "source_port": "OUT", "target_node_id": switch_out, "target_port": "IN"},
    ]
    fbd.save(doc["id"], doc["revision"], nodes, links)
    state = {}
    first = fbd.simulate(
        doc["id"], runtime_state=state,
        now_utc=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    assert first["outputs"]["Clock"] == 0.0
    assert first["outputs"]["Minute pulse"] is False
    assert first["outputs"]["Switch status"] is True
    assert first["node_values"][f"{time_id}:WEEKDAY"] == 4.0
    assert first["node_values"][f"{time_id}:DAY_BIT_7"] is True

    next_minute = fbd.simulate(
        doc["id"], runtime_state=state,
        now_utc=datetime(2026, 1, 1, 0, 1, 0, tzinfo=timezone.utc),
    )
    assert next_minute["outputs"]["Minute pulse"] is True
    override = fbd.simulate(
        doc["id"], inputs={switch_id: False}, runtime_state=state,
        now_utc=datetime(2026, 1, 1, 0, 1, 1, tzinfo=timezone.utc),
    )
    assert override["outputs"]["Switch status"] is False
    assert override["field_writes_performed"] is False
    core.close()


def test_studio_compiles_time_multi_outputs_and_switch_source(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("DEV191 Project")
    station = client.app.state.project_station.create_station(project["id"], "DEV191 Station")
    modules = [
        {"id": "time", "type": "TIME", "name": "Station clock", "params": {},
         "ins": [], "outs": [{"id": f"time-{name}", "name": name,
                              "type": "bool" if name in {"DAY_BIT_5", "DAY_BIT_6", "DAY_BIT_7",
                                  "SECOND_PULSE", "MINUTE_PULSE", "PULSE_5_MIN", "PULSE_10_MIN",
                                  "PULSE_15_MIN", "PULSE_20_MIN", "PULSE_30_MIN", "PULSE_60_MIN",
                                  "PULSE_6_HOUR", "PULSE_24_HOUR", "WEEKLY_PULSE", "MONTHLY_PULSE",
                                  "YEARLY_PULSE"} else "num"} for name in TIME_OUTPUTS]},
        {"id": "switch", "type": "SWITCH", "name": "Override",
         "params": {"value": True, "user_level": 5},
         "ins": [{"id": "switch-in", "name": "IN", "type": "bool"}],
         "outs": [{"id": "switch-out", "name": "OUT", "type": "bool"}]},
        {"id": "clock", "type": "FLOAT_OUTPUT", "name": "Clock", "params": {},
         "ins": [{"id": "clock-in", "name": "IN", "type": "num"}], "outs": []},
        {"id": "pulse", "type": "BOOL_OUTPUT", "name": "Minute pulse", "params": {},
         "ins": [{"id": "pulse-in", "name": "IN", "type": "bool"}], "outs": []},
        {"id": "switch-out", "type": "BOOL_OUTPUT", "name": "Switch", "params": {},
         "ins": [{"id": "switch-out-in", "name": "IN", "type": "bool"}], "outs": []},
    ]
    data = {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Time and switch parity",
        "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": modules}],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:time:0", "to": "in:clock:0", "signalType": "num"},
            {"id": "l2", "pageId": "page-main", "from": "out:time:9", "to": "in:pulse:0", "signalType": "bool"},
            {"id": "l3", "pageId": "page-main", "from": "out:switch:0", "to": "in:switch-out:0", "signalType": "bool"},
        ],
        "references": [], "fbdPoints": [],
    }
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Time and switch parity", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert {"TIME", "SWITCH"} <= set(preview.json()["supported_block_types"])
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    core_doc = compiled.json()["core_document"]
    time_node = next(node for node in core_doc["nodes"] if node["type"] == "TIME")
    assert set(time_node["ports"]["outputs"]) == set(TIME_OUTPUTS)
    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["Switch"] is True


def test_legacy_time_occ_placeholder_requires_explicit_recreation(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("Legacy TIME")
    station = client.app.state.project_station.create_station(project["id"], "Legacy station")
    data = {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Legacy TIME",
        "pages": [{"id": "page-main", "name": "Main", "code": "P1", "modules": [
            {"id": "time", "type": "TIME", "name": "Old TIME", "params": {},
             "ins": [], "outs": [{"id": "old-occ", "name": "OCC", "type": "bool"}]},
            {"id": "output", "type": "BOOL_OUTPUT", "name": "Old occupancy", "params": {},
             "ins": [{"id": "output-in", "name": "IN", "type": "bool"}], "outs": []},
        ]}],
        "links": [{"id": "legacy-link", "pageId": "page-main", "from": "out:time:0",
                   "to": "in:output:0", "signalType": "bool"}],
        "references": [], "fbdPoints": [],
    }
    created = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Legacy TIME", "data": data},
    )
    assert created.status_code == 201, created.text
    source = created.json()
    preview = client.post(
        f"/api/fbd-studio/{source['id']}/compile-preview",
        json={"expected_revision": source["revision"]},
    )
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is False
    assert any("TIME.OCC placeholder" in issue for issue in preview.json()["issues"])


def test_time_module_exposes_station_utc_offset(tmp_path):
    core, station, _ = setup(tmp_path)
    core.time_management.configure_station(station["id"], "Europe/Moscow")
    fbd = FBDService(core)
    doc = fbd.create(station["id"], "Station UTC offset")
    page_id = doc["pages"][0]["id"]
    time_id = _uid()
    fbd.save(doc["id"], doc["revision"], [
        {"id": time_id, "type": "TIME", "name": "Station clock", "params": {}, "page_id": page_id},
    ], [])
    result = fbd.simulate(
        doc["id"],
        now_utc=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )
    assert result["node_values"][f"{time_id}:UTC_OFFSET"] == 3.0
    assert result["node_values"][f"{time_id}:CURRENT_TIME"] == 3.0
    core.close()
