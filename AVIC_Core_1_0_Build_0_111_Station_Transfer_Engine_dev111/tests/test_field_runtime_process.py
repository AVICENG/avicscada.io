import json
import os
import subprocess
import sys
import time

import psutil
import pytest

from avic_core.field_runtime import FieldRuntimeProcess, FieldRuntimeProcessError


def _cleanup(runtime):
    process = runtime._test_only_process_handle()
    if process is not None and process.poll() is None:
        process.terminate()
        try: process.wait(timeout=2.0)
        except Exception: pass
    runtime._close_sockets()


def test_field_runtime_is_a_separate_os_process_and_reports_unattached_engine():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        ready = runtime.start()
        assert ready["pid"] != os.getpid()
        assert runtime.status()["state"] == "RUNNING"
        assert runtime.status()["execution_engine_attached"] is False
        assert runtime.status()["capability_state"] == "PROCESS_HOST_ONLY"
        assert runtime.ping()["ok"] is True
    finally:
        _cleanup(runtime)


def test_supervisor_ipc_disconnect_does_not_stop_agent_and_reconnects():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        runtime.start()
        process = runtime._test_only_process_handle()
        runtime.disconnect_supervisor()
        time.sleep(0.15)
        assert process is not None and process.poll() is None
        # The agent retries the listener; a later status request reconnects it.
        assert runtime.status()["state"] == "RUNNING"
    finally:
        _cleanup(runtime)


def test_field_runtime_maintenance_stop_requires_confirmation_and_token():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        runtime.start()
        with pytest.raises(FieldRuntimeProcessError, match="точное подтверждение"):
            runtime.stop_for_maintenance(confirmation="STOP", maintenance_token="invalid")
        with pytest.raises(FieldRuntimeProcessError, match="authorization rejected"):
            runtime.stop_for_maintenance(confirmation="STOP FIELD RUNTIME", maintenance_token="invalid")
        stopped = runtime.stop_for_maintenance(
            confirmation="STOP FIELD RUNTIME", maintenance_token=runtime._maintenance_token
        )
        assert stopped["state"] == "STOPPED"
        process = runtime._test_only_process_handle()
        assert process is not None and process.poll() == 0
    finally:
        _cleanup(runtime)


def test_field_runtime_heartbeat_advances_without_supervisor_commands():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        runtime.start()
        before = runtime.status()["last_heartbeat_monotonic"]
        time.sleep(0.15)
        after = runtime.status()["last_heartbeat_monotonic"]
        assert after > before
    finally:
        _cleanup(runtime)


def test_field_runtime_agent_survives_supervisor_process_exit():
    # Run the Supervisor in a short-lived parent process. Its detached agent
    # must remain alive after the parent exits and closes its IPC listener.
    script = """
import json
from avic_core.field_runtime import FieldRuntimeProcess

runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
ready = runtime.start()
print(json.dumps({"pid": runtime.pid, "state": ready["state"]}), flush=True)
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=os.getcwd(),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    agent_pid = int(payload["pid"])
    assert payload["state"] == "RUNNING"

    try:
        agent = psutil.Process(agent_pid)
        assert agent.is_running()
        time.sleep(0.2)
        assert agent.is_running()
        # This proves only OS-process survival, not FBD execution or control continuity.
    finally:
        try:
            agent = psutil.Process(agent_pid)
            agent.terminate()
            agent.wait(timeout=3)
        except psutil.NoSuchProcess:
            pass
        except psutil.TimeoutExpired:
            agent.kill()
