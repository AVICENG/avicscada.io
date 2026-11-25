"""Read-only BACnet/IP point adapter for the shared AVIC Point Runtime."""
from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any, Callable

from avic_core.network.bacnet_ip import BacnetIpClient


@dataclass(frozen=True, slots=True)
class BacnetIpPointBinding:
    point_id: str
    address: tuple[str, int]
    device_instance: int
    object_type: int
    object_instance: int
    property_id: int = 85  # Present_Value
    array_index: int | None = None
    scale: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        import ipaddress
        if not self.point_id.strip():
            raise ValueError("point_id is required")
        if len(self.address) != 2:
            raise ValueError("BACnet address must be (IPv4, UDP port)")
        ipaddress.ip_address(self.address[0])
        if not 1 <= int(self.address[1]) <= 65535:
            raise ValueError("BACnet UDP port must be in range 1..65535")
        if not 0 <= self.device_instance <= 4_194_303:
            raise ValueError("invalid BACnet Device Instance")
        if not 0 <= self.object_type <= 1023 or not 0 <= self.object_instance <= 4_194_303:
            raise ValueError("invalid BACnet object identifier")
        if not 0 <= self.property_id <= .property_id_max:
            raise ValueError("invalid BACnet property identifier")
        if self.array_index is not None and not 0 <= self.array_index <= 0xFFFFFFFF:
            raise ValueError("invalid BACnet array index")
        if not isfinite(float(self.scale)) or not isfinite(float(self.offset)):
            raise ValueError("scale and offset must be finite")


# Keep the maximum as a named constant so range validation is easy to audit.
BacnetIpPointBinding.property_id_max = 0xFFFFFFFF


class BacnetIpPointAdapter:
    """One-shot read polling. No WriteProperty, reinitialize or time-sync services."""

    def __init__(
        self,
        client: BacnetIpClient,
        point_runtime,
        driver_instance_id: str,
        bindings: tuple[BacnetIpPointBinding, ...] | list[BacnetIpPointBinding],
        *,
        value_transform: Callable[[Any], Any] | None = None,
    ) -> None:
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if len({b.point_id for b in bindings}) != len(bindings):
            raise ValueError("duplicate point_id in BACnet binding map")
        self.client = client
        self.point_runtime = point_runtime
        self.driver_instance_id = driver_instance_id
        self.bindings = tuple(bindings)
        self.value_transform = value_transform
        self._last_errors: dict[str, str] = {}
        self._success_count = 0
        self._failure_count = 0

    def _decode(self, value: Any, binding: BacnetIpPointBinding) -> Any:
        if self.value_transform is not None:
            value = self.value_transform(value)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value) * float(binding.scale) + float(binding.offset)
            if not isfinite(value):
                raise ValueError("decoded/scaled BACnet value is not finite")
        elif binding.scale != 1.0 or binding.offset != 0.0:
            raise ValueError("scale/offset can only be applied to numeric BACnet values")
        return value

    def poll_once(self) -> dict:
        from avic_core.domain.models import PointQuality

        results = []
        for binding in self.bindings:
            try:
                value = self.client.read_property(
                    binding.address, binding.device_instance,
                    binding.object_type, binding.object_instance, binding.property_id,
                    array_index=binding.array_index,
                )
                value = self._decode(value, binding)
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
            "driver_id": "bacnet-ip",
            "mode": "READ_ONLY",
            "write_supported": False,
            "configured_points": len(self.bindings),
            "success_count": self._success_count,
            "failure_count": self._failure_count,
            "last_errors": dict(self._last_errors),
        }
