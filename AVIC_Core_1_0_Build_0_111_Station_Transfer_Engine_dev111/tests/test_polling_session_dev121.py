import threading
import time

import pytest

from avic_core.drivers.polling import PollingSession


class FakeAdapter:
    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()
    def poll_once(self):
        with self.lock:
            self.calls += 1
        return {"results": [{"ok": True}, {"ok": False}]}


def test_polling_session_starts_runs_without_overlap_and_stops():
    adapter = FakeAdapter()
    session = PollingSession(adapter, 0.1)
    session.start()
    deadline = time.monotonic() + 2
    while adapter.calls < 2 and time.monotonic() < deadline:
        time.sleep(0.01)
    session.stop()
    diagnostics = session.diagnostics()
    assert adapter.calls >= 2
    assert diagnostics["state"] == "STOPPED"
    assert diagnostics["worker_alive"] is False
    assert diagnostics["failure_count"] >= 2
    assert diagnostics["success_count"] >= 2


def test_polling_session_is_idempotent_and_restarts():
    adapter = FakeAdapter()
    session = PollingSession(adapter, 0.1)
    session.start()
    session.start()
    time.sleep(0.15)
    session.stop()
    first = adapter.calls
    session.start()
    time.sleep(0.15)
    session.stop()
    assert adapter.calls > first


def test_polling_session_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        PollingSession(FakeAdapter(), 0.01)
    with pytest.raises(TypeError):
        PollingSession(object(), 1.0)
