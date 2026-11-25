from pathlib import Path

from fastapi.testclient import TestClient

from avic_core.ui import create_ui_app


def _workbench_html() -> str:
    from avic_core import ui as ui_module
    return (Path(ui_module.__file__).parent / "static" / "index.html").read_text(encoding="utf-8")


def test_dev51_workbench_has_locator_history_and_view_changer():
    html = _workbench_html()
    assert 'id="locatorPath"' in html
    assert 'id="locatorGo"' in html
    assert 'id="navBack"' in html and 'id="navForward"' in html
    assert 'id="viewChanger"' in html
    assert "function navigateWorkbench(delta)" in html
    assert "function resolveWorkbenchPath(value)" in html
    assert "state.navHistory" in html


def test_dev51_workbench_palette_is_a_real_switchable_pane():
    html = _workbench_html()
    assert 'id="navigatorTab"' in html and 'id="paletteTab"' in html
    assert 'id="palettePanel"' in html
    assert 'id="paletteSearch"' in html
    for component in ("Насос", "Вентилятор", "Клапан", "AND", "Таймер", "Расписание"):
        assert f'data-palette-item="{component}"' in html
    assert "function setLeftWorkbenchView(view)" in html


def test_dev51_context_menus_cover_entity_views_and_page_actions():
    html = _workbench_html()
    for action in ("properties", "open-view", "copy-path", "open-points", "open-history", "poll-device"):
        assert f"'{action}'" in html or f'"{action}"' in html
    assert "showPageContextMenu" in html
    assert "data-page-context" in html
    assert "entityDefaultView" in html


def test_dev51_menu_has_operational_navigation_groups():
    html = _workbench_html()
    for menu in ("Расписания", "Аварии", "Платформа", "Инженерия"):
        assert menu in html
    for page in ("schedules", "alarms", "events", "trends", "logic", "simulation", "security"):
        assert f'data-menu-action="{page}"' in html
    assert "DEV52" in html


def test_dev51_ui_route_serves_reconstructed_workbench(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert 'id="locatorPath"' in body
    assert 'id="palettePanel"' in body
    assert 'id="viewChanger"' in body
