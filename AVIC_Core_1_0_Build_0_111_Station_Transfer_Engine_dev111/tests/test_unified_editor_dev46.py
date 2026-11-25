from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "avic_core/ui/static/pages.html").read_text(encoding="utf-8")
GRAPHICS = (ROOT / "avic_core/ui/static/graphics.html").read_text(encoding="utf-8")


def test_graphics_editor_is_embedded_in_pages_workspace():
    assert 'id="graphicsFrame"' in PAGES
    assert "openGraphicEditor" in PAGES
    assert "window.open('/graphics" not in PAGES
    assert 'data-tab="graphics">Редактор мнемосхем</button>' in PAGES


def test_graphics_save_notifies_parent_workspace():
    assert "avic-graphics-saved" in GRAPHICS
    assert "postMessage" in GRAPHICS
    assert "avic-graphics-saved" in PAGES


def test_web_pages_tree_has_native_context_menu_and_actions():
    assert "addEventListener('contextmenu'" in PAGES
    assert "showNodeMenu" in PAGES
    assert "data-node-action" in PAGES
    for action in ("new-folder", "new-page", "rename", "move", "delete", "open-code"):
        assert action in PAGES


def test_embedded_graphics_mode_hides_separate_workbench_chrome():
    assert "embedded" in GRAPHICS
    assert "html.embedded .top" in GRAPHICS
    assert "stationTarget" in GRAPHICS
