"""Read-only enumeration of local IPv4 interfaces for network tools."""
from __future__ import annotations

import ipaddress
from typing import Any


_VPN_MARKERS = ("vpn", "adguard", "wireguard", "openvpn", "tunnel", "tun", "tap", "wintun", "tailscale", "zerotier", "anyconnect", "globalprotect", "forti", "pulse secure", "zscaler")
_VIRTUAL_MARKERS = ("virtual", "vmware", "virtualbox", "hyper-v", "veth", "docker", "wsl", "loopback", "host-only", "bridge")
_WIFI_MARKERS = ("wi-fi", "wifi", "wireless", "wlan", "802.11")


def _interface_kind(name: str) -> str:
    value = name.casefold()
    if any(marker in value for marker in _VPN_MARKERS):
        return "vpn"
    if any(marker in value for marker in _VIRTUAL_MARKERS):
        return "virtual"
    if any(marker in value for marker in _WIFI_MARKERS):
        return "wifi"
    if "ethernet" in value or value.startswith(("eth", "en")) or "gigabit" in value:
        return "ethernet"
    return "other"


def list_ipv4_interfaces() -> list[dict[str, Any]]:
    """Return active IPv4 adapters and recommend a physical LAN over VPN/tunnels."""
    try:
        import psutil  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Для автоматического определения сетевых адаптеров требуется пакет psutil") from exc

    result: list[dict[str, Any]] = []
    stats = psutil.net_if_stats()
    socket_module = __import__("socket")
    for name, addresses in psutil.net_if_addrs().items():
        state = stats.get(name)
        if not state or not state.isup:
            continue
        mac = None
        for item in addresses:
            if item.family == getattr(psutil, "AF_LINK", object()):
                mac = item.address
            if item.family != socket_module.AF_INET or not item.address or not item.netmask:
                continue
            try:
                address = ipaddress.IPv4Address(item.address)
                network = ipaddress.IPv4Network(f"{item.address}/{item.netmask}", strict=False)
            except ValueError:
                continue
            if address.is_loopback or address.is_link_local:
                continue
            kind = _interface_kind(name)
            result.append({
                "id": name, "name": name, "ipv4": str(address),
                "netmask": item.netmask, "prefix_length": network.prefixlen,
                "subnet_cidr": str(network), "broadcast": str(network.broadcast_address),
                "mac": mac, "is_up": True, "kind": kind,
                "kind_label": {"ethernet": "Ethernet", "wifi": "Wi-Fi", "vpn": "VPN", "virtual": "Виртуальный", "other": "Другой"}[kind],
                "recommended": False,
            })

    # Prefer a physical wired LAN; Wi-Fi is a fallback. VPN and virtual adapters
    # remain visible/selectable but are never auto-recommended over a physical NIC.
    priority = {"ethernet": 0, "wifi": 1, "other": 2, "virtual": 3, "vpn": 4}
    result.sort(key=lambda x: (priority[x["kind"]], x["name"].casefold(), x["ipv4"]))
    preferred = next((x for x in result if x["kind"] in ("ethernet", "wifi", "other")), None)
    if preferred is not None:
        preferred["recommended"] = True
        preferred["recommendation_reason"] = "Физический сетевой интерфейс; VPN и виртуальные адаптеры имеют более низкий приоритет"
    return result


def get_interface(interface_id: str) -> dict[str, Any]:
    matches = [x for x in list_ipv4_interfaces() if x["id"] == interface_id]
    if not matches:
        raise ValueError(f"Сетевой интерфейс '{interface_id}' не найден или не имеет активного IPv4")
    return matches[0]
