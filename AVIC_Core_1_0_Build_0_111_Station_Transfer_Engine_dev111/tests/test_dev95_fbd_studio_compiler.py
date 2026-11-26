from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _station(client):
    project = client.app.state.project_station.create_project("DEV95 Project")
    return client.app.state.project_station.create_station(project["id"], "DEV95 Station")


def _studio_graph():
    return {
        "format": "AVIC-FBD-STRATEGY", "version": "1.1.1", "project": "Fan Permit",
        "pages": [{"id": "page-main", "name": "Основная", "code": "P1", "modules": [
            {"id": "start", "type": "BOOL_INPUT", "name": "Команда Пуск", "x": 30, "y": 40,
             "params": {"value": True}, "ins": [], "outs": [{"id": "start-out", "name": "OUT", "type": "bool"}]},
            {"id": "safe", "type": "BOOL_INPUT", "name": "Защита исправна", "x": 30, "y": 180,
             "params": {"value": True}, "ins": [], "outs": [{"id": "safe-out", "name": "OUT", "type": "bool"}]},
            {"id": "and", "type": "AND", "name": "Разрешение", "x": 260, "y": 100,
             "params": {}, "ins": [{"id": "and-a", "name": "A", "type": "bool"}, {"id": "and-b", "name": "B", "type": "bool"}],
             "outs": [{"id": "and-out", "name": "OUT", "type": "bool"}]},
            {"id": "out", "type": "BOOL_OUTPUT", "name": "RUN", "x": 480, "y": 100,
             "params": {}, "ins": [{"id": "out-in", "name": "IN", "type": "bool"}], "outs": []},
        ]}],
        "links": [
            {"id": "l1", "pageId": "page-main", "from": "out:start:0", "to": "in:and:0", "signalType": "bool"},
            {"id": "l2", "pageId": "page-main", "from": "out:safe:0", "to": "in:and:1", "signalType": "bool"},
            {"id": "l3", "pageId": "page-main", "from": "out:and:0", "to": "in:out:0", "signalType": "bool"},
        ],
        "references": [], "fbdPoints": [],
    }


def test_fbd_studio_compile_preview_and_compile_to_executable_core_graph(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "AHU Permit", "data": _studio_graph()})
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True
    assert preview.json()["source_blocks"] == 4
    assert preview.json()["source_links"] == 3

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    result = compiled.json()
    core_doc = result["core_document"]
    assert result["compiled_blocks"] == 4
    assert result["compiled_links"] == 3
    assert result["field_writes_enabled"] is False
    assert result["runtime_published"] is False

    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["RUN"] is True

    # Compilation creates a separate executable document; it never rewrites Studio.
    loaded = client.get(f"/api/fbd-studio/{source['id']}").json()
    assert loaded["revision"] == source["revision"]
    assert loaded["data"] == _studio_graph()


def test_fbd_studio_compiler_refuses_unknown_semantics_without_creating_core_document(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"][0]["modules"][2]["type"] = "PID_LOOP"
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Unsupported PID", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    before = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]

    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200
    assert preview.json()["compilable"] is False
    assert any("PID_LOOP" in issue for issue in preview.json()["issues"])

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 400
    after = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]
    assert after == before


def test_fbd_studio_compiler_rejects_stale_revision(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Stale", "data": _studio_graph()})
    source = created.json()
    response = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                           json={"expected_revision": source["revision"] + 1})
    assert response.status_code == 409
    assert "CONCURRENCY_CONFLICT" in response.json()["detail"]


def test_fbd_studio_compiler_preserves_multiple_pages(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"].append({"id": "page-second", "name": "Нагрев", "code": "P2", "modules": [
        {"id": "heat", "type": "FLOAT_INPUT", "name": "Температура подачи", "x": 40, "y": 40,
         "params": {"value": 35.0}, "ins": [], "outs": [{"id": "heat-out", "name": "OUT", "type": "num"}]}
    ]})
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Two pages", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    pages = compiled.json()["core_document"]["pages"]
    assert [page["name"] for page in pages] == ["Основная", "Нагрев"]
    assert len(compiled.json()["core_document"]["nodes"]) == 5
    assert {node["page_id"] for node in compiled.json()["core_document"]["nodes"]} == {p["id"] for p in pages}


def test_fbd_studio_compile_is_idempotent_for_same_source_revision(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Idempotent", "data": _studio_graph()})
    source = created.json()
    first = client.post(f"/api/fbd-studio/{source['id']}/compile",
                        json={"expected_revision": source["revision"]})
    second = client.post(f"/api/fbd-studio/{source['id']}/compile",
                         json={"expected_revision": source["revision"]})
    assert first.status_code == second.status_code == 200
    assert first.json()["core_document"]["id"] == second.json()["core_document"]["id"]
    assert second.json()["already_compiled"] is True
    docs = client.get(f"/api/stations/{station['id']}/fbd").json()["documents"]
    assert len(docs) == 1


def test_fbd_studio_compiler_normalizes_values_edited_as_text_in_ui(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"][0]["modules"][0]["params"]["value"] = "Да"
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Text values", "data": data})
    source = created.json()
    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200 and preview.json()["compilable"] is True
    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    nodes = compiled.json()["core_document"]["nodes"]
    start = next(node for node in nodes if node["name"] == "Команда Пуск")
    assert start["params"]["value"] is True



def test_fbd_studio_rejects_module_id_collision_across_pages(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.app.state.project_station.create_project("Global IDs")
    station = client.app.state.project_station.create_station(project["id"], "Station")
    data = {
        "pages": [
            {"id": "page-a", "name": "A", "modules": [
                {"id": "same-module-id", "type": "BOOL_INPUT", "ins": [], "outs": []}
            ]},
            {"id": "page-b", "name": "B", "modules": [
                {"id": "same-module-id", "type": "BOOL_INPUT", "ins": [], "outs": []}
            ]},
        ],
        "links": [],
    }
    response = client.post(
        f"/api/stations/{station['id']}/fbd-studio",
        json={"name": "Duplicate global identity", "data": data},
    )
    assert response.status_code == 400
    assert "unique across the entire project" in response.json()["detail"]



def _studio_graph_with_connective():
    data = _studio_graph()
    data["pages"].append({
        "id": "page-fan", "name": "Вентилятор", "code": "P2", "modules": [
            {"id": "proxy-start", "type": "CONNECTIVE", "name": "Connective Команда Пуск",
             "params": {"referenceId": "ref-start-fan", "label": "Команда Пуск",
                        "sourcePageId": "page-main", "sourceModuleId": "start",
                        "sourcePort": 0, "targetPageId": "page-fan"},
             "ins": [], "outs": [{"id": "proxy-out", "name": "OUT", "type": "bool"}]},
            {"id": "remote-run", "type": "BOOL_OUTPUT", "name": "REMOTE_RUN",
             "params": {}, "ins": [{"id": "remote-in", "name": "IN", "type": "bool"}], "outs": []},
        ],
    })
    data["pages"][0]["modules"].append({
        "id": "marker-start-fan", "type": "TO_CONNECTIVE", "name": "To Connective Команда Пуск",
        "params": {"referenceId": "ref-start-fan", "targetPageId": "page-fan"},
        "ins": [{"id": "marker-in", "name": "OUT", "type": "bool"}], "outs": [],
    })
    data["links"].append({
        "id": "cross-link-start-fan", "pageId": "page-fan",
        "from": "out:proxy-start:0", "to": "in:remote-run:0", "signalType": "bool",
    })
    data["references"] = [{
        "id": "ref-start-fan", "sourcePageId": "page-main", "sourceModuleId": "start",
        "sourcePort": 0, "targetPageId": "page-fan",
        "proxyModuleId": "proxy-start", "toModuleId": "marker-start-fan",
    }]
    return data


def test_fbd_studio_compiles_connective_alias_to_core_cross_page_runtime(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph_with_connective()
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Cross-page Connective", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()

    preview = client.post(f"/api/fbd-studio/{source['id']}/compile-preview",
                          json={"expected_revision": source["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is True, preview.json()
    assert preview.json()["source_blocks"] == 5
    assert preview.json()["source_links"] == 4

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    result = compiled.json()
    core_doc = result["core_document"]
    assert result["compiled_blocks"] == 5
    assert result["compiled_links"] == 4
    assert len(core_doc["connectives"]) == 1
    assert len(core_doc["links"]) == 3
    assert all(node["type"] not in {"CONNECTIVE", "TO_CONNECTIVE"} for node in core_doc["nodes"])

    simulation = client.post(f"/api/fbd/{core_doc['id']}/simulate", json={})
    assert simulation.status_code == 200, simulation.text
    assert simulation.json()["outputs"]["RUN"] is True
    assert simulation.json()["outputs"]["REMOTE_RUN"] is True
    assert simulation.json()["field_writes_performed"] is False


def test_fbd_studio_rejects_connective_reference_with_missing_proxy(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph_with_connective()
    data["references"][0]["proxyModuleId"] = "missing-proxy"
    response = client.post(f"/api/stations/{station['id']}/fbd-studio",
                           json={"name": "Missing proxy", "data": data})
    assert response.status_code == 400
    assert "proxy does not exist" in response.json()["detail"]


def test_fbd_studio_rejects_connective_proxy_with_wrong_signal_type(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph_with_connective()
    data["pages"][1]["modules"][0]["outs"][0]["type"] = "float"
    response = client.post(f"/api/stations/{station['id']}/fbd-studio",
                           json={"name": "Wrong proxy type", "data": data})
    assert response.status_code == 400
    assert "signal type differs" in response.json()["detail"]


def test_fbd_studio_recompile_does_not_reuse_legacy_compiler_artifact(tmp_path):
    from avic_core.logic_fbd import FBDService

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph_with_connective()
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Compiler versioning", "data": data})
    assert created.status_code == 201, created.text
    source = created.json()

    legacy_marker = f"AVIC_FBD_STUDIO_SOURCE={source['id']};REV={source['revision']}"
    legacy = FBDService(client.app.state.core).create(
        station["id"], "Legacy compiler output", legacy_marker
    )

    compiled = client.post(f"/api/fbd-studio/{source['id']}/compile",
                           json={"expected_revision": source["revision"]})
    assert compiled.status_code == 200, compiled.text
    assert compiled.json()["core_document"]["id"] != legacy["id"]
    assert len(compiled.json()["core_document"]["connectives"]) == 1


def test_fbd_studio_page_copy_and_delete_are_reference_aware():
    from pathlib import Path

    html_path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
    html = html_path.read_text(encoding="utf-8")
    assert "const incomingRefs=state.references.filter(r=>r.targetPageId===pg.id)" in html
    assert "const outgoingRefs=state.references.filter(r=>r.sourcePageId===pg.id)" in html
    assert "deadModuleIds" in html
    assert "state.links.filter(l=>" in html


def test_fbd_studio_compiler_rejects_cycle_created_by_cross_page_connectives(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station = _station(client)
    data = _studio_graph()
    data["pages"].append({
        "id": "page-fan", "name": "Вентилятор", "code": "P2", "modules": [
            {"id": "fan-and", "type": "AND", "name": "Межстраничный цикл",
             "params": {}, "ins": [
                 {"id": "fan-a", "name": "A", "type": "bool"},
                 {"id": "fan-b", "name": "B", "type": "bool"}],
             "outs": [{"id": "fan-out", "name": "OUT", "type": "bool"}]},
            {"id": "proxy-main-and", "type": "CONNECTIVE", "name": "Из основной страницы",
             "params": {"referenceId": "ref-main-fan", "label": "Разрешение",
                        "sourcePageId": "page-main", "sourceModuleId": "and",
                        "sourcePort": 0, "targetPageId": "page-fan"},
             "ins": [], "outs": [{"id": "proxy-main-out", "name": "OUT", "type": "bool"}]},
        ],
    })
    data["pages"][0]["modules"].append({
        "id": "proxy-fan-main", "type": "CONNECTIVE", "name": "Из вентилятора",
        "params": {"referenceId": "ref-fan-main", "label": "Межстраничный цикл",
                   "sourcePageId": "page-fan", "sourceModuleId": "fan-and",
                   "sourcePort": 0, "targetPageId": "page-main"},
        "ins": [], "outs": [{"id": "proxy-fan-out", "name": "OUT", "type": "bool"}],
    })
    data["pages"][0]["modules"].append({
        "id": "marker-main-fan", "type": "TO_CONNECTIVE", "name": "To fan",
        "params": {"referenceId": "ref-main-fan", "targetPageId": "page-fan"},
        "ins": [{"id": "marker-main-in", "name": "OUT", "type": "bool"}], "outs": [],
    })
    data["pages"][1]["modules"].append({
        "id": "marker-fan-main", "type": "TO_CONNECTIVE", "name": "To main",
        "params": {"referenceId": "ref-fan-main", "targetPageId": "page-main"},
        "ins": [{"id": "marker-fan-in", "name": "OUT", "type": "bool"}], "outs": [],
    })
    data["links"] = [
        link for link in data["links"] if link["id"] != "l2"
    ] + [
        {"id": "cycle-a", "pageId": "page-fan",
         "from": "out:proxy-main-and:0", "to": "in:fan-and:0", "signalType": "bool"},
        {"id": "cycle-b", "pageId": "page-main",
         "from": "out:proxy-fan-main:0", "to": "in:and:1", "signalType": "bool"},
    ]
    data["references"] = [
        {"id": "ref-main-fan", "sourcePageId": "page-main", "sourceModuleId": "and",
         "sourcePort": 0, "targetPageId": "page-fan",
         "proxyModuleId": "proxy-main-and", "toModuleId": "marker-main-fan"},
        {"id": "ref-fan-main", "sourcePageId": "page-fan", "sourceModuleId": "fan-and",
         "sourcePort": 0, "targetPageId": "page-main",
         "proxyModuleId": "proxy-fan-main", "toModuleId": "marker-fan-main"},
    ]
    created = client.post(f"/api/stations/{station['id']}/fbd-studio",
                          json={"name": "Cross-page cycle", "data": data})
    assert created.status_code == 201, created.text
    preview = client.post(f"/api/fbd-studio/{created.json()['id']}/compile-preview",
                          json={"expected_revision": created.json()["revision"]})
    assert preview.status_code == 200, preview.text
    assert preview.json()["compilable"] is False
    assert any("циклическую зависимость" in issue for issue in preview.json()["issues"])


def test_fbd_studio_page_copy_assigns_unique_page_code():
    from pathlib import Path

    html_path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
    html = html_path.read_text(encoding="utf-8")
    copy_start = html.index("function copyActivePage(){")
    copy_end = html.index("\nfunction deleteActivePage(){", copy_start)
    copy_function = html[copy_start:copy_end]
    assert "const usedPageCodes=new Set(state.pages.map" in copy_function
    assert "c.code='P'+pageNumber" in copy_function


def test_fbd_studio_page_check_ignores_to_connective_navigation_marker():
    from pathlib import Path

    html_path = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"
    html = html_path.read_text(encoding="utf-8")
    check_start = html.index("function check(){")
    check_end = html.index("\nfunction undo(){", check_start)
    check_function = html[check_start:check_end]
    assert "if(m.type==='TO_CONNECTIVE')return" in check_function
