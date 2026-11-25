from pathlib import Path

HTML = Path(__file__).parents[1] / "avic_core" / "ui" / "static" / "logic.html"


def test_fbd_drag_starts_from_entire_block_except_ports():
    source = HTML.read_text(encoding="utf-8")
    assert "el.onpointerdown=e=>{if(e.button!==0||e.target.closest('[data-port]'))return;startDrag(e,id)}" in source
    assert "el.querySelector('.bhead').onpointerdown=e=>startDrag(e,id)" not in source


def test_wires_use_shared_orthogonal_router_for_preview_and_saved_links():
    source = HTML.read_text(encoding="utf-8")
    assert "function routeWirePoints(a,b,fromToken,toToken)" in source
    assert 'points=\"${pts}\"' in source
    assert 'class="wire-hit"' in source and 'class="wire ${state.selected===l.id?' in source
    assert " H${mid} L${b.x},${b.y}" not in source


def test_simulation_values_are_hidden_when_stopped_and_cleared_on_stop():
    source = HTML.read_text(encoding="utf-8")
    assert "let liveBound=Boolean(m.params?.pointRef?.id||m.params?.externalPointBinding?.pointId)" in source
    assert "let showValues=state.running||liveBound" in source
    assert "let fmt=v=>!showValues?'':" in source
    assert "${showValues?`<div class=\"block-value\">" in source
    stop = source[source.index("function stop()") : source.index("function check()", source.index("function stop()"))]
    for token in ("m.inputValues={}", "m.outputValues={}", "m.runtimeState={}", "m.pidDiagnostics=null"):
        assert token in stop


def test_tracker_hides_values_when_simulation_is_stopped():
    source = HTML.read_text(encoding="utf-8")
    assert "state.running?(typeof m.value==='boolean'?digital(m.value):(m.value??'—')):'—'" in source
    assert "state.simulationInitialValues=Object.fromEntries" in source
    assert "state.simulationInitialValues=null" in source


def test_wire_values_are_only_rendered_during_simulation():
    source = HTML.read_text(encoding="utf-8")
    assert "${state.running?`<text class=\"wire-value\"" in source


def test_port_labels_are_anchored_next_to_connectors():
    source = HTML.read_text(encoding="utf-8")
    assert ".portrow:has(.port.in){display:grid;grid-template-columns:10px minmax(0,1fr) 24px" in source
    assert ".portrow:has(.port.out){display:grid;grid-template-columns:24px minmax(0,1fr) 10px" in source
