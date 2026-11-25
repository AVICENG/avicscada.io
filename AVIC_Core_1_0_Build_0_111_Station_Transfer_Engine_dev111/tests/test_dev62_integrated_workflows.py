from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from avic_core.application.container import CoreApplication
from avic_core.network.discovery_history import DiscoveryHistory
from avic_core.ui.device_import import DeviceImportService
from avic_core.ui.project_station import ProjectStationService
from avic_core.graphics import GraphicsService
from avic_core.logic_fbd import FBDService


def make_station(tmp_path):
    core = CoreApplication(tmp_path)
    ps = ProjectStationService(core)
    project = ps.create_project("Integrated")
    station = ps.create_station(project["id"], "Plant")
    return core, station


def inspection():
    return {"address": "192.0.2.20", "network_id": "plant-net",
            "device_identity": {"device_instance": 120, "manufacturer": "Vendor A",
                                 "model": "Controller X", "identity_sources": {
                                     "manufacturer": "bacnet.vendor_id:5", "model": "bacnet.model_name"}},
            "objects": [
                {"type_name": "analog-input", "instance": 1, "object_name": "Supply temperature",
                 "native_identity": "object:0:1"},
                {"type_name": "binary-input", "instance": 2, "object_name": "Filter alarm",
                 "native_identity": "object:3:2"},
            ]}


def test_discovery_history_persists_and_returns_read_only_evidence(tmp_path):
    path = tmp_path / "db" / "discovery.sqlite3"
    history = DiscoveryHistory(path)
    saved = history.record_completed(network_id="plant-net", protocol="BACnet/IP",
        devices=[{"device_instance": 120, "ip_address": "192.0.2.20", "vendor_id": 5,
                  "manufacturer": "Vendor A", "manufacturer_source": "bacnet.vendor_id:5",
                  "model_name": None, "model_status": "not_read", "identity_confidence": "confirmed",
                  "password": "must-not-persist"}], diagnostics={"devices_found": 1})
    reopened = DiscoveryHistory(path)
    got = reopened.get(saved["session_id"])
    assert got["device_count"] == 1 and got["write_enabled"] is False
    assert got["devices"][0]["manufacturer"] == "Vendor A"
    assert "password" not in got["devices"][0]
    assert reopened.list()[0]["session_id"] == saved["session_id"]


def test_discovery_history_rejects_unbounded_limits_and_unknown_ids(tmp_path):
    history = DiscoveryHistory(tmp_path / "history.sqlite3")
    with pytest.raises(ValueError):
        history.list(501)
    with pytest.raises(KeyError):
        history.get("missing")


def test_import_preview_reports_new_points_without_mutation(tmp_path):
    core, station = make_station(tmp_path)
    service = DeviceImportService(core)
    before = len(core.repository.list_records(entity_type="Device"))
    preview = service.preview_bacnet(station["id"], inspection(), ["object:0:1"])
    after = len(core.repository.list_records(entity_type="Device"))
    assert preview["can_import"] is True
    assert preview["new_points"] == ["object:0:1"]
    assert preview["device_exists"] is False
    assert before == after == 0
    assert preview["field_device_writes"] is False


def test_import_preview_detects_duplicates_after_import(tmp_path):
    core, station = make_station(tmp_path)
    service = DeviceImportService(core)
    snapshot = inspection()
    service.import_bacnet(station["id"], snapshot, ["object:0:1"])
    preview = service.preview_bacnet(station["id"], snapshot, ["object:0:1", "object:3:2"])
    assert preview["device_exists"] is True
    assert preview["duplicate_points"] == ["object:0:1"]
    assert preview["new_points"] == ["object:3:2"]


def test_import_preview_rejects_unknown_selection(tmp_path):
    core, station = make_station(tmp_path)
    result = DeviceImportService(core).preview_bacnet(station["id"], inspection(), ["object:9:9"])
    assert result["unknown_selection"] == ["object:9:9"]
    assert result["can_import"] is False


def test_import_preview_is_station_scoped(tmp_path):
    core, station = make_station(tmp_path)
    project = core.repository.list_records(entity_type="Project")[0]["entity_id"]
    with pytest.raises(ValueError, match="станцией"):
        DeviceImportService(core).preview_bacnet(project, inspection(), import_all=True)


def test_graphics_fbd_roundtrip_and_simulation_are_offline(tmp_path):
    core, station = make_station(tmp_path)
    fbd = FBDService(core)
    logic = fbd.create_fan_demo(station["id"])
    result = fbd.simulate(logic["id"])
    assert result["outputs"]["Вентилятор: RUN"] is True
    assert result["field_writes_performed"] is False
    graphic = GraphicsService(core).create_fan_demo(station["id"])
    assert graphic["station_id"] == station["id"]
    assert graphic["write_enabled"] is False


def test_api_exposes_discovery_history_and_import_preview(tmp_path):
    from avic_core.ui.app import create_ui_app
    app = create_ui_app(data_dir=str(tmp_path / "api"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "P"}).json()
    station = client.post("/api/stations", json={"name": "S", "project_id": project["id"]}).json()
    assert client.get("/api/network/discovery-sessions").status_code == 200
    preview = client.post(f"/api/stations/{station['id']}/devices/import-preview", json={
        "inspection": inspection(), "selected_native_ids": ["object:0:1"]})
    assert preview.status_code == 200
    assert preview.json()["new_points"] == ["object:0:1"]
    assert preview.json()["write_enabled"] is False
    assert client.get("/api/network/discovery-sessions?limit=501").status_code == 400


def test_import_preview_does_not_accept_non_object_inspection(tmp_path):
    from avic_core.ui.app import create_ui_app
    app = create_ui_app(data_dir=str(tmp_path / "api"))
    client = TestClient(app)
    project = client.post("/api/projects", json={"name": "P"}).json()
    station = client.post("/api/stations", json={"name": "S", "project_id": project["id"]}).json()
    response = client.post(f"/api/stations/{station['id']}/devices/import-preview", json={"inspection": []})
    assert response.status_code == 400


def test_fbd_library_has_analog_limit_and_scaling_blocks(tmp_path):
    core, station = make_station(tmp_path)
    service = FBDService(core)
    doc = service.create(station["id"], "Analog chain")
    import uuid
    source = str(uuid.uuid4())
    limit = str(uuid.uuid4())
    output = str(uuid.uuid4())
    nodes = [
        {"id": source, "type": "FLOAT_INPUT", "name": "Raw", "params": {"value": 125.0}},
        {"id": limit, "type": "LIMIT", "name": "Clamp"},
        {"id": output, "type": "FLOAT_OUTPUT", "name": "Bounded"},
    ]
    links = [
        {"source_node_id": source, "source_port": "OUT", "target_node_id": limit, "target_port": "IN"},
        {"source_node_id": limit, "source_port": "OUT", "target_node_id": output, "target_port": "IN"},
    ]
    # Unconnected LOW/HIGH inputs default to 0.0, so the result is bounded to zero.
    saved = service.save(doc["id"], doc["revision"], nodes, links)
    result = service.simulate(doc["id"])
    assert result["outputs"]["Bounded"] == 0.0
    assert result["field_writes_performed"] is False
    assert {x["type"] for x in service.library()} >= {"LIMIT", "SCALE", "COMPARE_LT"}


def test_fbd_limit_rejects_inverted_bounds(tmp_path):
    core, station = make_station(tmp_path)
    service = FBDService(core)
    doc = service.create(station["id"], "Bad limits")
    import uuid
    raw, low, high, lim, out = [str(uuid.uuid4()) for _ in range(5)]
    nodes = [
        {"id": raw, "type": "FLOAT_INPUT", "name": "Raw", "params": {"value": 10}},
        {"id": low, "type": "FLOAT_INPUT", "name": "Low", "params": {"value": 20}},
        {"id": high, "type": "FLOAT_INPUT", "name": "High", "params": {"value": 5}},
        {"id": lim, "type": "LIMIT", "name": "Limit"},
        {"id": out, "type": "FLOAT_OUTPUT", "name": "Out"},
    ]
    links = []
    for src, target in ((raw, "IN"), (low, "LOW"), (high, "HIGH")):
        links.append({"source_node_id": src, "source_port": "OUT", "target_node_id": lim, "target_port": target})
    links.append({"source_node_id": lim, "source_port": "OUT", "target_node_id": out, "target_port": "IN"})
    service.save(doc["id"], doc["revision"], nodes, links)
    with pytest.raises(ValueError, match="LOW не может быть больше HIGH"):
        service.simulate(doc["id"])


def test_fbd_scale_maps_engineering_range(tmp_path):
    core, station = make_station(tmp_path)
    service = FBDService(core)
    doc = service.create(station["id"], "Scale")
    import uuid
    raw, scale, output = [str(uuid.uuid4()) for _ in range(3)]
    nodes = [
        {"id": raw, "type": "FLOAT_INPUT", "name": "Raw", "params": {"value": 50}},
        {"id": scale, "type": "SCALE", "name": "Percent"},
        {"id": output, "type": "FLOAT_OUTPUT", "name": "Scaled"},
    ]
    links = [
        {"source_node_id": raw, "source_port": "OUT", "target_node_id": scale, "target_port": "IN"},
        {"source_node_id": scale, "source_port": "OUT", "target_node_id": output, "target_port": "IN"},
    ]
    # Other SCALE inputs default to zero; the degenerate input span must fail explicitly.
    service.save(doc["id"], doc["revision"], nodes, links)
    with pytest.raises(ValueError, match="IN_MIN и IN_MAX"):
        service.simulate(doc["id"])


def test_fbd_scale_successful_linear_conversion(tmp_path):
    core, station = make_station(tmp_path)
    service = FBDService(core)
    doc = service.create(station["id"], "Scale success")
    import uuid
    ids = [str(uuid.uuid4()) for _ in range(7)]
    raw, in_min, in_max, out_min, out_max, scale, output = ids
    specs = [
        (raw, "FLOAT_INPUT", "Raw", 50),
        (in_min, "FLOAT_INPUT", "In min", 0),
        (in_max, "FLOAT_INPUT", "In max", 100),
        (out_min, "FLOAT_INPUT", "Out min", 0),
        (out_max, "FLOAT_INPUT", "Out max", 10),
        (scale, "SCALE", "Scale", None),
        (output, "FLOAT_OUTPUT", "Scaled", None),
    ]
    nodes = [{"id": nid, "type": typ, "name": name,
              "params": ({"value": value} if value is not None else {})}
             for nid, typ, name, value in specs]
    links = [{"source_node_id": src, "source_port": "OUT", "target_node_id": scale, "target_port": port}
             for src, port in ((raw, "IN"), (in_min, "IN_MIN"), (in_max, "IN_MAX"),
                               (out_min, "OUT_MIN"), (out_max, "OUT_MAX"))]
    links.append({"source_node_id": scale, "source_port": "OUT", "target_node_id": output, "target_port": "IN"})
    service.save(doc["id"], doc["revision"], nodes, links)
    result = service.simulate(doc["id"])
    assert result["outputs"]["Scaled"] == pytest.approx(5.0)


def test_platform_status_reports_safe_default_posture(tmp_path):
    from avic_core.ui.app import create_ui_app
    app = create_ui_app(data_dir=str(tmp_path / "platform"))
    response = TestClient(app).get("/api/platform/status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["version"] == "1.0.0.dev77"
    assert payload["safety"]["field_writes_enabled"] is False
    assert payload["safety"]["driver_autostart"] is False
    assert payload["safety"]["trend_integration_required"] is False
    assert payload["safety"]["tonn_linux_agent_implemented"] is False
