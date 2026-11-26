from __future__ import annotations

import json
import zipfile

import pytest

from avic_core.application.container import CoreApplication
from avic_core.domain.models import Component, Device, PhysicalNetwork, Point, PointDirection, ProtocolChannel
from avic_core.transfer import StationTransferError, StationTransferManager
from avic_core.ui.project_station import ProjectStationService


def _source_core(path):
    core = CoreApplication(path)
    project = ProjectStationService(core).create_project("Исходный проект")
    station = ProjectStationService(core).create_station(project["id"], "AHU-01")
    network = PhysicalNetwork(name="BACnet LAN", station_id=station["id"], interface_id="NIC-1",
                              interface_name="Ethernet", ipv4="192.168.10.5", subnet_cidr="192.168.10.0/24",
                              station_ipv4="192.168.10.5", gateway_ipv4="192.168.10.1", dns_servers=["1.1.1.1"])
    channel = ProtocolChannel(name="BACnet/IP", station_id=station["id"], network_id=network.id,
                              protocol="bacnet/ip", enabled=True, mode="read_write")
    device = Device(name="AHU Controller", station_id=station["id"], address="192.168.10.40",
                    protocol="bacnet/ip", network_id=network.id, native_identity="device:1234",
                    manufacturer="Trend", model="IQ4")
    point = Point(name="Supply Air Temp", device_id=device.id, value=21.5, direction=PointDirection.OUTPUT)
    component = Component(name="Supply Fan", station_id=station["id"], component_type="fan",
                          properties={"speed": 50, "mode": "AUTO"})
    core.objects.save_graph([network, channel, device, point, component])
    core.custom_svg.import_svg(station["id"], name="Fan", category="HVAC", filename="fan.svg",
                               svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><circle cx="5" cy="5" r="4"/></svg>')
    core.time_management.configure_station(station["id"], "America/Chicago", ntp_enabled=True, ntp_servers=["10.10.10.10"])
    core.time_management.set_device_sync_permission(station["id"], device.id, True,
                                                    approved_by="source-engineer", reason="commissioned")
    core.schedules.create(station_id=station["id"], name="Fan Schedule", value_type="NUMERIC", default_value=0)
    schedule = core.schedules.list(station_id=station["id"])[0]
    core.schedules.add_weekly_event(schedule["id"], day_of_week=0, start_minute=480,
                                    end_minute=1020, value=50)
    core.schedules.bind_point(schedule["id"], point.id)
    core.analytics.tag_point(point.id, "Temperature", hierarchy_path="/HVAC/AHU-01")
    core.dependencies.add(component.id, point.id, "uses", station_id=station["id"], metadata={"slot": "value"})
    return core, project, station, network, channel, device, point, component


def test_station_transfer_preserves_engineering_ids_and_rebinds_project(tmp_path):
    source, source_project, station, network, channel, device, point, component = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Целевой проект")
    try:
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "ahu.avicstation",
                                                          source_core_version="1.0.0.dev111")
        preview = target.station_transfer.inspect_package(package, target_core_version="1.0.0.dev111")
        assert preview.compatible
        assert preview.entity_count == 6
        stage = target.station_transfer.stage_import(package, tmp_path / "staging",
            expected_package_id=preview.package_id, target_core_version="1.0.0.dev111")
        result = target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id,
                                                       target_project_id=target_project["id"])
        assert result["activation"] == "NOT_ACTIVATED"
        imported_station = target.repository.get_record(station["id"])
        assert imported_station["payload"]["project_id"] == target_project["id"]
        imported_device = target.repository.get_record(device.id)
        assert imported_device["payload"]["address"] == ""
        assert imported_device["payload"]["native_identity"] == ""
        imported_point = target.repository.get_record(point.id)
        assert imported_point["payload"]["value"] is None
        assert imported_point["payload"]["quality"] == "UNCERTAIN"
        imported_network = target.repository.get_record(network.id)
        assert imported_network["payload"]["ipv4"] == ""
        imported_channel = target.repository.get_record(channel.id)
        assert imported_channel["payload"]["enabled"] is False
        assert imported_channel["payload"]["mode"] == "read_only"
        assert target.custom_svg.list_for_station(station["id"])[0]["name"] == "Fan"
        imported_time = target.time_management.station_time(station["id"])
        assert imported_time["timezone"] == "America/Chicago"
        assert imported_time["ntp_enabled"] is False
        assert imported_time["ntp_servers"] == []
        assert target.time_management.device_sync_permission(station["id"], device.id)["allowed"] is False
        imported_schedule = target.schedules.list(station_id=station["id"])[0]
        assert imported_schedule["name"] == "Fan Schedule"
        assert len(imported_schedule["weekly_events"]) == 1
        assert imported_schedule["point_ids"][0] == point.id
        assert target.analytics.find_points("Temperature") == [point.id]
        assert len(target.dependencies.list_for(component.id)) == 1
    finally:
        source.close()
        target.close()


def test_station_transfer_rejects_object_id_collision_without_partial_import(tmp_path):
    source, _, station, _, _, _, _, _ = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Target")
    try:
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "ahu.avicstation",
                                                          source_core_version="1.0.0.dev111")
        preview = target.station_transfer.inspect_package(package)
        stage = target.station_transfer.stage_import(package, tmp_path / "staging",
            expected_package_id=preview.package_id, target_core_version="1.0.0.dev111")
        # Occupy the Station ID with an existing target object.
        from avic_core.domain.models import Station
        target.repository.save(Station(name="Collision", id=station["id"], project_id=target_project["id"]))
        with pytest.raises(StationTransferError, match="Object ID collision"):
            target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id,
                                                  target_project_id=target_project["id"])
        assert target.repository.get_record(station["id"])["name"] == "Collision"
        assert target.repository.list_records(entity_type="Device") == []
    finally:
        source.close()
        target.close()


def test_station_package_detects_payload_tampering(tmp_path):
    source, _, station, *_ = _source_core(tmp_path / "source")
    try:
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "ahu.avicstation",
                                                          source_core_version="1.0.0.dev111")
        tampered = tmp_path / "tampered.avicstation"
        with zipfile.ZipFile(package) as src, zipfile.ZipFile(tampered, "w") as dst:
            for info in src.infolist():
                data = src.read(info.filename)
                if info.filename == StationTransferManager.PAYLOAD:
                    data += b" "
                dst.writestr(info, data)
        with pytest.raises(StationTransferError, match="integrity"):
            source.station_transfer.inspect_package(tampered)
    finally:
        source.close()


def test_stage_payload_is_rechecked_before_commit(tmp_path):
    source, _, station, *_ = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Target")
    try:
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "ahu.avicstation",
                                                          source_core_version="1.0.0.dev111")
        preview = source.station_transfer.inspect_package(package)
        stage = source.station_transfer.stage_import(package, tmp_path / "staging",
            expected_package_id=preview.package_id, target_core_version="1.0.0.dev111")
        (stage / "station.json").write_text("{}", encoding="utf-8")
        with pytest.raises(StationTransferError, match="staged Station payload integrity"):
            target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id,
                                                  target_project_id=target_project["id"])
    finally:
        source.close()
        target.close()


def test_station_export_blocks_free_text_site_endpoints(tmp_path):
    from avic_core.web_pages.models import WebPageNode

    source, _, station, *_ = _source_core(tmp_path / "source")
    try:
        page = WebPageNode(name="Site", station_id=station["id"], node_kind="site",
                           html='<script>const controller = "192.168.1.20";</script>')
        source.repository.save(page)
        with pytest.raises(StationTransferError, match="site endpoint remains in free-text"):
            source.station_transfer.export_station(source, station["id"], tmp_path / "blocked.avicstation",
                                                   source_core_version="1.0.0.dev111")
    finally:
        source.close()


def test_station_transfer_preflights_auxiliary_id_collisions(tmp_path):
    import sqlite3

    source, _, station, *_ = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Target")
    try:
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "ahu.avicstation",
                                                          source_core_version="1.0.0.dev111")
        preview = source.station_transfer.inspect_package(package)
        stage = source.station_transfer.stage_import(package, tmp_path / "staging",
            expected_package_id=preview.package_id, target_core_version="1.0.0.dev111")
        symbol = source.custom_svg.list_for_station(station["id"])[0]
        svg = source.custom_svg.read_svg(symbol["id"], station_id=station["id"])
        with sqlite3.connect(target.paths.databases / "custom_svg_library.sqlite3") as db:
            db.execute("INSERT INTO custom_svg_assets VALUES(?,?,?,?,?,?,?,?)",
                       (symbol["id"], station["id"], symbol["name"], symbol["category"], symbol["filename"],
                        svg, symbol["sha256"], symbol["created_at"]))
        with pytest.raises(StationTransferError, match="Auxiliary ID collision"):
            target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id,
                                                  target_project_id=target_project["id"])
        with pytest.raises(Exception):
            target.repository.get_record(station["id"])
    finally:
        source.close()
        target.close()


def test_station_transfer_keeps_graphics_fbd_and_web_page_child_graphs(tmp_path):
    from avic_core.graphics.service import GraphicsService
    from avic_core.logic_fbd import FBDService
    from avic_core.web_pages.service import WebPagesService

    source, _, station, _, _, _, point, _ = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Target")
    try:
        svg = source.custom_svg.list_for_station(station["id"])[0]
        graphics = GraphicsService(source)
        graphic_doc = graphics.create(station["id"], "AHU Graphics")
        graphic_doc = graphics.save(graphic_doc["id"], graphic_doc["revision"], [{
            "name": "Fan symbol", "symbol_key": svg["id"], "x": 100, "y": 100,
            "width": 120, "height": 90,
            "bindings": [{"point_id": point.id, "role": "value"}],
        }])
        graphic_element_id = graphic_doc["elements"][0]["id"]

        fbd = FBDService(source)
        logic_doc = fbd.create(station["id"], "Fan Logic")
        from uuid import uuid4
        input_id, output_id = str(uuid4()), str(uuid4())
        logic_doc = fbd.save(logic_doc["id"], logic_doc["revision"], [
            {"id": input_id, "type": "BOOL_INPUT", "name": "Enable", "params": {"value": True}},
            {"id": output_id, "type": "BOOL_OUTPUT", "name": "Fan Command"},
        ], [{"source_node_id": input_id, "source_port": "OUT",
             "target_node_id": output_id, "target_port": "IN"}])

        pages = WebPagesService(source)
        site = pages.create(station["id"], "AHU Site", "site")
        page = pages.create(station["id"], "Overview", "page", parent_id=site["id"], slug="overview")
        page = pages.assign_graphic(page["id"], graphic_doc["id"], page["revision"])

        package = source.station_transfer.export_station(source, station["id"], tmp_path / "full-station.avicstation",
                                                          source_core_version="1.0.0.dev111")
        preview = target.station_transfer.inspect_package(package, target_core_version="1.0.0.dev111")
        stage = target.station_transfer.stage_import(package, tmp_path / "staging",
            expected_package_id=preview.package_id, target_core_version="1.0.0.dev111")
        target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id,
                                              target_project_id=target_project["id"])

        target_graphics = GraphicsService(target).get(graphic_doc["id"])
        assert target_graphics["elements"][0]["id"] == graphic_element_id
        assert target_graphics["elements"][0]["bindings"][0]["point_id"] == point.id
        target_logic = FBDService(target).get(logic_doc["id"])
        assert len(target_logic["nodes"]) == 2
        assert len(target_logic["links"]) == 1
        target_page = WebPagesService(target).get(page["id"])
        assert target_page["graphic_ids"] == [graphic_doc["id"]]
    finally:
        source.close()
        target.close()


@pytest.mark.parametrize("failure_target", ["events", "audit"])
def test_station_import_journal_failure_is_retryable_and_idempotent(tmp_path, monkeypatch, failure_target):
    source, _, station, *_ = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Target")
    try:
        package = source.station_transfer.export_station(
            source, station["id"], tmp_path / "ahu.avicstation",
            source_core_version="1.0.0.dev112",
        )
        preview = target.station_transfer.inspect_package(package, target_core_version="1.0.0.dev112")
        stage = target.station_transfer.stage_import(
            package, tmp_path / "staging", expected_package_id=preview.package_id,
            target_core_version="1.0.0.dev112",
        )

        service = target.events if failure_target == "events" else target.audit
        method_name = "record" if failure_target == "events" else "append"
        original = getattr(service, method_name)
        failed = {"value": False}

        def fail_once(*args, **kwargs):
            is_target_record = (
                args and args[0] == "station.imported"
                if failure_target == "events"
                else kwargs.get("action") == "station.imported"
            )
            if is_target_record and not failed["value"]:
                failed["value"] = True
                raise RuntimeError("simulated journal outage")
            return original(*args, **kwargs)

        monkeypatch.setattr(service, method_name, fail_once)
        result = target.station_transfer.commit_import(
            target, stage, expected_package_id=preview.package_id,
            target_project_id=target_project["id"],
        )
        assert result["journal_status"] == "PENDING_RETRY"
        assert target.repository.get_record(station["id"])["entity_type"] == "Station"

        monkeypatch.setattr(service, method_name, original)
        target.close()
        target = CoreApplication(tmp_path / "target")
        recovered = target.station_transfer_recovery
        assert recovered["recovered"] == 1
        assert recovered["pending"] == 0

        imported_events = target.events.list(station_id=station["id"], event_type="station.imported")
        assert len(imported_events) == 1
        assert target.audit.verify_chain()[0] is True
        with target.repository._connect() as db:
            status = db.execute(
                "SELECT status FROM station_transfer_outbox WHERE operation_id=?",
                (result["operation_id"],),
            ).fetchone()[0]
        assert status == "COMPLETE"
    finally:
        source.close()
        target.close()

def test_station_clone_remaps_engineering_and_auxiliary_ids(tmp_path):
    source, _, station, _, component, device, point, channel = _source_core(tmp_path / "source")
    target = CoreApplication(tmp_path / "target")
    target_project = ProjectStationService(target).create_project("Clone Target")
    try:
        from avic_core.graphics import GraphicsService
        from avic_core.logic_fbd import FBDService
        from avic_core.web_pages import WebPagesService
        from uuid import uuid4
        symbol = source.custom_svg.list_for_station(station["id"])[0]
        graphics = GraphicsService(source)
        graphic = graphics.create(station["id"], "Clone Graphic")
        graphic = graphics.save(graphic["id"], graphic["revision"], [{
            "name": "Temperature", "symbol_key": symbol["id"], "x": 10, "y": 10,
            "width": 80, "height": 60, "bindings": [{"point_id": point.id, "role": "value"}],
        }])
        fbd = FBDService(source)
        logic = fbd.create(station["id"], "Clone Logic")
        input_id, output_id = str(uuid4()), str(uuid4())
        logic = fbd.save(logic["id"], logic["revision"], [
            {"id": input_id, "type": "BOOL_INPUT", "name": "Enable", "params": {"value": True}},
            {"id": output_id, "type": "BOOL_OUTPUT", "name": "Fan", "params": {}},
        ], [{"source_node_id": input_id, "source_port": "OUT", "target_node_id": output_id, "target_port": "IN"}])
        pages = WebPagesService(source)
        site = pages.create(station["id"], "Clone Site", "site")
        page = pages.create(station["id"], "Overview", "page", parent_id=site["id"], slug="overview")
        page = pages.assign_graphic(page["id"], graphic["id"], page["revision"])
        package = source.station_transfer.export_station(source, station["id"], tmp_path / "clone.avicstation", source_core_version="1.0.0.dev145")
        preview = target.station_transfer.inspect_package(package, target_core_version="1.0.0.dev145")
        stage = target.station_transfer.stage_import(package, tmp_path / "staging", expected_package_id=preview.package_id, target_core_version="1.0.0.dev145")
        result = target.station_transfer.commit_import(target, stage, expected_package_id=preview.package_id, target_project_id=target_project["id"], clone=True, clone_station_name="AHU Clone")
        clone_id = result["station_id"]
        assert result["cloned"] is True and clone_id != station["id"]
        clone_station = target.repository.get_record(clone_id)
        assert clone_station["name"] == "AHU Clone"
        assert clone_station["payload"]["project_id"] == target_project["id"]
        cloned_devices = target.repository.list_records(entity_type="Device")
        cloned_points = target.repository.list_records(entity_type="Point")
        assert len(cloned_devices) == 1 and cloned_devices[0]["entity_id"] != device.id
        assert len(cloned_points) == 1 and cloned_points[0]["entity_id"] != point.id
        assert cloned_points[0]["payload"]["device_id"] == cloned_devices[0]["entity_id"]
        cloned_graphics = target.repository.list_records(entity_type="GraphicDocument")
        cloned_logic = target.repository.list_records(entity_type="LogicDocument")
        cloned_pages = target.repository.list_records(entity_type="WebPageNode")
        assert len(cloned_graphics) == 1 and cloned_graphics[0]["entity_id"] != graphic["id"]
        assert len(cloned_logic) == 1 and cloned_logic[0]["entity_id"] != logic["id"]
        assert len(cloned_pages) == 2
        assert all(row["station_id"] == clone_id for row in target.repository.list_records(station_id=clone_id))
        cloned_graphic = GraphicsService(target).get(cloned_graphics[0]["entity_id"])
        assert cloned_graphic["elements"][0]["bindings"][0]["point_id"] == cloned_points[0]["entity_id"]
        assert cloned_graphic["elements"][0]["id"] != graphic["elements"][0]["id"]
        cloned_logic_doc = FBDService(target).get(cloned_logic[0]["entity_id"])
        assert len(cloned_logic_doc["nodes"]) == 2 and len(cloned_logic_doc["links"]) == 1
        assert {node["id"] for node in cloned_logic_doc["nodes"]}.isdisjoint({input_id, output_id})
        cloned_page = WebPagesService(target).get(next(r["entity_id"] for r in cloned_pages if r["name"] == "Overview"))
        assert cloned_page["graphic_ids"] == [cloned_graphics[0]["entity_id"]]
        assert result["activation"] == "NOT_ACTIVATED"
    finally:
        source.close()
        target.close()


@pytest.mark.parametrize("auxiliary, message", [
    ({"dependencies": {"dependencies": [{"station_id": "station", "dependent_id": "missing", "dependency_id": "missing"}]}},
     "dangling entity reference"),
    ({"time_management": {"device_time_permission": [{"station_id": "station", "device_id": "missing"}]}},
     "missing device"),
    ({"schedules": {"schedules": [{"station_id": "station", "schedule_id": "schedule"}],
                    "schedule_bindings": [{"station_id": "station", "schedule_id": "schedule", "point_id": "missing"}]}},
     "missing Point"),
    ({"analytics": {"point_tags": [{"point_id": "missing"}]}},
     "missing Point"),
])
def test_station_transfer_rejects_dangling_auxiliary_references(auxiliary, message):
    from avic_core.transfer.station import StationTransferError, StationTransferManager

    records = [{"entity_id": "station", "entity_type": "Station", "payload": {}}]
    with pytest.raises(StationTransferError, match=message):
        StationTransferManager._validate_auxiliary_references(records, auxiliary)
