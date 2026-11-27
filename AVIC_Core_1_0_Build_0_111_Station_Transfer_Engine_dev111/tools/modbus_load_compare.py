#!/usr/bin/env python3
"""Comparable Python-adapter vs Rust-kernel Modbus TCP benchmark.

Starts a local Modbus TCP simulator, runs both engines against the same server,
and prints measurements. This is a repeatable synthetic benchmark, not hardware acceptance.
"""
from __future__ import annotations

import argparse
import json
import socketserver
import statistics
import subprocess
import sys
import threading
import time
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor

from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.network.modbus_tcp import ModbusTcpClient


def recv_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            raise ConnectionError("client disconnected")
        data.extend(part)
    return bytes(data)


class ModbusHandler(socketserver.BaseRequestHandler):
    def handle(self):
        # DEV221 keeps one TCP socket open for multiple sequential Modbus reads.
        # Serve a stream of ADUs until the client closes the connection; a
        # one-request-per-socket fixture only exercised the pre-DEV221 behavior.
        while True:
            try:
                header = recv_exact(self.request, 7)
                tid = int.from_bytes(header[0:2], "big")
                protocol = int.from_bytes(header[2:4], "big")
                length = int.from_bytes(header[4:6], "big")
                unit = header[6]
                if protocol != 0 or length < 6 or length > 260:
                    return
                pdu = recv_exact(self.request, length - 1)
                if len(pdu) != 5 or pdu[0] != 3:
                    return
                address = int.from_bytes(pdu[1:3], "big")
                count = int.from_bytes(pdu[3:5], "big")
                if not 1 <= count <= 125 or address + count > 65536:
                    return
                payload = bytes([3, count * 2]) + b"".join(
                    ((address + i) & 0xffff).to_bytes(2, "big") for i in range(count)
                )
                response = (tid.to_bytes(2, "big") + b"\\x00\\x00" +
                            (len(payload) + 1).to_bytes(2, "big") + bytes([unit]) + payload)
                self.request.sendall(response)
            except (OSError, ConnectionError):
                return

class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


class RuntimeStub:
    def __init__(self):
        self.values = {}
    def publish(self, point_id, value, quality, source_driver_id):
        self.values[point_id] = value
        return SimpleNamespace(value=value, quality=str(quality.value if hasattr(quality, "value") else quality))
    def mark_quality(self, point_id, quality, source_driver_id):
        return SimpleNamespace(value=None, quality=str(quality.value if hasattr(quality, "value") else quality))


def percentile(values, p):
    if not values:
        return 0.0
    values = sorted(values)
    return values[min(len(values) - 1, int((len(values) - 1) * p + 0.999999))]


def run_python(host, port, devices, points, cycles, concurrency):
    latencies = []
    latency_lock = threading.Lock()
    updates = 0
    errors = 0
    counts_lock = threading.Lock()

    def worker(worker_id):
        nonlocal updates, errors
        local_updates = local_errors = 0
        local_latencies = []
        for device in range(worker_id, devices, min(concurrency, devices)):
            driver_id = f"py-driver-{device}"
            bindings = [ModbusTcpPointBinding(
                f"{driver_id}-point-{i}", 3, i, data_type="uint16"
            ) for i in range(points)]
            adapter = ModbusTcpPointAdapter(
                ModbusTcpClient(host, port, unit_id=(device % 247) + 1, timeout=2.0),
                RuntimeStub(), driver_id, bindings
            )
            for _ in range(cycles):
                started = time.perf_counter()
                result = adapter.poll_once()
                local_latencies.append((time.perf_counter() - started) * 1000)
                local_updates += sum(1 for item in result["results"] if item["ok"])
                local_errors += sum(1 for item in result["results"] if not item["ok"])
        with counts_lock:
            updates += local_updates
            errors += local_errors
        with latency_lock:
            latencies.extend(local_latencies)

    started = time.perf_counter()
    workers = min(concurrency, devices)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(worker, range(workers)))
    elapsed = time.perf_counter() - started
    return {
        "engine": "python",
        "devices": devices,
        "points_per_device": points,
        "cycles": cycles,
        "concurrency": workers,
        "updates": updates,
        "requests": devices * cycles,
        "errors": errors,
        "elapsed_s": round(elapsed, 6),
        "updates_per_s": round(updates / elapsed, 2) if elapsed else 0,
        "request_p50_ms": round(percentile(latencies, 0.50), 3),
        "request_p95_ms": round(percentile(latencies, 0.95), 3),
        "request_p99_ms": round(percentile(latencies, 0.99), 3),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--devices", type=int, default=100)
    parser.add_argument("--points-per-device", type=int, default=100)
    parser.add_argument("--cycles", type=int, default=10)
    parser.add_argument("--concurrency", type=int, default=8)
    args = parser.parse_args()
    if args.devices < 1 or not 1 <= args.points_per_device <= 125 or args.cycles < 1 or args.concurrency < 1:
        parser.error("devices/cycles/concurrency must be positive; points-per-device must be 1..125")

    with Server(("127.0.0.1", 0), ModbusHandler) as server:
        host, port = server.server_address
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        py_result = run_python(host, port, args.devices, args.points_per_device,
                               args.cycles, args.concurrency)

        crate = Path(__file__).resolve().parent.parent / "rust" / "avic-communication-engine"
        subprocess.run(["cargo", "build", "--release", "--manifest-path", str(crate / "Cargo.toml")], check=True)
        exe = crate / "target" / "release" / ("avic-modbus-bench.exe" if sys.platform == "win32" else "avic-modbus-bench")
        rust_run = subprocess.run(
            [str(exe), host, str(port), str(args.devices), str(args.points_per_device),
             str(args.cycles), str(args.concurrency)],
            check=True, capture_output=True, text=True
        )
        rust_line = next(line for line in rust_run.stdout.splitlines() if line.startswith("engine=rust "))
        fields = dict(part.split("=", 1) for part in rust_line.split() if "=" in part)
        rust_result = {
            "engine": "rust", "devices": int(fields["devices"]),
            "points_per_device": int(fields["points_per_device"]), "cycles": int(fields["cycles"]),
            "concurrency": int(fields["concurrency"]), "updates": int(fields["updates"]),
            "requests": int(fields["requests"]), "errors": int(fields["errors"]),
            "elapsed_s": float(fields["elapsed_s"]), "updates_per_s": float(fields["updates_per_s"]),
            "request_p50_ms": float(fields["request_p50_ms"]),
            "request_p95_ms": float(fields["request_p95_ms"]),
            "request_p99_ms": float(fields["request_p99_ms"]),
        }
        server.shutdown()
        thread.join(timeout=2)

    results = {"benchmark": "synthetic_modbus_tcp_fc03_same_local_simulator",
               "warning": "Synthetic loopback benchmark only; not hardware acceptance or production capacity evidence.",
               "python": py_result, "rust": rust_result}
    print(json.dumps(results, indent=2))
    if py_result["errors"] or rust_result["errors"] or py_result["updates"] != rust_result["updates"]:
        raise SystemExit("benchmark parity failed: errors or update count mismatch")


if __name__ == "__main__":
    main()
