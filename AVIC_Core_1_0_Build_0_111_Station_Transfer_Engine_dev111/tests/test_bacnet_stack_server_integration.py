from __future__ import annotations

import subprocess

import pytest

from tools.bacnet_stack_server_integration import local_interface


def _completed(stdout: str = "", *, returncode: int = 0, stderr: str = ""):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


def test_local_interface_uses_route_device_name_not_source_ip(monkeypatch):
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        if command[:4] == ["ip", "-o", "route", "get"]:
            return _completed("192.0.2.1 via 10.0.0.1 dev enp3s0 src 10.0.0.42 uid 1000")
        return _completed("2: enp3s0 inet 10.0.0.42/24 brd 10.0.0.255 scope global enp3s0")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert local_interface() == ("enp3s0", "10.0.0.42")
    assert calls[1] == ["ip", "-o", "-4", "addr", "show", "dev", "enp3s0"]


def test_local_interface_rejects_route_without_dev(monkeypatch):
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed("192.0.2.1 via 10.0.0.1"))
    with pytest.raises(RuntimeError, match="did not report a device"):
        local_interface()


def test_local_interface_rejects_interface_without_ipv4(monkeypatch):
    def fake_run(command, **kwargs):
        if command[:4] == ["ip", "-o", "route", "get"]:
            return _completed("192.0.2.1 dev eth0 src 10.0.0.42")
        return _completed("2: eth0 inet6 fe80::1/64 scope link")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="no valid IPv4"):
        local_interface()


def test_local_interface_reports_route_command_failure(monkeypatch):
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **k: _completed(returncode=2, stderr="network unreachable"),
    )
    with pytest.raises(RuntimeError, match="network unreachable"):
        local_interface()


def test_local_interface_reports_address_command_failure(monkeypatch):
    def fake_run(command, **kwargs):
        if command[:4] == ["ip", "-o", "route", "get"]:
            return _completed("192.0.2.1 dev eth0 src 10.0.0.42")
        return _completed(returncode=1, stderr="device not found")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(RuntimeError, match="device not found"):
        local_interface()
