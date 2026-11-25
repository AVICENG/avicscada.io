from pathlib import Path

HTML = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"


def test_saved_wires_use_obstacle_aware_orthogonal_router():
    source = HTML.read_text(encoding="utf-8")
    assert "function blockObstacles(excludeIds=[])" in source
    assert "function wireSegmentHitsRect(a,b,r)" in source
    assert "function wireRouteIsClear(points,obstacles)" in source
    assert "function routeWirePoints(a,b,fromToken,toToken)" in source
    assert "const pts=routeWirePoints(a,b,l.from,l.to);" in source
    assert "wireSegmentHitsRect(points[i-1],points[i],r)" in source


def test_wire_selection_highlights_complete_connection():
    source = HTML.read_text(encoding="utf-8")
    assert ".wire.selected{stroke:#e07816;stroke-width:3.25" in source
    assert 'data-link="${esc(l.id)}"' in source
    assert "state.selected=el.dataset.link;renderProperties();renderWires()" in source


def test_ports_expose_exact_module_and_contact_identity():
    source = HTML.read_text(encoding="utf-8")
    assert "· IN ${i+1} · ${esc(a.name)}" in source
    assert "· OUT ${i+1} · ${esc(a.name)}" in source


def test_block_labels_have_wrapping_and_separate_rows():
    source = HTML.read_text(encoding="utf-8")
    assert "overflow-wrap:anywhere" in source
    assert ".portrow{min-height:18px;height:auto" in source
    assert ".btag{font-size:8px;line-height:11px" in source
