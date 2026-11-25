from __future__ import annotations

import sys
from types import SimpleNamespace

from avic_core.ui import __main__ as ui_main


def test_workbench_cli_passes_host_port_and_data_directory(monkeypatch, tmp_path):
    calls = {}
    fake_uvicorn = SimpleNamespace(run=lambda app, **kwargs: calls.update(app=app, **kwargs))
    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.setattr(sys, "argv", ["avic-core-ui", "--host", "127.0.0.1", "--port", "8123", "--data-dir", str(tmp_path)])
    ui_main.main()
    assert calls["host"] == "127.0.0.1"
    assert calls["port"] == 8123
    assert calls["app"].title == "AVIC Engineering Workbench"
    assert calls["app"].state.core is not None


def test_workbench_cli_help_does_not_start_server(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["avic-core-ui", "--help"])
    try:
        ui_main.main()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --help must exit")
    assert "--data-dir" in capsys.readouterr().out
