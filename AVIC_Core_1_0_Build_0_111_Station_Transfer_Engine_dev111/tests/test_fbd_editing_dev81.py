from pathlib import Path


def test_wires_are_thin_orthogonal_and_selectable():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "stroke-width:1.5;vector-effect:non-scaling-stroke" in html
    assert "class=\"wire-hit\"" in html and "stroke=\"transparent\"" in html
    assert "function routeWirePoints(a,b,fromToken,toToken)" in html
    assert "Q${mid}" not in html
    assert "data-link" in html and "state.selected=el.dataset.link" in html
    assert "e.key==='Delete'||e.key==='Backspace'" in html


def test_block_drag_and_text_notes_are_persisted_on_page():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "el.onpointerdown=e=>{if(e.button!==0||e.target.closest('[data-port]'))return;startDrag(e,id)}" in html
    assert "function renderCanvasNotes(pg)" in html
    assert "pg.notes.push({id:uid(),x,y,text:txt})" in html
    assert "data-canvas-note" in html


def test_fbd_point_creation_offers_source_navigation():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "Источник: ${c.pageName} → ${c.moduleName} → ${c.portName}" in html
    assert "jumpToModule(c.pageId,c.moduleId)" in html


def test_page_names_are_unique_within_project():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "Page с таким названием уже существует в проекте" in html
    assert "while(state.pages.some(x=>x.name.trim().toLocaleLowerCase()===name.toLocaleLowerCase()))" in html
