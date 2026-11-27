"""Read-only Modbus TCP point adapter for the shared AVIC Point Runtime."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Literal

from avic_core.network.modbus_tcp import ModbusTcpClient, decode_registers

ModbusFunction = Literal[1, 2, 3, 4]


@dataclass(frozen=True, slots=True)
class ModbusTcpPointBinding:
    point_id: str
    function: ModbusFunction
    address: int
    count: int = 1
    data_type: str = "uint16"
    byte_order: Literal["big", "little"] = "big"
    word_order: Literal["big", "little"] = "big"
    scale: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        if not self.point_id.strip():
            raise ValueError("point_id is required")
        if self.function not in (1, 2, 3, 4):
            raise ValueError("only Modbus read functions 1..4 are supported")
        if not 0 <= self.address <= 65535:
            raise ValueError("Modbus address must be in range 0..65535")
        max_count = 2000 if self.function in (1, 2) else 125
        if not 1 <= self.count <= max_count or self.address + self.count > 65536:
            raise ValueError("invalid Modbus address/count")
        sizes = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2,
                 "float32": 2, "uint64": 4, "int64": 4, "float64": 4}
        if self.function in (1, 2):
            if self.count != 1 or self.data_type not in {"bool", "boolean"}:
                raise ValueError("coil/discrete input bindings require count=1 and bool data type")
        elif self.data_type not in sizes or sizes[self.data_type] != self.count:
            raise ValueError("register count does not match data_type")
        if self.byte_order not in ("big", "little") or self.word_order not in ("big", "little"):
            raise ValueError("invalid byte/word order")
        if not isfinite(float(self.scale)) or not isfinite(float(self.offset)):
            raise ValueError("scale and offset must be finite")


class ModbusTcpPointAdapter:
    """One-shot polling adapter. It never sends Modbus write function codes."""

    def __init__(self, client: ModbusTcpClient, point_runtime, driver_instance_id: str,
                 bindings: tuple[ModbusTcpPointBinding, ...] | list[ModbusTcpPointBinding]) -> None:
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if len({b.point_id for b in bindings}) != len(bindings):
            raise ValueError("duplicate point_id in Modbus binding map")
        self.client, self.point_runtime = client, point_runtime
        self.driver_instance_id, self.bindings = driver_instance_id, tuple(bindings)
        self._last_errors: dict[str, str] = {}
        self._success_count = self._failure_count = 0

    def _read_group(self, function: int, address: int, count: int) -> list:
        if function == 1:
            return self.client.read_coils(address, count)
        if function == 2:
            return self.client.read_discrete_inputs(address, count)
        if function == 3:
            return self.client.read_holding_registers(address, count)
        return self.client.read_input_registers(address, count)

    def _plan_groups(self) -> list[dict]:
        """Coalesce contiguous read-only bindings to reduce PLC request load."""
        groups: list[dict] = []
        ordered = sorted(self.bindings, key=lambda item: (item.function, item.address, item.count))
        for binding in ordered:
            maximum = 2000 if binding.function in (1, 2) else 125
            binding_end = binding.address + binding.count
            if groups:
                current = groups[-1]
                combined_end = max(current["end"], binding_end)
                if (current["function"] == binding.function
                        and binding.address <= current["end"]
                        and combined_end - current["address"] <= maximum):
                    current["end"] = combined_end
                    current["bindings"].append(binding)
                    continue
            groups.append({"function": binding.function, "address": binding.address,
                           "end": binding_end, "bindings": [binding]})
        return groups

    def _publish_failure(self, binding: ModbusTcpPointBinding, message: str, quality) -> dict:
        self._last_errors[binding.point_id] = message
        self._failure_count += 1
        try:
            sample = self.point_runtime.mark_quality(
                binding.point_id, quality, source_driver_id=self.driver_instance_id)
            return {"point_id": binding.point_id, "ok": False, "value": sample.value,
                    "quality": sample.quality, "error": message}
        except Exception as qexc:
            return {"point_id": binding.point_id, "ok": False, "quality": "UNKNOWN",
                    "error": message, "quality_error": f"{type(qexc).__name__}: {qexc}"}

    def poll_once(self) -> dict:
        from avic_core.domain.models import PointQuality
        results_by_id: dict[str, dict] = {}
        group_count = 0
        for group in self._plan_groups():
            group_count += 1
            count = group["end"] - group["address"]
            try:
                values = self._read_group(group["function"], group["address"], count)
                if len(values) != count:
                    raise ValueError(f"Modbus read returned {len(values)} values; expected {count}")
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                for binding in group["bindings"]:
                    results_by_id[binding.point_id] = self._publish_failure(
                        binding, message, PointQuality.BAD_COMMUNICATION)
                continue

            for binding in group["bindings"]:
                try:
                    offset = binding.address - group["address"]
                    segment = values[offset:offset + binding.count]
                    if len(segment) != binding.count:
                        raise ValueError("Modbus grouped response does not cover binding range")
                    if binding.function in (1, 2):
                        value = bool(segment[0])
                    else:
                        value = decode_registers(segment, binding.data_type,
                            byte_order=binding.byte_order, word_order=binding.word_order)
                        if binding.data_type.startswith("float") or binding.scale != 1.0 or binding.offset != 0.0:
                            value = float(value) * float(binding.scale) + float(binding.offset)
                            if not isfinite(value):
                                raise ValueError("decoded/scaled Modbus value is not finite")
                    sample = self.point_runtime.publish(
                        binding.point_id, value, quality=PointQuality.GOOD,
                        source_driver_id=self.driver_instance_id)
                    self._last_errors.pop(binding.point_id, None)
                    self._success_count += 1
                    results_by_id[binding.point_id] = {"point_id": binding.point_id, "ok": True,
                        "value": sample.value, "quality": sample.quality}
                except Exception as exc:
                    message = f"{type(exc).__name__}: {exc}"
                    results_by_id[binding.point_id] = self._publish_failure(
                        binding, message, PointQuality.BAD_COMMUNICATION)

        results = [results_by_id[b.point_id] for b in self.bindings]
        return {"driver_instance_id": self.driver_instance_id, "polled": len(results),
                "group_count": group_count, "success_count": self._success_count,
                "failure_count": self._failure_count, "results": results}

    def close(self) -> None:
        """Release persistent transport resources (including a supervised Rust process)."""
        close = getattr(self.client, "close", None)
        if callable(close):
            close()

    def diagnostics(self) -> dict:
        client_diagnostics = getattr(self.client, "diagnostics", None)
        return {"driver_id": "modbus-tcp", "mode": "READ_ONLY", "write_supported": False,
                "engine_backend": getattr(self.client, "engine_backend", "python"),
                "engine": client_diagnostics() if callable(client_diagnostics) else None,
                "configured_points": len(self.bindings), "success_count": self._success_count,
                "failure_count": self._failure_count, "last_errors": dict(self._last_errors)}
