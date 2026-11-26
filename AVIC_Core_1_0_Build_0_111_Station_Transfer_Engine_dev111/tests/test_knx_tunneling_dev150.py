import socket

import pytest

from avic_core.network.knxnet_ip import decode_frame, encode_frame
from avic_core.network.knx_tunneling import (
    KnxTunnelingError, KnxTunnelingSession, TUNNELING_REQ,
)


class FakeKnxSocket:
    def __init__(self, gateway=("192.0.2.20", 3671), data_port=3672, advertised_host="192.0.2.20"):
        self.gateway = gateway
        self.data_port = data_port
        self.advertised_host = advertised_host
        self.bound = None
        self.timeout = 1.0
        self.queue = []
        self.sent = []
        self.closed = False

    def bind(self, address):
        self.bound = address

    def getsockname(self):
        return (self.bound[0], self.bound[1] or 41000)

    def settimeout(self, value):
        self.timeout = value

    def sendto(self, packet, endpoint):
        self.sent.append((packet, endpoint))
        frame = decode_frame(packet)
        if frame.service_type == 0x0205:
            payload = bytes((7, 0, 8, 1)) + bytes(map(int, self.advertised_host.split("."))) + self.data_port.to_bytes(2, "big") + bytes((4, 4, 0x11, 1))
            self.queue.append((encode_frame(0x0206, payload), self.gateway))
        elif frame.service_type == TUNNELING_REQ:
            channel, sequence = frame.payload[1], frame.payload[2]
            self.queue.append((encode_frame(0x0421, bytes((4, channel, sequence, 0))), (self.gateway[0], self.data_port)))
        elif frame.service_type == 0x0207:
            self.queue.append((encode_frame(0x0208, bytes((frame.payload[0], 0))), self.gateway))
        elif frame.service_type == 0x0209:
            self.queue.append((encode_frame(0x020A, bytes((frame.payload[0], 0))), self.gateway))

    def recvfrom(self, _size):
        if not self.queue:
            raise socket.timeout("empty")
        return self.queue.pop(0)

    def close(self):
        self.closed = True


def make_session(fake):
    return KnxTunnelingSession(
        "192.0.2.20", local_host="192.0.2.10",
        socket_factory=lambda *_: fake, timeout_seconds=0.1, retries=1,
    )


def test_knx_tunneling_connect_send_and_disconnect():
    fake = FakeKnxSocket()
    session = make_session(fake)
    connected = session.connect()
    assert connected["state"] == "CONNECTED"
    assert connected["channel_id"] == 7
    assert connected["data_endpoint"] == ("192.0.2.20", 3672)
    assert connected["individual_address"] == 0x1101
    assert session.send_cemi(b"\x29\x00\x00\x00") == 0
    assert session.tx_sequence == 1
    session.disconnect()
    assert session.state == "DISCONNECTED"
    assert fake.closed


def test_knx_rejects_connect_response_redirect_to_other_host():
    fake = FakeKnxSocket(advertised_host="198.51.100.99")
    session = make_session(fake)
    with pytest.raises(KnxTunnelingError, match="untrusted data endpoint"):
        session.connect()
    assert session.state == "ERROR"
    assert fake.closed


def test_knx_receive_cemi_acknowledges_and_deduplicates():
    fake = FakeKnxSocket()
    session = make_session(fake)
    session.connect()
    incoming = encode_frame(TUNNELING_REQ, bytes((4, 7, 0, 0)) + b"\x29\x00\x00\x00")
    fake.queue.append((incoming, ("192.0.2.20", 3672)))
    assert session.receive_cemi() == b"\x29\x00\x00\x00"
    assert decode_frame(fake.sent[-1][0]).service_type == 0x0421
    fake.queue.append((incoming, ("192.0.2.20", 3672)))
    assert session.receive_cemi() is None
    assert decode_frame(fake.sent[-1][0]).service_type == 0x0421
    session.close()


def test_knx_rejects_unroutable_local_bind_address():
    with pytest.raises(ValueError):
        KnxTunnelingSession("192.0.2.20", local_host="0.0.0.0")


def test_knx_send_requires_connection():
    session = make_session(FakeKnxSocket())
    with pytest.raises(KnxTunnelingError):
        session.send_cemi(b"\x29")
