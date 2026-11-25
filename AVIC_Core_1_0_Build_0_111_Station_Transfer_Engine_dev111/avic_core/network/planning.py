"""Validated network planning and deployment-binding contracts.

These contracts describe intended addressing. They never change the host adapter,
router, gateway, DHCP scope, NAT, or field-device configuration.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress


@dataclass(frozen=True)
class NetworkPlan:
    name: str
    subnet_cidr: str
    station_ipv4: str
    gateway_ipv4: str | None = None
    dns_servers: tuple[str, ...] = ()
    addressing_mode: str = "manual"

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("Название сети обязательно")
        if self.addressing_mode not in {"auto", "manual"}:
            raise ValueError("addressing_mode должен быть auto или manual")
        try:
            network = ipaddress.IPv4Network(self.subnet_cidr, strict=False)
            station = ipaddress.IPv4Address(self.station_ipv4)
        except ValueError as exc:
            raise ValueError("Требуется корректная IPv4-подсеть и адрес станции") from exc
        if station not in network or station in {network.network_address, network.broadcast_address}:
            raise ValueError("IP станции должен быть доступным адресом внутри заданной подсети")
        if self.gateway_ipv4:
            try:
                gateway = ipaddress.IPv4Address(self.gateway_ipv4)
            except ValueError as exc:
                raise ValueError("Некорректный IPv4 шлюза") from exc
            if gateway not in network or gateway in {network.network_address, network.broadcast_address}:
                raise ValueError("Шлюз должен находиться в заданной подсети")
            if gateway == station:
                raise ValueError("IP станции не может совпадать с IP шлюза")
        for dns in self.dns_servers:
            try:
                ipaddress.IPv4Address(dns)
            except ValueError as exc:
                raise ValueError(f"Некорректный DNS IPv4: {dns}") from exc

    def as_dict(self) -> dict:
        return {
            "name": self.name.strip(), "addressing_mode": self.addressing_mode,
            "station_ipv4": self.station_ipv4,
            "subnet_cidr": str(ipaddress.IPv4Network(self.subnet_cidr, strict=False)),
            "gateway_ipv4": self.gateway_ipv4 or None,
            "dns_servers": list(self.dns_servers),
        }


def assess_deployment_binding(plan: NetworkPlan, interfaces: list[dict]) -> dict:
    """Compare a planned station IP/subnet with currently detected local adapters."""
    matches = [item for item in interfaces if item.get("subnet_cidr") == str(ipaddress.IPv4Network(plan.subnet_cidr, strict=False))]
    exact = [item for item in matches if item.get("ipv4") == plan.station_ipv4]
    if exact:
        status, message = "BOUND", "Текущий компьютер использует запланированный IP-адрес станции."
    elif matches:
        status, message = "SUBNET_PRESENT_ADDRESS_MISMATCH", "Подсеть доступна, но IP текущего компьютера отличается от проектного адреса станции."
    else:
        status, message = "PLANNED_NOT_PRESENT", "Проектная сеть сохранена; соответствующая подсеть на этом компьютере не обнаружена."
    return {"status": status, "message": message,
            "planned_station_ipv4": plan.station_ipv4,
            "planned_subnet_cidr": str(ipaddress.IPv4Network(plan.subnet_cidr, strict=False)),
            "matching_interfaces": [{"id": x.get("id"), "name": x.get("name"), "ipv4": x.get("ipv4")} for x in matches],
            "exact_binding": bool(exact), "configuration_changed": False}
