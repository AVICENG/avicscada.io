"""Read-only KNX group monitor publishing into AVIC's shared Point Runtime."""
from __future__ import annotations

from dataclasses import dataclass

from avic_core.domain.models import PointQuality
from avic_core.network.knx_cemi import CemiMessageCode, KnxGroupService, parse_cemi_frame
from avic_core.network.knxnet_ip import KnxProtocolError, decode_datapoint, parse_group_address


@dataclass(frozen=True, slots=True)
class KnxPointBinding:
    point_id: str
    group_address: str | int
    datapoint_type: str
    group_address_style: str = "three_level"

    def __post_init__(self):
        if not self.point_id.strip():
            raise ValueError("point_id is required")
        address = parse_group_address(self.group_address, self.group_address_style)
        object.__setattr__(self, "group_address", address)
        normalized = self.datapoint_type.strip().upper().replace("DPT-", "").replace("DPT", "")
        supported = {
            "1.001", "1.002", "1.003", "1.004", "1.005", "1.006", "1.007",
            "1.008", "1.009", "1.010", "1.011", "1.012", "1.013", "1.014",
            "1.015", "1.016", "1.017", "1.018", "1.019", "1.021", "1.022",
            "1.023", "1.024", "1.100", "5.001", "5.003", "5.004", "6.001",
            "7.001", "8.001", "9.001", "12.001", "13.001", "14.000",
            "16.000", "17.001", "18.001",
        }
        if normalized not in supported:
            raise ValueError(f"Unsupported KNX DPT binding: {self.datapoint_type}")
        object.__setattr__(self, "datapoint_type", normalized)


class KnxPointAdapter:
    """Passively monitors mapped group telegrams; does not transmit field writes."""

    def __init__(self, session, point_runtime, driver_instance_id: str, bindings, *,
                 read_mode: str = "passive"):
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if read_mode not in {"passive", "poll"}:
            raise ValueError("KNX read_mode must be 'passive' or 'poll'")
        normalized = tuple(bindings)
        if not normalized:
            raise ValueError("at least one KNX point binding is required")
        if len({b.point_id for b in normalized}) != len(normalized):
            raise ValueError("duplicate point_id in KNX binding map")
        if len({b.group_address for b in normalized}) != len(normalized):
            raise ValueError("duplicate KNX group address in binding map")
        self.session = session
        self.read_mode = read_mode
        self._read_cursor = 0
        self.point_runtime = point_runtime
        self.driver_instance_id = driver_instance_id
        self.bindings = normalized
        self._by_group = {b.group_address: b for b in normalized}
        self._last_errors = {}
        self._success_count = 0
        self._failure_count = 0
        self._ignored_count = 0
        self._malformed_count = 0

    def _mark_all_bad(self, error: str) -> list[dict]:
        results = []
        for binding in self.bindings:
            self._last_errors[binding.point_id] = error
            try:
                sample = self.point_runtime.mark_quality(
                    binding.point_id, PointQuality.BAD_COMMUNICATION,
                    source_driver_id=self.driver_instance_id,
                )
                results.append({"point_id": binding.point_id, "ok": False,
                                "value": sample.value, "quality": sample.quality, "error": error})
            except Exception as exc:
                results.append({"point_id": binding.point_id, "ok": False, "quality": "UNKNOWN",
                                "error": error, "quality_error": f"{type(exc).__name__}: {exc}"})
        self._failure_count += len(results)
        return results

    def poll_once(self) -> dict:
        requested_binding = None
        try:
            if not self.session.connected:
                self.session.connect()
            if self.read_mode == "poll":
                requested_binding = self.bindings[self._read_cursor]
                self._read_cursor = (self._read_cursor + 1) % len(self.bindings)
                individual = self.session.individual_address
                if individual is None:
                    raise KnxProtocolError("KNX gateway did not assign an individual address")
                destination = int(requested_binding.group_address)
                # cEMI L_Data.req with GroupValueRead APCI (0x00), no data.
                read_request = bytes((
                    0x11, 0x00, 0xBC, 0xE0,
                    (int(individual) >> 8) & 0xFF, int(individual) & 0xFF,
                    (destination >> 8) & 0xFF, destination & 0xFF,
                    0x01, 0x00, 0x00,
                ))
                self.session.send_cemi(read_request)
            cemi = self.session.poll_cemi()
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            if requested_binding is None:
                results = self._mark_all_bad(message)
            else:
                self._last_errors[requested_binding.point_id] = message
                self._failure_count += 1
                try:
                    sample = self.point_runtime.mark_quality(
                        requested_binding.point_id, PointQuality.BAD_COMMUNICATION,
                        source_driver_id=self.driver_instance_id,
                    )
                    results = [{"point_id": requested_binding.point_id, "ok": False,
                                "value": sample.value, "quality": sample.quality, "error": message}]
                except Exception as qexc:
                    results = [{"point_id": requested_binding.point_id, "ok": False,
                                "quality": "UNKNOWN", "error": message,
                                "quality_error": f"{type(qexc).__name__}: {qexc}"}]
            return self._result(results)

        if cemi is None:
            if requested_binding is None:
                return self._result([])
            message = "KNX GroupValueRead response timeout"
            self._last_errors[requested_binding.point_id] = message
            self._failure_count += 1
            try:
                sample = self.point_runtime.mark_quality(
                    requested_binding.point_id, PointQuality.BAD_COMMUNICATION,
                    source_driver_id=self.driver_instance_id,
                )
                return self._result([{"point_id": requested_binding.point_id, "ok": False,
                                      "value": sample.value, "quality": sample.quality, "error": message}])
            except Exception as exc:
                return self._result([{"point_id": requested_binding.point_id, "ok": False,
                                      "quality": "UNKNOWN", "error": message,
                                      "quality_error": f"{type(exc).__name__}: {exc}"}])
        try:
            frame = parse_cemi_frame(cemi)
        except KnxProtocolError as exc:
            self._malformed_count += 1
            return self._result([{"ok": False, "error": f"Malformed cEMI: {exc}"}])

        if frame.message_code is not CemiMessageCode.L_DATA_INDICATION:
            self._ignored_count += 1
            return self._result([])
        if not frame.destination_is_group or frame.service not in {
            KnxGroupService.GROUP_VALUE_RESPONSE, KnxGroupService.GROUP_VALUE_WRITE,
        }:
            self._ignored_count += 1
            return self._result([])
        binding = self._by_group.get(frame.destination_address)
        if binding is None:
            self._ignored_count += 1
            return self._result([])

        try:
            if binding.datapoint_type.startswith("1."):
                if frame.short_value is None:
                    raise KnxProtocolError(f"DPT {binding.datapoint_type} requires a short APDU value")
                raw = bytes((frame.short_value,))
            else:
                raw = frame.data
            value = decode_datapoint(raw, binding.datapoint_type)
            sample = self.point_runtime.publish(
                binding.point_id, value, quality=PointQuality.GOOD,
                source_driver_id=self.driver_instance_id,
            )
            self._last_errors.pop(binding.point_id, None)
            self._success_count += 1
            result = {"point_id": binding.point_id, "ok": True,
                      "value": sample.value, "quality": sample.quality,
                      "group_address": frame.destination_address,
                      "source_address": frame.source_address,
                      "service": frame.service.value}
            return self._result([result])
        except Exception as exc:
            message = f"{type(exc).__name__}: {exc}"
            self._last_errors[binding.point_id] = message
            self._failure_count += 1
            try:
                sample = self.point_runtime.mark_quality(
                    binding.point_id, PointQuality.BAD_CONFIGURATION,
                    source_driver_id=self.driver_instance_id,
                )
                result = {"point_id": binding.point_id, "ok": False,
                          "value": sample.value, "quality": sample.quality, "error": message}
            except Exception as qexc:
                result = {"point_id": binding.point_id, "ok": False, "quality": "UNKNOWN",
                          "error": message, "quality_error": f"{type(qexc).__name__}: {qexc}"}
            return self._result([result])

    def _result(self, results):
        return {"driver_instance_id": self.driver_instance_id, "polled": len(results),
                "success_count": self._success_count, "failure_count": self._failure_count,
                "ignored_count": self._ignored_count, "malformed_count": self._malformed_count,
                "results": results}

    def close(self):
        self.session.disconnect()

    def diagnostics(self):
        return {"driver_id": "knxnet-ip",
                "mode": "READ_ONLY_ACTIVE_GROUP_READ" if self.read_mode == "poll" else "READ_ONLY_PASSIVE_GROUP_MONITOR",
                "read_mode": self.read_mode, "write_supported": False, "configured_points": len(self.bindings),
                "success_count": self._success_count, "failure_count": self._failure_count,
                "ignored_count": self._ignored_count, "malformed_count": self._malformed_count,
                "last_errors": dict(self._last_errors), "transport": self.session.diagnostics()}
