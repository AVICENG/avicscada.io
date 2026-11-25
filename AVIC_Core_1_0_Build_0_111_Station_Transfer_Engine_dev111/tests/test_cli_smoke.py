from __future__ import annotations

import json
import os
import subprocess
import sys


def _run(*args: str, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "avic_core", *args],
        check=False, capture_output=True, text=True, env=env, timeout=30,
    )


def test_cli_init_and_health_smoke(tmp_path):
    project_root = str(__file__)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(__import__("pathlib").Path(project_root).parents[1])
    data_dir = tmp_path / "avic-data"

    initialized = _run("--data-dir", str(data_dir), "init", env=env)
    assert initialized.returncode == 0, initialized.stderr
    assert json.loads(initialized.stdout)["status"] == "initialized"

    health = _run("--data-dir", str(data_dir), "health", env=env)
    assert health.returncode == 0, health.stderr
    report = json.loads(health.stdout)
    assert report["status"] == "OK"
    assert {item["name"] for item in report["checks"]} == {
        "data_directory", "audit_chain", "runtime"
    }
