import socket

import pytest

from avic_core.network import BacnetIpClient, BacnetIpNetworkConfig, BacnetProtocolError, parse_iam
from avic_core.network.bacnet_ip import diagnose_bacnet_packet


def _iam_packet(device=1234, vendor=42):
    # BVLC + NPDU + unconfirmed I-Am + application tags.
    object_id = ((8 << 22) | device).to_bytes(4, "big")
    payload = (
        b"\x10\x00"                 # UnconfirmedRequest / I-Am
        + b"\xC4" + object_id       # application ObjectIdentifier
        + b"\x22\x05\xC4"         # application Unsigned max APDU
        + b"\x91\x03"               # application Enumerated segmentation
        + b"\x21" + bytes([vendor]) # application Unsigned vendor id
    )
    npdu = b"\x01\x00" + payload
    return b"\x81\x0A" + (len(npdu) + 4).to_bytes(2, "big") + npdu


def _config():
    return BacnetIpNetworkConfig(
        network_id="plant-lan", interface_name="loopback",
        local_address="127.0.0.1", subnet_cidr="127.0.0.0/8",
        udp_port=47808,
    )


def test_parse_iam_extracts_device_instance_and_vendor():
    iam = parse_iam(_iam_packet(), ("127.0.0.2", 47808))
    assert iam is not None
    assert iam.device_instance == 1234
    assert iam.vendor_id == 42
    assert iam.max_apdu == 1476
    assert iam.segmentation == 3


def test_parse_iam_ignores_non_bacnet_packet():
    assert parse_iam(b"not bacnet", ("127.0.0.2", 47808)) is None


def test_discovery_client_is_read_only_and_sends_who_is(monkeypatch):
    class FakeSocket:
        def __init__(self, *args):
            self.sent = None
            self.timeout = None
            self.received = False
            self.closed = False
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): self.sent = (data, target)
        def settimeout(self, value): self.timeout = value
        def recvfrom(self, size):
            if not self.received:
                self.received = True
                return _iam_packet(), ("127.0.0.2", 47808)
            raise socket.timeout()
        def close(self): self.closed = True

    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())
    devices = client.discover(timeout_seconds=0.01)
    assert len(devices) == 1
    assert devices[0].device_instance == 1234
    assert devices[0].vendor_id == 42
    assert fake.sent[0][0:2] == b"\x81\x0b"
    assert fake.sent[1] == ("127.255.255.255", 47808)
    assert client.last_discovery_diagnostics["request_bytes"] > 0
    assert client.last_discovery_diagnostics["received_udp_packets"] == 1
    assert client.last_discovery_diagnostics["valid_iam_packets"] == 1
    assert client.last_discovery_diagnostics["packet_details"][0]["source_ip"] == "127.0.0.2"
    assert client.last_discovery_diagnostics["packet_details"][0]["hex"].startswith("81 0A")
    assert client.last_discovery_diagnostics["devices_found"] == 1
    client.close()
    assert fake.closed



def test_discovery_classifies_looped_back_who_is_as_self_request(monkeypatch):
    class FakeSocket:
        def __init__(self, *args): self.sent = None; self.index = 0
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): self.sent = (data, target); return len(data)
        def settimeout(self, value): pass
        def recvfrom(self, size):
            self.index += 1
            if self.index == 1:
                return self.sent[0], ("127.0.0.1", 47808)
            if self.index == 2:
                return _iam_packet(device=1001, vendor=91), ("127.0.0.2", 47808)
            raise socket.timeout()
        def close(self): pass

    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())
    devices = client.discover(timeout_seconds=0.01)
    diagnostics = client.last_discovery_diagnostics
    assert [d.device_instance for d in devices] == [1001]
    assert diagnostics["received_udp_packets"] == 2
    assert diagnostics["self_packets"] == 1
    assert diagnostics["valid_iam_packets"] == 1
    assert diagnostics["ignored_packets"] == 0
    assert [p["classification"] for p in diagnostics["packet_details"]] == ["SELF_REQUEST", "I-AM"]
    assert "собственный who-is" in diagnostics["packet_details"][0]["reason"].lower()
    client.close()

def test_discovery_client_rejects_write_policy():
    from avic_core.network import DiscoveryPolicy
    with pytest.raises(ValueError, match="read-only"):
        BacnetIpClient(_config(), DiscoveryPolicy(allow_writes=True))


def test_read_property_builds_confirmed_request_and_decodes_unsigned(monkeypatch):
    class FakeSocket:
        def __init__(self, *args): self.sent = None
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): self.sent = (data, target)
        def settimeout(self, value): pass
        def recvfrom(self, size):
            apdu = b"\x30\x01\x0c\x3e\x21\x2a\x3f"
            npdu = b"\x01\x00" + apdu
            packet = b"\x81\x0a" + (len(npdu)+4).to_bytes(2, "big") + npdu
            return packet, ("127.0.0.2", 47808)
        def close(self): pass

    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())
    value = client.read_property(("127.0.0.2", 47808), 1234, 0, 1, 85)
    assert value == 42
    assert fake.sent[0][6:10] == b"\x00\x05\x01\x0c"


def _read_property_ack(invoke, value_tagged):
    # ReadProperty ComplexACK: context object-id, property-id, value wrapper.
    object_id = ((8 << 22) | 1001).to_bytes(4, "big")
    payload = (bytes([0x30, invoke, 0x0C]) + b"\x0c" + object_id
               + b"\x19\x4c\x3e" + value_tagged + b"\x3f")
    npdu = b"\x01\x00" + payload
    return b"\x81\x0a" + (len(npdu) + 4).to_bytes(2, "big") + npdu


def test_read_object_list_uses_array_index_and_preserves_native_identity(monkeypatch):
    class FakeSocket:
        def __init__(self, *args):
            self.sent = []
            self.responses = [
                _read_property_ack(1, b"\x21\x02"),  # array length = 2
                _read_property_ack(2, b"\xc4" + ((1 << 22) | 1).to_bytes(4, "big")),
                _read_property_ack(3, b"\xc4" + ((3 << 22) | 2).to_bytes(4, "big")),
            ]
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): self.sent.append(data)
        def settimeout(self, value): pass
        def recvfrom(self, size): return self.responses.pop(0), ("127.0.0.2", 47808)
        def close(self): pass

    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())
    objects = client.read_object_list(("127.0.0.2", 47808), 1001)
    assert [(o.object_type, o.instance) for o in objects] == [(1, 1), (3, 2)]
    assert objects[0].type_name == "analog-output"
    assert objects[1].type_name == "binary-input"
    assert objects[0].native_identity == "bacnet:object:1:1"
    # The array index is encoded as context tag 2 in each request.
    assert b"\x29\x00" in fake.sent[0]
    assert b"\x29\x01" in fake.sent[1]
    assert b"\x29\x02" in fake.sent[2]


def test_read_object_list_rejects_excessive_array_count(monkeypatch):
    class FakeSocket:
        def __init__(self, *args): pass
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): pass
        def settimeout(self, value): pass
        def recvfrom(self, size): return _read_property_ack(1, b"\x22\x13\x89"), ("127.0.0.2", 47808)
        def close(self): pass

    monkeypatch.setattr(socket, "socket", lambda *args: FakeSocket())
    client = BacnetIpClient(_config())
    with pytest.raises(BacnetProtocolError, match="Object_List count"):
        client.read_object_list(("127.0.0.2", 47808), 1001, max_objects=100)


def test_parse_iam_supports_forwarded_npdu_and_uses_embedded_origin():
    original = _iam_packet(device=1001, vendor=7)
    forwarded = original[:4] + socket.inet_aton("10.10.10.2") + (47808).to_bytes(2, "big") + original[4:]
    forwarded = b"\x81\x04" + len(forwarded).to_bytes(2, "big") + forwarded[4:]
    iam = parse_iam(forwarded, ("10.10.10.1", 47808))
    assert iam is not None
    assert iam.device_instance == 1001
    assert iam.vendor_id == 7
    assert iam.source == ("10.10.10.2", 47808)


def test_parse_iam_supports_npdu_destination_specifier():
    # Destination specifier: DNET(2), DLEN(1), DADR, hop-count(1).
    base = _iam_packet(device=1001)
    npdu = b"\x01\x20" + b"\x00\x01\x01\x01\xFF" + base[6:]
    packet = b"\x81\x0A" + (len(npdu) + 4).to_bytes(2, "big") + npdu
    iam = parse_iam(packet, ("10.10.10.2", 47808))
    assert iam is not None and iam.device_instance == 1001


def test_diagnose_bacnet_packet_reports_bvlc_and_apdu_layers():
    result = diagnose_bacnet_packet(_iam_packet(device=1001))
    assert result["bvlc_type"] == "0x81"
    assert result["bvlc_function"] == "0x0A"
    assert result["npdu_version"] == 1
    assert result["apdu_type"] == "0x10"
    assert result["apdu_service"] == "0x00"


def test_diagnose_bacnet_packet_explains_non_bacnet_udp():
    result = diagnose_bacnet_packet(b"\x01\x02\x03\x04")
    assert result["reason"] == "BVLC type is not BACnet/IPv4 (0x81)"


def test_parse_real_trend_iq3_global_broadcast_iam_capture():
    # Captured from Trend IQ3 at 10.10.10.2:47808 during AVIC DEV30 discovery.
    packet = bytes.fromhex(
        "81 0B 00 18 01 20 FF FF 00 FF 10 00 "
        "C4 02 00 03 E9 22 05 C4 91 00 21 5B"
    )
    iam = parse_iam(packet, ("10.10.10.2", 47808))
    assert iam is not None
    assert iam.device_instance == 1001
    assert iam.max_apdu == 1476
    assert iam.segmentation == 0
    assert iam.vendor_id == 91
    assert iam.source == ("10.10.10.2", 47808)


def test_diagnose_real_trend_iq3_global_broadcast_iam_capture():
    packet = bytes.fromhex(
        "81 0B 00 18 01 20 FF FF 00 FF 10 00 "
        "C4 02 00 03 E9 22 05 C4 91 00 21 5B"
    )
    result = diagnose_bacnet_packet(packet)
    assert result["npdu_control"] == "0x20"
    assert result["destination_network"] == 0xFFFF
    assert result["destination_address_length"] == 0
    assert result["hop_count"] == 255
    assert result["apdu_type"] == "0x10"
    assert result["apdu_service"] == "0x00"
    assert result["reason"].startswith("I-Am APDU envelope detected")


def test_read_property_ignores_response_from_wrong_udp_port(monkeypatch):
    class FakeSocket:
        def __init__(self, *args): self.calls = 0
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): pass
        def settimeout(self, value): pass
        def recvfrom(self, size):
            self.calls += 1
            packet = _read_property_ack(1, b"\\x21\\x2a")
            return packet, ("127.0.0.2", 47809 if self.calls == 1 else 47808)
        def close(self): pass
    fake = FakeSocket()
    monkeypatch.setattr(socket, "socket", lambda *args: fake)
    client = BacnetIpClient(_config())
    assert client.read_property(("127.0.0.2", 47808), 1001, 0, 1, 85) == 42
    assert fake.calls == 2


def test_read_property_reports_unsupported_segmented_ack_without_timeout(monkeypatch):
    class FakeSocket:
        def __init__(self, *args): pass
        def setsockopt(self, *args): pass
        def bind(self, *args): pass
        def sendto(self, data, target): pass
        def settimeout(self, value): pass
        def recvfrom(self, size):
            npdu = b"\\x01\\x00\\x38\\x01\\x0c"
            packet = b"\\x81\\x0a" + (len(npdu) + 4).to_bytes(2, "big") + npdu
            return packet, ("127.0.0.2", 47808)
        def close(self): pass
    monkeypatch.setattr(socket, "socket", lambda *args: FakeSocket())
    client = BacnetIpClient(_config())
    with pytest.raises(BacnetProtocolError, match="segmented ReadProperty"):
        client.read_property(("127.0.0.2", 47808), 1001, 0, 1, 85)
