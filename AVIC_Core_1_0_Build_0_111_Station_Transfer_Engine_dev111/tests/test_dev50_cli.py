from __future__ import annotations

import sys
from types import SimpleNamespace

from avic_core.ui import __main__ as ui_main
from avic_core.ui import app as ui_app


def test_workbench_cli_passes_host_port_and_data_directory(monkeypatch, tmp_path):
    calls = {}
    real_create_ui_app = ui_app.create_ui_app

    def tracking_create_ui_app(*, data_dir=None):
        calls["data_dir"] = data_dir
        return real_create_ui_app(data_dir=data_dir)

    monkeypatch.setattr(ui_app, "create_ui_app", tracking_create_ui_app)

    def fake_config(app, **kwargs):
        calls["app"] = app
        calls["config"] = SimpleNamespace(**kwargs)
        return calls["config"]

    class FakeServer:
        def __init__(self, config):
            calls["server_config"] = config
            self.should_exit = False

        def run(self):
            calls["server_run"] = True

    fake_uvicorn = SimpleNamespace(
        Config=fake_config,
        Server=FakeServer,
    )

    monkeypatch.setitem(sys.modules, "uvicorn", fake_uvicorn)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "avic-core-ui",
            "--host",
            "127.0.0.1",
            "--port",
            "8123",
            "--data-dir",
            str(tmp_path),
        ],
    )

    ui_main.main()

    assert calls["data_dir"] == str(tmp_path)
    assert calls["config"].host == "127.0.0.1"
    assert calls["config"].port == 8123
    assert calls["app"].title == "AVIC Engineering Workbench"
    assert calls["app"].state.core is not None
    assert calls["server_run"] is True


def test_workbench_cli_help_does_not_start_server(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["avic-core-ui", "--help"])
    try:
        ui_main.main()
    except SystemExit as exc:
        assert exc.code == 0
    else:
        raise AssertionError("argparse --help must exit")
    assert "--data-dir" in capsys.readouterr().out
