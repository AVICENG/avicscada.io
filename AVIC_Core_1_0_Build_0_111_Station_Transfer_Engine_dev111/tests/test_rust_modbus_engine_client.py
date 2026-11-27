import json
import queue
import subprocess
from pathlib import Path

import pytest

from avic_core.drivers.rust_communication_engine import (
    RustCommunicationEngineError,
    RustModbusTcpClient,
)


def test_rust_modbus_client_requires_existing_binary(tmp_path):
    with pytest.raises(FileNotFoundError):
        RustModbusTcpClient("127.0.0.1", engine_binary=tmp_path / "missing-engine")


def test_rust_modbus_client_validates_transport_parameters(tmp_path):
    binary = tmp_path / "engine"
    binary.write_text("placeholder", encoding="utf-8")
    with pytest.raises(ValueError):
        RustModbusTcpClient("not-an-ip", engine_binary=binary)
    with pytest.raises(ValueError):
        RustModbusTcpClient("127.0.0.1", port=0, engine_binary=binary)


def test_rust_engine_response_rejects_wrong_value_shape(tmp_path, monkeypatch):
    binary = tmp_path / "engine"
    binary.write_text("placeholder", encoding="utf-8")
    client = RustModbusTcpClient("127.0.0.1", engine_binary=binary)
    class FakeProcess:
        def __init__(self):
            self.stdin = type("Input", (), {"write": lambda self, value: None, "flush": lambda self: None})()
            self.stdout = None
            self.returncode = None
        def poll(self): return None
        def kill(self): self.returncode = -9
        def wait(self, timeout=None): return self.returncode
    fake = FakeProcess()
    monkeypatch.setattr(subprocess, "Popen", lambda *args, **kwargs: fake)
    client._process = fake
    client._healthy = True
    client._responses.put({"request_id": 1, "ok": True, "values": [65536]})
    client._request_id = 0
    with pytest.raises(RustCommunicationEngineError, match="invalid Modbus values"):
        client.read_holding_registers(0, 1)
