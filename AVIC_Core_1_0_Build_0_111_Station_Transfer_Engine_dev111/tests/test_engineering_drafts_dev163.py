from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from avic_core.ui.drafts import DraftConflict, DraftError, DraftNotFound, EngineeringDraftStore


def test_draft_round_trip_is_durable_and_revisioned(tmp_path):
    path = tmp_path / "drafts.sqlite3"
    store = EngineeringDraftStore(path)
    saved = store.save("graphics", "station-1", "graphic-1",
                       content={"elements": [{"id": "e1", "x": 10}]},
                       base_revision=4, expected_draft_revision=0)
    assert saved["draft_revision"] == 1
    reopened = EngineeringDraftStore(path)
    loaded = reopened.get("graphics", "station-1", "graphic-1")
    assert loaded["content"]["elements"][0]["x"] == 10
    assert loaded["base_revision"] == 4


def test_draft_compare_and_swap_rejects_stale_writer(tmp_path):
    store = EngineeringDraftStore(tmp_path / "drafts.sqlite3")
    first = store.save("fbd", "s1", "fbd1", content={"pages": []},
                       base_revision=2, expected_draft_revision=0)
    assert first["draft_revision"] == 1
    with pytest.raises(DraftConflict):
        store.save("fbd", "s1", "fbd1", content={"pages": [{"name": "stale"}]},
                   base_revision=2, expected_draft_revision=0)
    current = store.get("fbd", "s1", "fbd1")
    assert current["content"] == {"pages": []}


def test_drafts_are_isolated_by_station_and_editor(tmp_path):
    store = EngineeringDraftStore(tmp_path / "drafts.sqlite3")
    store.save("graphics", "s1", "same-id", content={"v": 1},
               base_revision=1, expected_draft_revision=0)
    store.save("graphics", "s2", "same-id", content={"v": 2},
               base_revision=1, expected_draft_revision=0)
    store.save("fbd", "s1", "same-id", content={"v": 3},
               base_revision=1, expected_draft_revision=0)
    assert len(store.list_station("s1")) == 2
    assert store.get("graphics", "s2", "same-id")["content"]["v"] == 2


def test_draft_rejects_unknown_editor_non_json_and_oversized_payload(tmp_path):
    store = EngineeringDraftStore(tmp_path / "drafts.sqlite3")
    with pytest.raises(DraftError):
        store.save("runtime", "s1", "r1", content={}, base_revision=0, expected_draft_revision=0)
    with pytest.raises(DraftError):
        store.save("fbd", "s1", "r1", content={"bad": float("nan")},
                   base_revision=0, expected_draft_revision=0)
    with pytest.raises(DraftError):
        store.save("fbd", "s1", "r1", content={"data": "x" * (5 * 1024 * 1024)},
                   base_revision=0, expected_draft_revision=0)


def test_delete_requires_current_draft_revision_and_is_idempotent(tmp_path):
    store = EngineeringDraftStore(tmp_path / "drafts.sqlite3")
    store.save("web-page", "s1", "page-1", content={"html": "draft"},
               base_revision=7, expected_draft_revision=0)
    with pytest.raises(DraftConflict):
        store.delete("web-page", "s1", "page-1", expected_draft_revision=2)
    assert store.delete("web-page", "s1", "page-1", expected_draft_revision=1)
    assert not store.delete("web-page", "s1", "page-1", expected_draft_revision=1)
    with pytest.raises(DraftNotFound):
        store.get("web-page", "s1", "page-1")



def test_engineering_draft_api_uses_revision_checks_and_is_separate_from_publish(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    url = "/api/engineering-drafts/graphics/station-1/graphic-1"
    payload = {
        "base_revision": 3,
        "expected_draft_revision": 0,
        "content": {"elements": [{"id": "fan-1", "x": 25}]},
    }
    saved = client.put(url, json=payload)
    assert saved.status_code == 200
    assert saved.json()["draft_revision"] == 1
    assert client.get(url).json()["content"] == payload["content"]
    assert len(client.get("/api/stations/station-1/engineering-drafts").json()["drafts"]) == 1

    stale = client.put(url, json={**payload, "content": {"elements": []}})
    assert stale.status_code == 409
    assert client.get(url).json()["content"] == payload["content"]

    removed = client.delete(url + "?expected_draft_revision=1")
    assert removed.status_code == 200
    assert removed.json()["deleted"] is True
    assert client.get(url).status_code == 404


def test_save_manager_script_is_served_only_as_editor_support_and_injected(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    script = client.get("/avic-static/save-manager.js")
    assert script.status_code == 200
    assert "indexedDB" in script.text
    assert "prepareForExit" in script.text
    assert "getExitStatus" in script.text
    assert "shouldWarnBeforeUnload" in script.text
    assert "JSON.parse(encode(config.getContent()))" in script.text
    exit_start = script.text.index("async function prepareForExit")
    exit_end = script.text.index("function getExitStatus", exit_start)
    assert "await recoveryReady" not in script.text[exit_start:exit_end]
    assert "const operation = flush(target" in script.text[exit_start:exit_end]
    assert "beforeunload" not in script.text
    assert "expected_draft_revision" in script.text
    assert "recoveryReady" in script.text
    assert "remoteContent" in script.text
    assert "recoveryPending" in script.text
    assert "preservedMatches" in script.text
    assert "localWrite = Promise.resolve()" in script.text
    assert "await localWrite.catch" in script.text
    assert script.text.index("const local = await persistLocal(snapshot, baseRevision)") < script.text.index("await recoveryReady.catch")
    assert "pendingSnapshot = { snapshot, baseRevision }" in script.text
    assert "flush(next?.snapshot" in script.text
    assert "другой черновик" in script.text
    for path in ("/graphics", "/logic", "/repository?section=WebApplication"):
        response = client.get(path)
        assert response.status_code == 200
        assert "/avic-static/save-manager.js" in response.text
    graphics = client.get("/graphics").text
    assert "Элемент удалён из текущей редакции" in graphics
    assert "saveDraft?.schedule()" in graphics
    repository = client.get("/repository?section=WebApplication").text
    assert "Изображение загружено в Repository станции." in repository
    assert "saveDraft?.schedule()" in repository



def test_engineering_draft_reads_reject_untrusted_cross_origin_requests(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    url = "/api/engineering-drafts/graphics/station-1/graphic-1"
    payload = {
        "base_revision": 0,
        "expected_draft_revision": 0,
        "content": {"elements": []},
    }
    saved = client.put(url, json=payload)
    assert saved.status_code == 200

    blocked = client.get(url, headers={"Origin": "https://untrusted.example"})
    assert blocked.status_code == 403
    allowed = client.get(url, headers={"Origin": "http://127.0.0.1"})
    assert allowed.status_code == 200

    blocked_list = client.get(
        "/api/stations/station-1/engineering-drafts",
        headers={"Origin": "https://untrusted.example"},
    )
    assert blocked_list.status_code == 403



def test_save_manager_javascript_syntax_with_node_when_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed; browser asset syntax check is optional")
    script = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "save-manager.js"
    result = subprocess.run(
        [node, "--check", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr



def test_application_exit_flow_is_available_on_all_workspaces(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    script = client.get("/avic-static/application-lifecycle.js")
    assert script.status_code == 200
    assert "beforeunload" in script.text
    assert "prepareForExit" in script.text
    assert "Выйти с потерей изменений" in script.text
    assert "noActiveEditor" in script.text
    assert "Открытых инженерных редакторов" in script.text
    assert "STOP AVIC CORE" in script.text
    assert "/api/core/shutdown-preview" in script.text
    assert "/api/core/shutdown" in script.text
    assert "Core и работающий Runtime не останавливаются" in script.text

    for path in ("/", "/graphics", "/logic", "/repository?section=WebApplication"):
        page = client.get(path)
        assert page.status_code == 200
        assert 'id="avicApplicationExit"' in page.text
        assert 'id="avicCoreStop"' in page.text
        assert "/avic-static/application-lifecycle.js" in page.text

    graphics = client.get("/graphics").text
    assert "/avic-static/save-manager.js" in graphics
    home = client.get("/").text
    assert "/avic-static/save-manager.js" not in home


def test_application_lifecycle_javascript_syntax_with_node_when_available():
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node.js is not installed; browser asset syntax check is optional")
    script = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "application-lifecycle.js"
    result = subprocess.run(
        [node, "--check", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr



def test_core_shutdown_api_requires_explicit_confirmation_and_requests_process_exit(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    app = create_ui_app(data_dir=str(tmp_path / "core-shutdown"))
    client = TestClient(app)
    preview = client.get("/api/core/shutdown-preview")
    assert preview.status_code == 200
    assert preview.json()["core_state"] == "RUNNING"
    assert preview.json()["confirmation_required"] == "STOP AVIC CORE"

    invalid = client.post("/api/core/shutdown", json={"confirmation": "STOP"})
    assert invalid.status_code == 422
    assert app.state.core.closed is False

    requested = []
    app.state.process_shutdown_callback = lambda: requested.append(True)
    stopped = client.post("/api/core/shutdown", json={"confirmation": "STOP AVIC CORE"})
    assert stopped.status_code == 200
    assert stopped.json()["status"] == "SHUTTING_DOWN"
    assert app.state.core.closed is True
    assert requested == [True]


def test_core_shutdown_api_does_not_exit_when_worker_shutdown_is_not_confirmed(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    app = create_ui_app(data_dir=str(tmp_path / "core-shutdown-blocked"))
    client = TestClient(app)
    def fail_shutdown():
        raise RuntimeError("simulated worker did not stop")
    app.state.core.fbd_execution.close = fail_shutdown
    requested = []
    app.state.process_shutdown_callback = lambda: requested.append(True)

    stopped = client.post("/api/core/shutdown", json={"confirmation": "STOP AVIC CORE"})
    assert stopped.status_code == 409
    assert "Безопасная остановка отменена" in stopped.json()["detail"]
    assert app.state.core.closed is False
    assert app.state.core.shutdown_preview()["core_state"] == "SHUTDOWN_BLOCKED"
    assert requested == []



def test_asgi_shutdown_event_closes_core_services(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app

    app = create_ui_app(data_dir=str(tmp_path / "asgi-shutdown"))
    with TestClient(app) as client:
        assert client.get("/api/core/shutdown-preview").status_code == 200
        core = app.state.core
        assert core.closed is False
    assert core.closed is True
    assert core.fbd_execution._closed is True
