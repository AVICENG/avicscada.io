"""Read-only Modbus TCP point adapter for the shared AVIC Point Runtime."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Callable, Literal

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
        expected = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2,
                    "float32": 2, "uint64": 4, "int64": 4, "float64": 4}
        if self.function in (1, 2):
            if self.count != 1 or self.data_type not in {"bool", "boolean"}:
                raise ValueError("coil/discrete input bindings require count=1 and bool data type")
        elif self.data_type not in expected or expected[self.data_type] != self.count:
            raise ValueError("register count does not match data_type")
        if self.byte_order not in ("big", "little") or self.word_order not in ("big", "little"):
            raise ValueError("invalid byte/word order")
        if not isfinite(float(self.scale)) or not isfinite(float(self.offset)):
            raise ValueError("scale and offset must be finite")


class ModbusTcpPointAdapter:
    """One-shot polling adapter. It never sends Modbus write function codes."""

    def __init__(
        self,
        client: ModbusTcpClient,
        point_runtime,
        driver_instance_id: str,
        bindings: tuple[ModbusTcpPointBinding, ...] | list[ModbusTcpPointBinding],
        *,
        client_factory: Callable[..., ModbusTcpClient] | None = None,
    ) -> None:
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if len({b.point_id for b in bindings}) != len(bindings):
            raise ValueError("duplicate point_id in Modbus binding map")
        self.client = client
        self.point_runtime = point_runtime
        self.driver_instance_id = driver_instance_id
        self.bindings = tuple(bindings)
        self._client_factory = client_factory
        self._last_errors: dict[str, str] = {}
        self._success_count = 0
        self._failure_count = 0

    def _read_binding(self, binding: ModbusTcpPointBinding):
        if binding.function == 1:
            raw = self.client.read_coils(binding.address, 1)
            return bool(raw[0])
        if binding.function == 2:
            raw = self.client.read_discrete_inputs(binding.address, 1)
            return bool(raw[0])
        if binding.function == 3:
            raw = self.client.read_holding_registers(binding.address, binding.count)
        else:
            raw = self.client.read_input_registers(binding.address, binding.count)
        value = decode_registers(
            raw, binding.data_type, byte_order=binding.byte_order, word_order=binding.word_order
        )
        if binding.data_type.startswith("float") or binding.scale != 1.0 or binding.offset != 0.0:
            value = float(value) * float(binding.scale) + float(binding.offset)
            if not isfinite(value):
                raise ValueError("decoded/scaled Modbus value is not finite")
        return value

    def poll_once(self) -> dict:
        """Poll all configured input bindings; isolate failures per point."""
        from avic_core.domain.models import PointQuality

        results = []
        for binding in self.bindings:
            try:
                value = self._read_binding(binding)
                sample = self.point_runtime.publish(
                    binding.point_id, value, quality=PointQuality.GOOD,
                    source_driver_id=self.driver_instance_id,
                )
                self._last_errors.pop(binding.point_id, None)
                self._success_count += 1
                results.append({"point_id": binding.point_id, "ok": True,
                                "value": sample.value, "quality": sample.quality})
            except Exception as exc:
                message = f"{type(exc).__name__}: {exc}"
                self._last_errors[binding.point_id] = message
                self._failure_count += 1
                try:
                    sample = self.point_runtime.mark_quality(
                        binding.point_id, PointQuality.BAD_COMMUNICATION,
                        source_driver_id=self.driver_instance_id,
                    )
                    results.append({"point_id": binding.point_id, "ok": False,
                                    "value": sample.value, "quality": sample.quality,
                                    "error": message})
                except Exception as quality_exc:
                    results.append({"point_id": binding.point_id, "ok": False,
                                    "quality": "UNKNOWN", "error": message,
                                    "quality_error": f"{type(quality_exc).__name__}: {quality_exc}"})
        return {
            "driver_instance_id": self.driver_instance_id,
            "polled": len(results),
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "results": results,
        }

    def diagnostics(self) -> dict:
        return {
            "driver_id": "modbus-tcp",
            "mode": "READ_ONLY",
            "write_supported": False,
            "configured_points": len(self.bindings),
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "last_errors": dict(self._last_errors),
        }
