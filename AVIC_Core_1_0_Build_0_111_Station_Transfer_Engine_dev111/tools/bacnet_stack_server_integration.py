#!/usr/bin/env python3
"""Exercise the AVIC BACnet/IP transaction probe against Steve Karg bacserv.

The simulator is built from the same pinned upstream BACnet Stack revision as
the probe. No AVIC-side BACnet packet encoder or mock protocol implementation
is used by this test.
"""
from __future__ import annotations

import argparse
import ipaddress
import os
import subprocess
import sys
import time
from pathlib import Path


def local_interface() -> tuple[str, str]:
    """Resolve the Linux route interface and verify that it owns an IPv4 address.

    Steve Karg's Linux BACnet/IP port expects BACNET_IFACE to be an interface
    name (for example eth0), not the interface's IPv4 address.
    """
    route = subprocess.run(
        ["ip", "-o", "route", "get", "192.0.2.1"],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=5, check=False,
    )
    if route.returncode != 0:
        raise RuntimeError(
            f"cannot resolve BACnet route interface (ip route exit={route.returncode}): "
            f"{route.stderr.strip()}"
        )
    tokens = route.stdout.split()
    try:
        index = tokens.index("dev")
        interface = tokens[index + 1]
    except (ValueError, IndexError) as exc:
        raise RuntimeError(
            f"route lookup did not report a device interface: {route.stdout.strip()}"
        ) from exc
    if not interface or any(char.isspace() for char in interface):
        raise RuntimeError(f"invalid route interface name: {interface!r}")

    addresses = subprocess.run(
        ["ip", "-o", "-4", "addr", "show", "dev", interface],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=5, check=False,
    )
    if addresses.returncode != 0:
        raise RuntimeError(
            f"cannot inspect IPv4 address for interface {interface!r} "
            f"(ip addr exit={addresses.returncode}): {addresses.stderr.strip()}"
        )
    ipv4 = None
    address_tokens = addresses.stdout.split()
    for position, token in enumerate(address_tokens[:-1]):
        if token == "inet":
            try:
                ipv4 = str(ipaddress.ip_interface(address_tokens[position + 1]).ip)
                break
            except ValueError:
                continue
    if ipv4 is None:
        raise RuntimeError(
            f"route interface {interface!r} has no valid IPv4 address: "
            f"{addresses.stdout.strip()}"
        )
    return interface, ipv4


def run_probe(probe: Path, env: dict[str, str], object_type: int,
              object_instance: int, property_id: int, target_ipv4: str,
              timeout_seconds: float) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(probe), "--read-property-at", "123", target_ipv4, "47808",
         str(object_type), str(object_instance), str(property_id), "5000"],
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

    iface, local_ipv4 = local_interface()
    print(f"BACnet interface: {iface} ({local_ipv4})")
    server_env = os.environ.copy()
    server_env.update({
        "BACNET_IFACE": iface,
        "BACNET_IP_PORT": "47808",
        "BACNET_IP_BROADCAST_PORT": "47808",
        "BACNET_IP_DEBUG": "1",
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
            raise RuntimeError(
                f"bacserv exited during startup ({process.returncode}):\n{output}"
            )

        # bacserv exposes its configured Device object (instance 123). Read
        # Object_Name (property 77), rather than assuming an Analog Input
        # object exists in the example server's default object database.
        ack = run_probe(probe, client_env, 8, 123, 77, local_ipv4, 10.0)
        if ack.returncode != 0 or "bacnet_read_property=ack" not in ack.stdout:
            raise RuntimeError(
                "ReadProperty ACK integration test failed "
                f"(exit={ack.returncode})\nstdout:\n{ack.stdout}\nstderr:\n{ack.stderr}"
            )
        print("bacnet_read_property_ack=passed")
        print(ack.stdout.strip())

        # Property identifier 511 is deliberately unsupported by the Device
        # object and must return a BACnet Error, not be misreported as an ACK.
        error = run_probe(probe, client_env, 8, 123, 511, local_ipv4, 10.0)
        if error.returncode == 0 or "bacnet_read_property_error" not in error.stderr:
            raise RuntimeError(
                "ReadProperty Error integration test failed "
                f"(exit={error.returncode})\nstdout:\n{error.stdout}\nstderr:\n{error.stderr}"
            )
        print("bacnet_read_property_error=passed")
        print(error.stderr.strip())
        return 0
    finally:
        if process.poll() is None:
            process.terminate()
        try:
            server_output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            server_output, _ = process.communicate(timeout=5)
        except ProcessLookupError:
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
