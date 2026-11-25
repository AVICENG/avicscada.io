"""Bounded, single-target IPv4 reachability probe; no shell and no configuration writes."""
from __future__ import annotations

import ipaddress
import platform
import subprocess


def ping_ipv4(address: str, timeout_seconds: float = 2.0) -> dict:
    try:
        target = ipaddress.ip_address(address)
    except ValueError as exc:
        raise ValueError("Некорректный IP-адрес") from exc
    if target.version != 4:
        raise ValueError("Поддерживается только IPv4")
    if not 0.1 <= float(timeout_seconds) <= 3.0:
        raise ValueError("Тайм-аут Ping должен быть от 0.1 до 3 секунд")
    system = platform.system().lower()
    if system == "windows":
        command = ["ping", "-n", "1", "-w", str(int(timeout_seconds * 1000)), str(target)]
    else:
        command = ["ping", "-c", "1", "-W", str(max(1, int(timeout_seconds))), str(target)]
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout_seconds + 1.0, check=False)
    except FileNotFoundError:
        return {"address": str(target), "reachable": None, "status": "PING_UNAVAILABLE",
                "message": "Утилита ping отсутствует; используйте проверку TCP-порта.", "rtt_ms": None}
    except subprocess.TimeoutExpired:
        return {"address": str(target), "reachable": False, "status": "TIMEOUT",
                "message": "Истекло время ожидания ответа Ping.", "rtt_ms": None}
    output = (result.stdout or "") + "\n" + (result.stderr or "")
    import re
    match = re.search(r"(?:time|время)[=<]\s*(\d+(?:[.,]\d+)?)\s*ms", output, re.IGNORECASE)
    rtt = float(match.group(1).replace(",", ".")) if match else None
    reachable = result.returncode == 0
    return {"address": str(target), "reachable": reachable,
            "status": "REACHABLE" if reachable else "NO_REPLY",
            "message": "Узел ответил на Ping." if reachable else "Ответ на Ping не получен. ICMP может быть запрещён политикой сети.",
            "rtt_ms": rtt, "method": "ICMP_ECHO", "configuration_changed": False}
