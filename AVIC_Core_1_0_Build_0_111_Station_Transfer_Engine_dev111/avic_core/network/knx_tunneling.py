"""Managed KNXnet/IP UDP tunnelling transport.

This module owns transport lifecycle only. It deliberately does not interpret
cEMI/APDU payloads or publish points; those belong to the KNX adapter layer.
"""
from __future__ import annotations

import ipaddress
import socket
import time
from typing import Callable

from avic_core.network.knxnet_ip import (
    KnxProtocolError,
    build_connect_request,
    build_tunneling_ack,
    decode_frame,
    encode_frame,
    encode_hpai,
    parse_connect_response,
    parse_tunneling_ack,
)

CONNECT_STATE_REQ = 0x0207
CONNECT_STATE_RES = 0x0208
DISCONNECT_REQ = 0x0209
DISCONNECT_RES = 0x020A
TUNNELING_REQ = 0x0420


class KnxTunnelingError(ConnectionError):
    """KNX tunnelling transport failed or violated its session contract."""


class KnxTunnelingSession:
    """Synchronous, explicit-lifecycle KNXnet/IP tunnelling client.

    The configured gateway address remains the trusted peer. CONNECT_RES HPAI
    must advertise that same IPv4 address; the client never follows an
    arbitrary endpoint supplied by an unauthenticated UDP response.
    """

    def __init__(
        self,
        gateway_host: str,
        *,
        gateway_port: int = 3671,
        local_host: str,
        local_port: int = 0,
        timeout_seconds: float = 1.0,
        retries: int = 2,
        heartbeat_interval_seconds: float = 60.0,
        socket_factory: Callable[..., object] | None = None,
    ) -> None:
        try:
            self.gateway_host = str(ipaddress.IPv4Address(gateway_host))
            self.local_host = str(ipaddress.IPv4Address(local_host))
        except ipaddress.AddressValueError as exc:
            raise ValueError("KNX tunnelling requires explicit IPv4 addresses") from exc
        if self.local_host == "0.0.0.0" or self.local_host.startswith("127."):
            raise ValueError("local_host must be a routable interface IPv4 address")
        if not 1 <= int(gateway_port) <= 65535 or not 0 <= int(local_port) <= 65535:
            raise ValueError("UDP port out of range")
        if not 0.05 <= float(timeout_seconds) <= 30:
            raise ValueError("timeout_seconds must be between 0.05 and 30")
        if not 0 <= int(retries) <= 10:
            raise ValueError("retries must be between 0 and 10")
        if not 5 <= float(heartbeat_interval_seconds) <= 3600:
            raise ValueError("heartbeat interval must be between 5 and 3600 seconds")

        self.gateway_port = int(gateway_port)
        self.local_port = int(local_port)
        self.timeout_seconds = float(timeout_seconds)
        self.retries = int(retries)
        self.heartbeat_interval_seconds = float(heartbeat_interval_seconds)
        self._socket_factory = socket_factory or socket.socket
        self._socket = None
        self.channel_id: int | None = None
        self.data_endpoint: tuple[str, int] | None = None
        self.individual_address: int | None = None
        self.tx_sequence = 0
        self.rx_sequence: int | None = None
        self.state = "DISCONNECTED"
        self.last_activity = 0.0
        self.last_heartbeat = 0.0

    @property
    def connected(self) -> bool:
        return self.state == "CONNECTED" and self._socket is not None

    def _require_connected(self) -> None:
        if not self.connected or self.channel_id is None or self.data_endpoint is None:
            raise KnxTunnelingError("KNX tunnelling session is not connected")

    def _receive_frame(self, expected_endpoint: tuple[str, int], expected_service: int):
        assert self._socket is not None
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise socket.timeout("KNXnet/IP response timeout")
            self._socket.settimeout(remaining)
            packet, sender = self._socket.recvfrom(65535)
            if (str(sender[0]), int(sender[1])) != expected_endpoint:
                continue
            frame = decode_frame(packet)
            if frame.service_type == expected_service:
                self.last_activity = time.monotonic()
                return frame

    def connect(self) -> dict:
        if self.connected:
            return self.diagnostics()
        if self._socket is not None:
            self._close_socket()
        self.state = "CONNECTING"
        sock = self._socket_factory(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket = sock
        try:
            sock.bind((self.local_host, self.local_port))
            bound_host, bound_port = sock.getsockname()[:2]
            if str(bound_host) not in {self.local_host, "0.0.0.0"}:
                raise KnxTunnelingError("UDP socket bound to an unexpected local address")
            request = build_connect_request(self.local_host, int(bound_port))
            response = None
            for attempt in range(self.retries + 1):
                sock.sendto(request, (self.gateway_host, self.gateway_port))
                try:
                    frame = self._receive_frame((self.gateway_host, self.gateway_port), 0x0206)
                    response = parse_connect_response(encode_frame(frame.service_type, frame.payload))
                    break
                except socket.timeout:
                    if attempt >= self.retries:
                        raise KnxTunnelingError("KNX CONNECT_RES timeout")
            if response is None:
                raise KnxTunnelingError("KNX CONNECT_RES missing")
            if response.status != 0:
                raise KnxTunnelingError(f"KNX gateway rejected CONNECT: status 0x{response.status:02X}")
            if response.data_host != self.gateway_host or not response.data_port:
                raise KnxTunnelingError("KNX CONNECT_RES advertised an untrusted data endpoint")
            self.channel_id = response.channel_id
            self.data_endpoint = (self.gateway_host, response.data_port)
            self.individual_address = response.individual_address
            self.tx_sequence = 0
            self.rx_sequence = None
            self.state = "CONNECTED"
            self.last_activity = time.monotonic()
            self.last_heartbeat = self.last_activity
            return self.diagnostics()
        except Exception:
            self.state = "ERROR"
            self._close_socket()
            raise

    def send_cemi(self, cemi: bytes) -> int:
        self._require_connected()
        if not isinstance(cemi, bytes) or not cemi or len(cemi) > 65500:
            raise ValueError("cEMI payload must be a non-empty byte string")
        assert self._socket is not None and self.channel_id is not None and self.data_endpoint is not None
        sequence = self.tx_sequence
        payload = bytes((4, self.channel_id, sequence, 0)) + cemi
        packet = encode_frame(TUNNELING_REQ, payload)
        for attempt in range(self.retries + 1):
            self._socket.sendto(packet, self.data_endpoint)
            try:
                frame = self._receive_frame(self.data_endpoint, 0x0421)
                ack = parse_tunneling_ack(encode_frame(frame.service_type, frame.payload))
                if ack.channel_id != self.channel_id or ack.sequence != sequence:
                    continue
                if ack.status != 0:
                    raise KnxTunnelingError(f"KNX TUNNELING_ACK status 0x{ack.status:02X}")
                self.tx_sequence = (sequence + 1) & 0xFF
                return sequence
            except socket.timeout:
                if attempt >= self.retries:
                    self.state = "DEGRADED"
                    raise KnxTunnelingError("KNX TUNNELING_ACK timeout")
        raise KnxTunnelingError("KNX TUNNELING_ACK not received")

    def receive_cemi(self) -> bytes | None:
        self._require_connected()
        assert self._socket is not None and self.channel_id is not None and self.data_endpoint is not None
        self._socket.settimeout(self.timeout_seconds)
        try:
            packet, sender = self._socket.recvfrom(65535)
        except socket.timeout:
            return None
        if (str(sender[0]), int(sender[1])) != self.data_endpoint:
            return None
        frame = decode_frame(packet)
        if frame.service_type != TUNNELING_REQ:
            return None
        payload = frame.payload
        if len(payload) < 5 or payload[0] != 4:
            raise KnxProtocolError("invalid TUNNELING_REQ structure")
        channel, sequence = payload[1], payload[2]
        if channel != self.channel_id or payload[3] != 0:
            raise KnxProtocolError("TUNNELING_REQ channel/reserved mismatch")
        expected = 0 if self.rx_sequence is None else (self.rx_sequence + 1) & 0xFF
        if self.rx_sequence is not None and sequence == self.rx_sequence:
            # A retransmitted frame is acknowledged successfully but never delivered twice.
            self._socket.sendto(build_tunneling_ack(channel, sequence), sender)
            self.last_activity = time.monotonic()
            return None
        if sequence != expected:
            # KNXnet/IP E_SEQUENCE_NUMBER: do not acknowledge an out-of-order
            # frame as successfully consumed, otherwise the gateway may drop it.
            self._socket.sendto(build_tunneling_ack(channel, sequence, 0x04), sender)
            raise KnxProtocolError(
                f"unexpected KNX receive sequence {sequence}, expected {expected}"
            )
        self._socket.sendto(build_tunneling_ack(channel, sequence), sender)
        self.last_activity = time.monotonic()
        self.rx_sequence = sequence
        return payload[4:]

    def heartbeat(self) -> bool:
        self._require_connected()
        assert self._socket is not None and self.channel_id is not None
        hpai = encode_hpai(self.local_host, int(self._socket.getsockname()[1]))
        request = encode_frame(CONNECT_STATE_REQ, bytes((self.channel_id, 0)) + hpai)
        try:
            self._socket.sendto(request, (self.gateway_host, self.gateway_port))
            frame = self._receive_frame((self.gateway_host, self.gateway_port), CONNECT_STATE_RES)
            if len(frame.payload) != 2 or frame.payload[0] != self.channel_id:
                raise KnxProtocolError("invalid CONNECTIONSTATE_RES")
            if frame.payload[1] != 0:
                self.state = "DEGRADED"
                return False
            self.last_heartbeat = time.monotonic()
            return True
        except (socket.timeout, KnxProtocolError):
            self.state = "DEGRADED"
            return False

    def poll_cemi(self) -> bytes | None:
        """Read one inbound cEMI frame and keep the KNX tunnel alive."""
        self._require_connected()
        now = time.monotonic()
        if now - self.last_heartbeat >= self.heartbeat_interval_seconds:
            if not self.heartbeat():
                raise KnxTunnelingError("KNX connection-state heartbeat failed")
        return self.receive_cemi()

    def disconnect(self) -> None:
        if self._socket is None:
            self.state = "DISCONNECTED"
            return
        if self.channel_id is not None and self.connected:
            try:
                hpai = encode_hpai(self.local_host, int(self._socket.getsockname()[1]))
                request = encode_frame(DISCONNECT_REQ, bytes((self.channel_id, 0)) + hpai)
                self._socket.sendto(request, (self.gateway_host, self.gateway_port))
                self._receive_frame((self.gateway_host, self.gateway_port), DISCONNECT_RES)
            except Exception:
                # Teardown is best-effort; local socket closure is mandatory.
                pass
        self._close_socket()
        self.state = "DISCONNECTED"

    def _close_socket(self) -> None:
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                sock.close()
            except Exception:
                pass
        self.channel_id = None
        self.data_endpoint = None
        self.individual_address = None

    def diagnostics(self) -> dict:
        return {
            "state": self.state,
            "connected": self.connected,
            "gateway": f"{self.gateway_host}:{self.gateway_port}",
            "data_endpoint": self.data_endpoint,
            "channel_id": self.channel_id,
            "individual_address": self.individual_address,
            "tx_sequence": self.tx_sequence,
            "rx_sequence": self.rx_sequence,
            "last_activity_monotonic": self.last_activity or None,
            "last_heartbeat_monotonic": self.last_heartbeat or None,
        }

    def close(self) -> None:
        self.disconnect()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.disconnect()
