"""DEV196: managed BACnet/IP read -> FBD point -> fan graphic -> published page."""
import time

from fastapi.testclient import TestClient

from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.ui import create_ui_app


class FakeTrendBacnetController:
    """Deterministic ReadProperty peer used in CI; no physical device is contacted."""

    def __init__(self):
        self.calls = []

    def read_property(self, address, device_instance, object_type, object_instance,
                      property_id, array_index=None):
        self.calls.append((address, device_instance, object_type, object_instance,
                           property_id, array_index))
        if property_id != 85:
            raise AssertionError("the demo must read Present_Value only")
        return True


def _studio_graph(physical_point_id: str, exposed_point_id: str) -> dict:
    return {
        "format": "AVIC-FBD-STRATEGY",
        "version": "1.1.1",
        "project": "BACnet fan demo",
        "pages": [{
            "id": "ahu-main", "name": "Основная", "code": "P1",
            "modules": [
                {"id": "bacnet-run", "type": "POINT_INPUT", "name": "BACnet Fan Status",
                 "x": 20, "y": 40, "params": {"pointRef": {"id": physical_point_id}},
                 "ins": [], "outs": [{"id": "bacnet-out", "name": "OUT", "type": "bool"}]},
                {"id": "safety", "type": "BOOL_INPUT", "name": "Тепловая защита",
                 "x": 20, "y": 180, "params": {"value": True}, "ins": [],
                 "outs": [{"id": "safety-out", "name": "OUT", "type": "bool"}]},
                {"id": "permit", "type": "AND", "name": "Разрешение вентилятора",
                 "x": 250, "y": 100, "params": {},
                 "ins": [{"id": "permit-a", "name": "A", "type": "bool"},
                         {"id": "permit-b", "name": "B", "type": "bool"}],
                 "outs": [{"id": "permit-out", "name": "OUT", "type": "bool"}]},
                {"id": "run-output", "type": "BOOL_OUTPUT", "name": "FAN_RUN",
                 "x": 470, "y": 100, "params": {},
                 "ins": [{"id": "run-in", "name": "IN", "type": "bool"}], "outs": []},
            ],
        }],
        "links": [
            {"id": "l1", "pageId": "ahu-main", "from": "out:bacnet-run:0",
             "to": "in:permit:0", "signalType": "bool"},
            {"id": "l2", "pageId": "ahu-main", "from": "out:safety:0",
             "to": "in:permit:1", "signalType": "bool"},
            {"id": "l3", "pageId": "ahu-main", "from": "out:permit:0",
             "to": "in:run-output:0", "signalType": "bool"},
        ],
        "references": [],
        "fbdPoints": [{
            "id": exposed_point_id,
            "tag": "AHU_FAN_RUN",
            "name": "FAN_RUN",
            "path": "AHU-01/FBD/AHU_FAN_RUN",
            "dataType": "digital",
            "unit": "",
            "direction": "output",
            "source": {"pageId": "ahu-main", "moduleId": "permit",
                       "portIndex": 0, "portId": "permit-out", "portName": "OUT"},
            "license": {"status": "pending_core_registration"},
        }],
    }


def test_managed_bacnet_point_flows_through_fbd_to_published_fan_page(tmp_path):
    app = create_ui_app(data_dir=str(tmp_path / "dev196"))
    controller = FakeTrendBacnetController()
    with TestClient(app) as client:
        manifest = client.get("/api/ui/manifest").json()
        health = client.get("/api/ui/health").json()
        assert manifest["version"] == "1.0.0.dev196"
        assert manifest["capabilities"]["driver_manager"] is True
        assert manifest["capabilities"]["bacnet_ip_polling"] == "managed-read-only-present-value"
        assert manifest["capabilities"]["field_writes_enabled"] is False
        assert health["version"] == "1.0.0.dev196"
        project = client.post("/api/projects", json={"name": "DEV196 BACnet AHU"}).json()
        station = client.post("/api/stations", json={
            "project_id": project["id"], "name": "AHU-01",
        }).json()

        # Create the same network-bound BACnet driver that the Discovery UI creates.
        driver = app.state.driver_manager.create_instance(
            station["id"], "bacnet-ip", "Trend BACnet/IP",
            config={
                "network_id": "test-lan", "interface_name": "Test Ethernet",
                "local_address": "192.0.2.10", "subnet_cidr": "192.0.2.0/24",
                "udp_port": 47808, "timeout": 2, "poll_interval_seconds": 5,
                "bindings": [],
            })
        driver_id = driver["id"]
        native = "bacnet:binary-input:1"
        inspection = {
            "protocol": "BACnet/IP", "network_id": "test-lan",
            "device": {
                "native_identity": "bacnet:device:1234",
                "address": "192.0.2.50:47808", "device_instance": 1234,
                "name": "Trend BACnet Controller", "manufacturer": "Trend",
                "model": "BACnet Controller", "identity_sources": {"manufacturer": "BACnet Vendor ID"},
            },
            "points": [{
                "native_identity": native, "name": "Fan Status",
                "data_type": "binary-input", "direction": "input",
                "unit": "", "object_type": "binary-input",
            }],
        }
        import_payload = {
            "driver_instance_id": driver_id, "inspection": inspection,
            "selected_native_ids": [native], "import_all": False,
        }
        preview = client.post(
            f"/api/stations/{station['id']}/protocol-devices/import-preview",
            json=import_payload,
        )
        assert preview.status_code == 200, preview.text
        assert preview.json()["bindings_validated"] is True
        imported = client.post(
            f"/api/stations/{station['id']}/protocol-devices/import",
            json=import_payload,
        )
        assert imported.status_code == 200, imported.text
        physical_id = imported.json()["points_added"][0]
        saved_driver = app.state.driver_manager.get_instance(driver_id)
        assert saved_driver["config"]["bindings"][0]["point_id"] == physical_id
        assert saved_driver["config"]["bindings"][0]["object_type"] == 3

        # Use the managed Driver Manager lifecycle with a fake ReadProperty peer
        # so CI never needs access to plant hardware.
        app.state.driver_manager.register_adapter_factory(
            "bacnet-ip",
            lambda core, instance: BacnetIpPointAdapter(
                controller, core.point_runtime, instance.id,
                [BacnetIpPointBinding(
                    physical_id, ("192.0.2.50", 47808), 1234, 3, 1, property_id=85,
                )],
            ),
        )
        driver_state = app.state.driver_manager.start_instance(
            driver_id, poll_interval_seconds=0.1)
        assert driver_state["field_read_enabled"] is True
        deadline = time.monotonic() + 3.0
        sample = app.state.core.point_runtime.read(physical_id)
        while sample.quality != "GOOD" and time.monotonic() < deadline:
            time.sleep(0.02)
            sample = app.state.core.point_runtime.read(physical_id)
        assert sample.value is True and sample.quality == "GOOD"
        assert controller.calls and controller.calls[0][4] == 85

        exposed_id = "b6a8a9a2-6f76-4e12-8a36-1b2c3d4e5f60"
        created = client.post(f"/api/stations/{station['id']}/fbd-studio", json={
            "name": "AHU-01 Fan Logic",
            "data": _studio_graph(physical_id, exposed_id),
        })
        assert created.status_code == 201, created.text
        source = created.json()
        compiled = client.post(f"/api/fbd-studio/{source['id']}/compile", json={
            "expected_revision": source["revision"],
        })
        assert compiled.status_code == 200, compiled.text
        core_document_id = compiled.json()["core_document"]["id"]
        assert compiled.json()["registered_fbd_points"] == 1

        started = client.post(f"/api/fbd-runtime/{core_document_id}/start", json={
            "interval_ms": 100, "background": False,
        })
        assert started.status_code == 200, started.text
        try:
            tick = client.post(f"/api/fbd-runtime/{core_document_id}/tick", json={})
            assert tick.status_code == 200, tick.text
            assert tick.json()["runtime_published"] is True
            assert app.state.core.point_runtime.read(exposed_id).value is True
            assert app.state.core.point_runtime.read(exposed_id).quality == "GOOD"
            # Bind the published fan animation to the FBD virtual point, not to a copied value.
            graphic = client.post(f"/api/stations/{station['id']}/graphics", json={
                "name": "AHU-01 Fan Mimic",
            }).json()
            saved_graphic = client.put(f"/api/graphics/{graphic['id']}", json={
                "expected_revision": graphic["revision"],
                "elements": [{
                    "id": "f1a10000-0000-4000-8000-000000000001", "name": "Вентилятор SF-01", "symbol_key": "fan",
                    "x": 120, "y": 100, "width": 180, "height": 140,
                    "rotation": 0, "layer": 1,
                    "bindings": [
                        {"point_id": exposed_id, "role": "feedback", "binding_type": "status",
                         "target_property": "animation", "settings": {"converter": "boolean"}},
                        {"point_id": exposed_id, "role": "quality", "binding_type": "status",
                         "target_property": "status", "settings": {}},
                    ],
                }],
            })
            assert saved_graphic.status_code == 200, saved_graphic.text

            site = client.post("/api/web-pages", json={
                "station_id": station["id"], "name": "Здание", "kind": "site",
            }).json()
            page = client.post("/api/web-pages", json={
                "station_id": station["id"], "name": "AHU-01", "kind": "page",
                "parent_id": site["id"], "slug": "ahu-01",
            }).json()
            assigned = client.post(f"/api/web-pages/{page['id']}/graphics", json={
                "expected_revision": page["revision"], "graphic_id": graphic["id"],
            })
            assert assigned.status_code == 200, assigned.text
            saved_page = client.put(f"/api/web-pages/{page['id']}", json={
                "expected_revision": assigned.json()["revision"],
                "layout": [
                    {"type": "heading", "text": "Приточная установка AHU-01",
                     "x": 24, "y": 20, "width": 600, "height": 58},
                    {"type": "value", "label": "Состояние BACnet-контроллера",
                     "point_id": physical_id, "x": 24, "y": 100, "width": 260, "height": 90},
                    {"type": "value", "label": "Состояние FAN_RUN по FBD",
                     "point_id": exposed_id, "x": 24, "y": 210, "width": 260, "height": 90},
                    {"type": "graphic", "graphic_id": graphic["id"],
                     "label": "Вентилятор SF-01", "x": 320, "y": 90, "width": 700, "height": 520},
                ],
            })
            assert saved_page.status_code == 200, saved_page.text
            published = client.post(f"/api/web-pages/{page['id']}/publish", json={
                "expected_revision": saved_page.json()["revision"],
            })
            assert published.status_code == 200, published.text

            rendered = client.get(f"/published/{station['id']}/ahu-01")
            assert rendered.status_code == 200, rendered.text
            assert "Приточная установка AHU-01" in rendered.text
            assert physical_id in rendered.text and exposed_id in rendered.text
            assert f"/published-graphics/{station['id']}/{graphic['id']}" in rendered.text

            fan_runtime = client.get(
                f"/published-graphics/{station['id']}/{graphic['id']}/bindings?page_id={page['id']}"
            )
            assert fan_runtime.status_code == 200, fan_runtime.text
            assert any(item["value"] is True and item["quality"] == "GOOD"
                       for item in fan_runtime.json()["bindings"].values())

        finally:
            client.post(f"/api/fbd-runtime/{core_document_id}/stop")
            app.state.driver_manager.stop_instance(driver_id)
            app.state.core.close()


def test_dev196_bacnet_discovery_import_and_driver_manager_ui_are_wired_and_parse(tmp_path):
    import re
    import shutil
    import subprocess
    from pathlib import Path

    root = Path(__file__).parents[1]
    index = (root / "avic_core" / "ui" / "static" / "index.html").read_text(encoding="utf-8")
    logic = (root / "avic_core" / "ui" / "static" / "logic.html").read_text(encoding="utf-8")
    pages = (root / "avic_core" / "ui" / "static" / "pages.html").read_text(encoding="utf-8")

    assert "state.bacnetInspection" in index
    assert "/protocol-devices/import-preview" in index
    assert "/protocol-devices/import" in index
    assert "function driversWorkspace()" in index
    assert "data-driver-start" in index and "data-driver-stop" in index
    assert "POINT_INPUT" in logic
    assert "loadPointCatalog()" in pages
    assert "bindDroppedPagePoint(pointId,index)" in pages

    node = shutil.which("node")
    if node:
        scripts = re.findall(r"<script[^>]*>(.*?)</script>", index, re.S)
        assert scripts, "index.html must contain its inline application script"
        for number, script in enumerate(scripts):
            if not script.strip():
                continue
            source = tmp_path / f"index-inline-{number}.js"
            source.write_text(script, encoding="utf-8")
            result = subprocess.run([node, "--check", str(source)], capture_output=True, text=True, timeout=20)
            assert result.returncode == 0, result.stdout + result.stderr
