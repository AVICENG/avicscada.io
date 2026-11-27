import struct
import pytest
from avic_core.network.modbus_tcp import ModbusTcpClient, ModbusProtocolError


class FakeSocket:
    def __init__(self, response): self.response = response; self.sent = None
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def settimeout(self, value): pass
    def sendall(self, data): self.sent = data
    def recv(self, size):
        if len(self.response) < size: raise AssertionError("short fake response")
        part, self.response = self.response[:size], self.response[size:]
        return part


def test_modbus_mei_device_identification_reads_vendor_product_revision(monkeypatch):
    body = bytes([0x2B, 0x0E, 0x01, 0x01, 0x00, 0x00, 0x03,
                  0x00, 0x06]) + b"AcmeCo" + bytes([0x01, 0x04]) + b"X100" + bytes([0x02, 0x03]) + b"1.2"
    response = struct.pack(">HHHB", 1, 0, len(body) + 1, 1) + body
    fake = FakeSocket(response)
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: fake)
    client = ModbusTcpClient("127.0.0.1", unit_id=1)
    result = client.read_device_identification()
    assert result == {"0": "AcmeCo", "1": "X100", "2": "1.2"}
    assert fake.sent[-4:] == bytes([0x2B, 0x0E, 0x01, 0x00])


def test_modbus_mei_rejects_invalid_read_code():
    client = ModbusTcpClient("127.0.0.1")
    with pytest.raises(ValueError):
        client.read_device_identification(read_code=0)



def _mei_response(body, *, tid=1, unit=1):
    return struct.pack(">HHHB", tid, 0, len(body) + 1, unit) + body


@pytest.mark.parametrize(
    "body",
    [
        bytes([0x2B, 0x0E, 0x02, 0x01, 0x00, 0x00, 0x00]),  # wrong read code
        bytes([0x2B, 0x0E, 0x01, 0x01, 0x01, 0x00, 0x00]),  # invalid more-follows
        bytes([0x2B, 0x0E, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00, 0x02, 0x41]),  # truncated value
        bytes([0x2B, 0x0E, 0x01, 0x01, 0x00, 0x00, 0x00, 0xFF]),  # trailing bytes
        bytes([0xAB]),  # malformed exception
    ],
)
def test_modbus_mei_rejects_malformed_or_mismatched_responses(monkeypatch, body):
    fake = FakeSocket(_mei_response(body))
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: fake)
    client = ModbusTcpClient("127.0.0.1", unit_id=1)
    with pytest.raises(ModbusProtocolError):
        client.read_device_identification()


def test_modbus_mei_uses_shared_atomic_transaction_id_allocator(monkeypatch):
    body = bytes([0x2B, 0x0E, 0x01, 0x01, 0x00, 0x00, 0x00])
    fake = FakeSocket(_mei_response(body, tid=0x1235))
    monkeypatch.setattr("socket.create_connection", lambda *a, **k: fake)
    client = ModbusTcpClient("127.0.0.1", unit_id=1)
    client._transaction_id = 0x1234
    assert client.read_device_identification() == {}
    assert struct.unpack(">H", fake.sent[:2])[0] == 0x1235
