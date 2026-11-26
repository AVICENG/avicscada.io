import time

import pytest

from avic_core.field_runtime import FieldRuntimeProcess, FieldRuntimeProcessError


def test_field_runtime_is_a_separate_process_and_reports_capability_boundary():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        ready = runtime.start()
        assert ready["pid"] != __import__("os").getpid()
        status = runtime.status()
        assert status["state"] == "RUNNING"
        assert status["execution_engine_attached"] is False
        assert status["capability_state"] == "PROCESS_HOST_ONLY"
        assert status["active_strategies"] == 0
        assert runtime.ping()["ok"] is True
    finally:
        process = runtime._test_only_process_handle()
        if process is not None and process.is_alive():
            process.terminate()
            process.join(timeout=2.0)


def test_supervisor_ipc_disconnect_does_not_stop_field_process():
    runtime = FieldRuntimeProcess(heartbeat_interval=0.05)
    try:
        runtime.start()
        process = runtime._test_only_process_handle()
        runtime.disconnect_supervisor()
        time.sleep(0.15)
        assert process is not None and process.is_alive()
    finally:
        process = runtime._test_only_process_handle()
        if process is not None and process.is_alive():
            process.terminate()
            process.join(timeout=2.0)


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
    finally:
        process = runtime._test_only_process_handle()
        if process is not None and process.is_alive():
            process.terminate()
            process.join(timeout=2.0)

