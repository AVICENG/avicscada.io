#!/usr/bin/env python3
"""Python BACnet/IP ReadProperty baseline against a local UDP BACnet peer.

This establishes the current Python serial ReadProperty baseline. It does not
pretend that a Rust BACnet implementation exists yet.
"""
from __future__ import annotations

import argparse
import json
import socket
import socketserver
import struct
import threading
import time
from types import SimpleNamespace

from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding
from avic_core.network.bacnet_ip import BacnetIpClient
from avic_core.network.contracts import BacnetIpNetworkConfig, DiscoveryPolicy


def _free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.2", 0))
        return sock.getsockname()[1]


class BacnetReadPropertyHandler(socketserver.BaseRequestHandler):
    def handle(self):
        packet, server = self.request
        if len(packet) < 17 or packet[:2] != b"\x81\x0a":
            return
        invoke_id = packet[8]
        object_tag = packet[10:15]
        property_tag = packet[15:17]
        ack = (bytes([0x30, invoke_id, 0x0c]) + object_tag + property_tag +
               b"\x3e\x44" + struct.pack(">f", 22.5) + b"\x3f")
        npdu = b"\x01\x00" + ack
        response = b"\x81\x0a" + (len(npdu) + 4).to_bytes(2, "big") + npdu
        server.sendto(response, self.client_address)


class UdpServer(socketserver.ThreadingUDPServer):
    allow_reuse_address = True
    daemon_threads = True


class RuntimeStub:
    def __init__(self):
        self.values = {}
    def publish(self, point_id, value, quality, source_driver_id):
        self.values[point_id] = value
        return SimpleNamespace(value=value, quality=str(getattr(quality, "value", quality)))
    def mark_quality(self, point_id, quality, source_driver_id):
        return SimpleNamespace(value=self.values.get(point_id), quality=str(getattr(quality, "value", quality)))


class TimedBacnetClient(BacnetIpClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.latencies_ms = []
    def read_property(self, *args, **kwargs):
        started = time.perf_counter()
        try:
            return super().read_property(*args, **kwargs)
        finally:
            self.latencies_ms.append((time.perf_counter() - started) * 1000)


def percentile(values, p):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered)-1, int((len(ordered)-1)*p + 0.999999))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--points", type=int, default=10000)
    args = parser.parse_args()
    if not 1 <= args.points <= 100000:
        parser.error("points must be 1..100000")

    port = _free_port()
    server = UdpServer(("127.0.0.2", port), BacnetReadPropertyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    config = BacnetIpNetworkConfig(
        network_id="bench-loopback", interface_name="loopback",
        local_address="127.0.0.1", subnet_cidr="127.0.0.0/8", udp_port=port,
    )
    client = TimedBacnetClient(config, DiscoveryPolicy(request_timeout_seconds=1.0))
    bindings = [
        BacnetIpPointBinding(f"bacnet-point-{i}", ("127.0.0.2", port),
                             1001, 0, i, property_id=85)
        for i in range(args.points)
    ]
    runtime = RuntimeStub()
    adapter = BacnetIpPointAdapter(client, runtime, "python-bacnet-bench", bindings)
    started = time.perf_counter()
    try:
        result = adapter.poll_once()
    finally:
        client.close()
        server.shutdown()
        thread.join(timeout=2)
        server.server_close()
    elapsed = time.perf_counter() - started
    output = {
        "benchmark": "synthetic_bacnet_ip_readproperty_loopback",
        "warning": "Python baseline only; not Rust parity, not hardware acceptance, no COV/RPM.",
        "engine": "python",
        "protocol": "BACnet/IP ReadProperty Present_Value",
        "points": args.points,
        "requests": len(client.latencies_ms),
        "updates": sum(1 for item in result["results"] if item["ok"]),
        "errors": sum(1 for item in result["results"] if not item["ok"]),
        "elapsed_s": round(elapsed, 6),
        "updates_per_s": round(result["polled"] / elapsed, 2) if elapsed else 0,
        "request_p50_ms": round(percentile(client.latencies_ms, 0.50), 3),
        "request_p95_ms": round(percentile(client.latencies_ms, 0.95), 3),
        "request_p99_ms": round(percentile(client.latencies_ms, 0.99), 3),
        "concurrency": 1,
    }
    print(json.dumps(output, indent=2))
    if output["errors"] or output["updates"] != args.points:
        raise SystemExit("BACnet baseline failed: update count mismatch or protocol errors")


if __name__ == "__main__":
    main()
