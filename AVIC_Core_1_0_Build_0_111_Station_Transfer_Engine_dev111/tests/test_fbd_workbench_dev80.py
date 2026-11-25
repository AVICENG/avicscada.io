from pathlib import Path


def test_fbd_workbench_has_responsive_page_tabs_and_context_actions():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "grid-template-columns:repeat(auto-fit,minmax(92px,1fr))" in html
    assert "max-height:92px" in html
    assert "showPageTabContext" in html
    assert "Unified right-click handling" in html
    assert "Печать всего FBD-проекта" in html
    assert "Печать всех страниц проекта" in html


def test_fbd_workbench_exposes_multiple_persisted_projects_in_station_tree():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "const docs=station.fbd_projects||[]" in html
    assert "data-fbd-document" in html
    assert "data-create-fbd-project" in html
    assert "data-document=\"${escTree(doc.id)}\"" in html
