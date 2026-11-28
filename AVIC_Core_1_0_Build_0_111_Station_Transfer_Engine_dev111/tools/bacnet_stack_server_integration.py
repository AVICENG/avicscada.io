#!/usr/bin/env python3
"""Exercise the AVIC BACnet/IP transaction probe against Steve Karg bacserv.

The simulator is built from the same pinned upstream BACnet Stack revision as
the probe. No AVIC-side BACnet packet encoder or mock protocol implementation
is used by this test.
"""
from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def local_interface_address() -> str:
    """Ask the OS routing table which local IPv4 address it would use."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect(("192.0.2.1", 9))
        return str(sock.getsockname()[0])


def run_probe(probe: Path, env: dict[str, str], property_id: int,
              timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(probe), "--read-property", "123", "0", "0",
         str(property_id), "5000"],
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", required=True, type=Path)
    parser.add_argument("--probe", required=True, type=Path)
    args = parser.parse_args()
    server = args.server.resolve()
    probe = args.probe.resolve()
    if not server.is_file() or not probe.is_file():
        raise SystemExit(f"missing simulator or probe: server={server}, probe={probe}")

    iface = local_interface_address()
    server_env = os.environ.copy()
    server_env.update({
        "BACNET_IFACE": iface,
        "BACNET_IP_PORT": "47808",
        "BACNET_IP_BROADCAST_PORT": "47808",
    })
    client_env = os.environ.copy()
    client_env.update({
        "BACNET_IFACE": iface,
        "BACNET_IP_PORT": "47809",
        "BACNET_IP_BROADCAST_PORT": "47808",
    })

    process = subprocess.Popen(
        [str(server), "123", "AVIC-CI-BACnet-Simulator"],
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        # Give the upstream server time to bind its UDP socket.
        time.sleep(0.75)
        if process.poll() is not None:
            output, _ = process.communicate()
            raise RuntimeError(f"bacserv exited during startup ({process.returncode}):\\n{output}")

        ack = run_probe(probe, client_env, 85, 10.0)
        if ack.returncode != 0 or "bacnet_read_property=ack" not in ack.stdout:
            raise RuntimeError(
                "ReadProperty ACK integration test failed "
                f"(exit={ack.returncode})\\nstdout:\\n{ack.stdout}\\nstderr:\\n{ack.stderr}"
            )
        print("bacnet_read_property_ack=passed")
        print(ack.stdout.strip())

        # Property identifier 511 is deliberately unsupported by the example
        # server and must return a BACnet Error, not be misreported as an ACK.
        error = run_probe(probe, client_env, 511, 10.0)
        if error.returncode == 0 or "bacnet_read_property_error" not in error.stderr:
            raise RuntimeError(
                "ReadProperty Error integration test failed "
                f"(exit={error.returncode})\\nstdout:\\n{error.stdout}\\nstderr:\\n{error.stderr}"
            )
        print("bacnet_read_property_error=passed")
        print(error.stderr.strip())
        return 0
    finally:
        process.terminate()
        try:
            server_output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            server_output, _ = process.communicate(timeout=5)
        if server_output:
            print("bacserv_log_begin", file=sys.stderr)
            print(server_output[-12000:], file=sys.stderr)
            print("bacserv_log_end", file=sys.stderr)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"BACnet simulator integration failure: {exc}", file=sys.stderr)
        raise SystemExit(1)
