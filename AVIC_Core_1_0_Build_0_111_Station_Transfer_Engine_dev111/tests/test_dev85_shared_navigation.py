from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def test_all_workspaces_have_same_shared_navigation_and_tree_drawer(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    for route in ("/", "/logic", "/graphics", "/pages"):
        response = client.get(route)
        assert response.status_code == 200
        html = response.text
        assert 'aria-label="Общая навигация AVIC"' in html
        assert 'id="avicSharedTreeToggle"' in html
        assert 'id="avic-shared-tree"' in html
        for key in ("home", "projects", "network", "devices", "points", "graphics", "logic", "repository", "alarms", "trends", "security", "diagnostics"):
            assert f'data-rail-page="{key}"' in html
    assert client.get("/api/engineering/tree").status_code == 200


def test_shared_tree_exposes_physical_point_drag_contract(tmp_path):
    html = TestClient(create_ui_app(data_dir=str(tmp_path))).get("/logic").text
    assert "data-point-id" in html
    assert "setData('point'" in html
    assert "data-fbd-point-id" in html
    assert "setData('fbd-point'" in html


def test_fbd_workspace_polls_shared_runtime_and_displays_live_bound_values(tmp_path):
    html = TestClient(create_ui_app(data_dir=str(tmp_path))).get("/logic").text
    assert "refreshLivePointValues" in html
    assert "/api/engineering/points/runtime" in html
    assert "liveBound" in html
    assert "LIVE" in html
    assert "setInterval(refreshLivePointValues,2000)" in html
