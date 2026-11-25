from pathlib import Path
import re


def _pid_script():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    scripts = re.findall(r"<script>(.*?)</script>", html, re.S)
    return scripts[1]


def test_pid_direct_and_reverse_action_are_unambiguous():
    script = _pid_script()
    assert "DIRECT means OUT rises as PV rises" in script
    assert "c.action==='direct'?-1:1" in script
    assert "derivativeRaw=s.initialized?-(pv-s.previousPV)/dt:0" in script


def test_pid_has_filtered_derivative_anti_windup_and_bumpless_manual_transfer():
    script = _pid_script()
    assert "const alpha=tau<=0?1:dt/(tau+dt)" in script
    assert "Conditional integration anti-windup" in script
    assert "s.lastOutput??bias" in script
    assert "s.integral=clamp(manualOut-bias-p-d" in script


def test_pid_dialog_is_responsive_and_does_not_clip_header_or_footer():
    html = (Path(__file__).parents[1] / "avic_core/ui/static/logic.html").read_text(encoding="utf-8")
    assert "max-height:90dvh" in html
    assert "#modalBody{overflow:auto;min-height:0;flex:1" in html
    assert ".pid-modal .modal{width:min(900px,94vw)" in html
    assert "Direct — OUT increases when PV increases" in html
