from __future__ import annotations

import argparse
import json
import socket
import sys
import time
from time import monotonic


def _read_message(reader):
    raw = reader.readline(65537)
    if not raw:
        return None
    if len(raw) > 65536:
        return None
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def run(host: str, port: int, token: str, heartbeat: float) -> int:
    started = monotonic()
    sequence = 0
    state = "RUNNING"
    last_heartbeat = started
    connection = None
    reader = None
    while state == "RUNNING":
        if connection is None:
            try:
                connection = socket.create_connection((host, port), timeout=1.0)
                connection.settimeout(None)
                reader = connection.makefile("rb")
                connection.sendall((json.dumps({"kind": "hello", "token": token}) + "\n").encode("utf-8"))
            except OSError:
                if connection is not None:
                    connection.close()
                connection = reader = None
                time.sleep(min(heartbeat, 1.0))
                last_heartbeat = monotonic()
                continue
        request = _read_message(reader)
        if request is None:
            try: reader.close()
            except Exception: pass
            try: connection.close()
            except Exception: pass
            connection = reader = None
            # Supervisor loss is not a field stop. Keep the service process alive
            # and retry its control connection while the local runtime continues.
            last_heartbeat = monotonic()
            continue
        if request.get("protocol") != 1:
            continue
        command = request.get("command")
        request_id = request.get("request_id")
        try:
            received_sequence = int(request.get("sequence", 0))
        except (TypeError, ValueError):
            received_sequence = 0
        if received_sequence <= sequence:
            response = {"ok": False, "request_id": request_id, "error": "stale command sequence"}
        else:
            sequence = received_sequence
            last_heartbeat = monotonic()
            if command in {"status", "ping"}:
                response = {"ok": True, "request_id": request_id, "protocol": 1,
                            "state": state, "pid": __import__("os").getpid(),
                            "uptime_seconds": max(0.0, monotonic() - started),
                            "last_command_sequence": sequence,
                            "last_heartbeat_monotonic": last_heartbeat,
                            "active_strategies": 0, "execution_engine_attached": False,
                            "capability_state": "PROCESS_HOST_ONLY"}
            elif command == "maintenance_stop":
                import hmac
                authorized = hmac.compare_digest(str(request.get("maintenance_token", "")), token)
                confirmed = request.get("confirmation") == "STOP FIELD RUNTIME"
                if authorized and confirmed:
                    state = "STOPPED"
                    response = {"ok": True, "request_id": request_id, "state": state}
                else:
                    response = {"ok": False, "request_id": request_id, "error": "maintenance authorization rejected"}
            else:
                response = {"ok": False, "request_id": request_id, "error": "unsupported command"}
        try:
            connection.sendall((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
        except OSError:
            try: reader.close()
            except Exception: pass
            try: connection.close()
            except Exception: pass
            connection = reader = None
    if reader is not None:
        try: reader.close()
        except Exception: pass
    if connection is not None:
        try: connection.close()
        except Exception: pass
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--heartbeat", type=float, default=0.25)
    args = parser.parse_args()
    token = sys.stdin.readline().strip()
    if not token:
        return 2
    return run(args.host, args.port, token, args.heartbeat)


if __name__ == "__main__":
    raise SystemExit(main())
