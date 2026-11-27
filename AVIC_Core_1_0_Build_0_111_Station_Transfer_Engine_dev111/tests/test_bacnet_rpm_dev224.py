import socket

import pytest

from avic_core.network import BacnetIpClient, BacnetIpNetworkConfig, BacnetProtocolError


def _config():
    return BacnetIpNetworkConfig(
        network_id="plant-lan", interface_name="loopback",
        local_address="127.0.0.1", subnet_cidr="127.0.0.0/8",
        udp_port=47808,
    )


def _ctx(number, raw):
    return bytes([(number << 4) | 0x08 | len(raw)]) + raw


def _rpm_ack(invoke, object_type=0, instance=1, *, wrong_object=False):
    actual_instance = instance + 1 if wrong_object else instance
    object_id = ((object_type << 22) | actual_instance).to_bytes(4, "big")
    # Property 85 = Present_Value, Real 22.5; property 111 = Status_Flags,
    # returned as a per-property BACnet Error (error-class 2, error-code 37).
    data = (
        _ctx(0, object_id) + b"\x1e"
        + _ctx(2, b"\x55") + b"\x4e" + b"\x44\x41\xb4\x00\x00" + b"\x4f"
        + _ctx(2, b"\x6f") + b"\x5e" + b"\x91\x02\x91\x25" + b"\x5f"
        + b"\x1f"
    )
    apdu = bytes((0x30, invoke, 0x0E)) + data
    npdu = b"\x01\x00" + apdu
    return b"\x81\x0a" + (len(npdu) + 4).to_bytes(2, "big") + npdu


class FakeSocket:
    def __init__(self, response):
        self.response = response
        self.sent = []
        self.closed = False

    def setsockopt(self, *args):
        pass

    def bind(self, *args):
        pass

    def sendto(self, data, address):
        self.sent.append((data, address))
        return len(data)

    def settimeout(self, value):
        pass

    def recvfrom(self, size):
        return self.response, ("127.0.0.2", 47808)

    def close(self):
        self.closed = True


def test_read_property_multiple_reads_many_properties_in_one_request(monkeypatch):
    fake = FakeSocket(_rpm_ack(1))
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())

    result = client.read_property_multiple(
        ("127.0.0.2", 47808), 1001, 0, 1, [85, 111]
    )

    assert result[85] == pytest.approx(22.5)
    assert result[111] == {"error": [2, 37]}
    assert len(fake.sent) == 1
    packet = fake.sent[0][0]
    assert packet[0:2] == b"\x81\x0a"
    assert packet[6:10] == b"\x00\x05\x01\x0e"
    assert b"\x09\x55" in packet
    assert b"\x09\x6f" in packet


def test_read_property_multiple_rejects_mismatched_object_identity(monkeypatch):
    fake = FakeSocket(_rpm_ack(1, wrong_object=True))
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())

    with pytest.raises(BacnetProtocolError, match="object identifier does not match"):
        client.read_property_multiple(
            ("127.0.0.2", 47808), 1001, 0, 1, [85, 111]
        )


def test_read_property_multiple_rejects_duplicate_or_unbounded_requests():
    client = BacnetIpClient(_config())
    with pytest.raises(ValueError, match="duplicate"):
        client.read_property_multiple(("127.0.0.2", 47808), 1001, 0, 1, [85, 85])
    with pytest.raises(ValueError, match="64"):
        client.read_property_multiple(
            ("127.0.0.2", 47808), 1001, 0, 1, list(range(65))
        )
