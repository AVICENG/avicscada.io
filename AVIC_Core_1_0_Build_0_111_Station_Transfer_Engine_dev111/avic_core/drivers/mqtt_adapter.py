"""Read-only MQTT point adapter with explicit session lifecycle.

The adapter accepts a configured Paho-compatible client. TLS, credentials and
certificate policy must be configured on that client by the deployment layer.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from math import isfinite
from typing import Any

_MAX_PAYLOAD_BYTES = 1_048_576


def mqtt_topic_matches(topic_filter: str, topic: str) -> bool:
    """Match an MQTT topic filter using the MQTT 3.1.1/5.0 level rules."""
    if not isinstance(topic_filter, str) or not topic_filter:
        return False
    if not isinstance(topic, str) or not topic:
        return False
    # Wildcard subscriptions do not match system topics unless the filter
    # explicitly starts with '(frozen=True, slots=True)
class MqttPointBinding:
    point_id: str
    topic: str
    qos: int = 1
    payload_format: str = "json"
    value_path: str = "value"
    scale: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        if not self.point_id.strip() or not self.topic.strip():
            raise ValueError("point_id and topic are required")
        levels = self.topic.split("/")
        if any(("#" in level and level != "#") or ("+" in level and level != "+")
               for level in levels) or ("#" in levels and levels[-1] != "#"):
            raise ValueError("MQTT wildcards must occupy a complete level and # must be final")
        if self.qos not in (0, 1, 2):
            raise ValueError("MQTT QoS must be 0, 1 or 2")
        if self.payload_format not in ("json", "raw"):
            raise ValueError("payload_format must be json or raw")
        if self.payload_format == "json" and not self.value_path.strip():
            raise ValueError("JSON value_path is required")
        if not isfinite(float(self.scale)) or not isfinite(float(self.offset)):
            raise ValueError("scale and offset must be finite")


class MqttPointAdapter:
    """Subscribe-only MQTT adapter. It never publishes commands to a broker."""

    def __init__(self, client: Any, point_runtime: Any, driver_instance_id: str,
                 bindings: tuple[MqttPointBinding, ...] | list[MqttPointBinding], *,
                 host: str, port: int = 1883, keepalive: int = 60) -> None:
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if not host.strip() or not 1 <= port <= 65535 or not 10 <= keepalive <= 3600:
            raise ValueError("invalid MQTT host, port or keepalive")
        if len({b.point_id for b in bindings}) != len(bindings):
            raise ValueError("duplicate point_id in MQTT binding map")
        self.client, self.point_runtime = client, point_runtime
        self.driver_instance_id, self.bindings = driver_instance_id, tuple(bindings)
        self.host, self.port, self.keepalive = host, port, keepalive
        self._connected = False
        self._started = False
        self._success_count = self._failure_count = 0
        self._last_errors: dict[str, str] = {}
        self._last_message_at: dict[str, str] = {}
        # The adapter owns these callbacks for its configured client instance.
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        if self._started:
            return
        self.client.connect(self.host, self.port, self.keepalive)
        self.client.loop_start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        try:
            self.client.loop_stop()
        finally:
            try:
                self.client.disconnect()
            finally:
                self._started = False
                self._set_disconnected()

    @staticmethod
    def _reason_failed(reason_code: Any) -> bool:
        if hasattr(reason_code, "is_failure"):
            return bool(reason_code.is_failure)
        try:
            return int(reason_code) != 0
        except (TypeError, ValueError):
            return str(reason_code).casefold() not in ("success", "0", "none")

    def _on_connect(self, client: Any, userdata: Any, flags: Any,
                    reason_code: Any, properties: Any = None) -> None:
        if self._reason_failed(reason_code):
            self._connected = False
            self._set_disconnected()
            self._last_errors["__connection__"] = f"MQTT connect rejected: {reason_code}"
            return
        self._connected = True
        self._last_errors.pop("__connection__", None)
        subscriptions = {}
        for binding in self.bindings:
            subscriptions[binding.topic] = max(subscriptions.get(binding.topic, 0), binding.qos)
        for topic, qos in subscriptions.items():
            result = client.subscribe(topic, qos=qos)
            if isinstance(result, tuple) and result and int(result[0]) != 0:
                self._last_errors[f"__subscribe__:{topic}"] = f"subscribe failed: {result}"
                self._failure_count += 1

    def _on_disconnect(self, client: Any, userdata: Any, disconnect_flags: Any = None,
                       reason_code: Any = None, properties: Any = None) -> None:
        self._connected = False
        if reason_code is not None and self._reason_failed(reason_code):
            self._last_errors["__connection__"] = f"MQTT disconnected: {reason_code}"
        self._set_disconnected()

    def _set_disconnected(self) -> None:
        from avic_core.domain.models import PointQuality
        for binding in self.bindings:
            try:
                self.point_runtime.mark_quality(
                    binding.point_id, PointQuality.BAD_COMMUNICATION,
                    source_driver_id=self.driver_instance_id)
            except Exception as exc:
                self._last_errors[binding.point_id] = f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _extract(payload: bytes, binding: MqttPointBinding) -> Any:
        if len(payload) > _MAX_PAYLOAD_BYTES:
            raise ValueError("MQTT payload exceeds 1 MiB safety limit")
        if binding.payload_format == "raw":
            value: Any = payload.decode("utf-8")
        else:
            value = json.loads(payload.decode("utf-8"))
            for part in binding.value_path.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
                    value = value[int(part)]
                else:
                    raise ValueError(f"JSON value_path not found: {binding.value_path}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value) * float(binding.scale) + float(binding.offset)
            if not isfinite(value):
                raise ValueError("decoded/scaled MQTT value is not finite")
        elif binding.scale != 1.0 or binding.offset != 0.0:
            raise ValueError("scale/offset can only be applied to numeric MQTT values")
        return value

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        from datetime import datetime, timezone
        from avic_core.domain.models import PointQuality
        topic = str(message.topic)
        matched = [b for b in self.bindings if mqtt_topic_matches(b.topic, topic)]
        for binding in matched:
            try:
                value = self._extract(bytes(message.payload), binding)
                sample = self.point_runtime.publish(
                    binding.point_id, value, quality=PointQuality.GOOD,
                    timestamp=datetime.now(timezone.utc),
                    source_driver_id=self.driver_instance_id)
                self._last_errors.pop(binding.point_id, None)
                self._last_message_at[binding.point_id] = sample.timestamp.isoformat() if sample.timestamp else ""
                self._success_count += 1
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                self._last_errors[binding.point_id] = error
                self._failure_count += 1
                try:
                    self.point_runtime.mark_quality(
                        binding.point_id, PointQuality.BAD_CONFIGURATION,
                        source_driver_id=self.driver_instance_id)
                except Exception as quality_exc:
                    self._last_errors[binding.point_id] += (
                        f"; quality update failed: {type(quality_exc).__name__}: {quality_exc}")

    def diagnostics(self) -> dict:
        return {
            "driver_id": "mqtt", "mode": "READ_ONLY_SUBSCRIBE",
            "write_supported": False, "connected": self._connected,
            "started": self._started, "broker": f"{self.host}:{self.port}",
            "configured_points": len(self.bindings),
            "subscribed_topics": len({b.topic for b in self.bindings}),
            "success_count": self._success_count, "failure_count": self._failure_count,
            "last_message_at": dict(self._last_message_at),
            "last_errors": dict(self._last_errors),
        }
 (MQTT-3.3.2- દ).
    if topic.startswith("$") and topic_filter[0] in {"+", "#"}:
        return False
    filters = topic_filter.split("/")
    levels = topic.split("/")
    for index, level_filter in enumerate(filters):
        if level_filter == "#":
            return index == len(filters) - 1
        if index >= len(levels):
            return False
        if level_filter != "+" and level_filter != levels[index]:
            return False
    return len(filters) == len(levels)


@dataclass(frozen=True, slots=True)
class MqttPointBinding:
    point_id: str
    topic: str
    qos: int = 1
    payload_format: str = "json"
    value_path: str = "value"
    scale: float = 1.0
    offset: float = 0.0

    def __post_init__(self) -> None:
        if not self.point_id.strip() or not self.topic.strip():
            raise ValueError("point_id and topic are required")
        if self.qos not in (0, 1, 2):
            raise ValueError("MQTT QoS must be 0, 1 or 2")
        if self.payload_format not in ("json", "raw"):
            raise ValueError("payload_format must be json or raw")
        if self.payload_format == "json" and not self.value_path.strip():
            raise ValueError("JSON value_path is required")
        if not isfinite(float(self.scale)) or not isfinite(float(self.offset)):
            raise ValueError("scale and offset must be finite")


class MqttPointAdapter:
    """Subscribe-only MQTT adapter. It never publishes commands to a broker."""

    def __init__(self, client: Any, point_runtime: Any, driver_instance_id: str,
                 bindings: tuple[MqttPointBinding, ...] | list[MqttPointBinding], *,
                 host: str, port: int = 1883, keepalive: int = 60) -> None:
        if not driver_instance_id.strip():
            raise ValueError("driver_instance_id is required")
        if not host.strip() or not 1 <= port <= 65535 or not 10 <= keepalive <= 3600:
            raise ValueError("invalid MQTT host, port or keepalive")
        if len({b.point_id for b in bindings}) != len(bindings):
            raise ValueError("duplicate point_id in MQTT binding map")
        self.client, self.point_runtime = client, point_runtime
        self.driver_instance_id, self.bindings = driver_instance_id, tuple(bindings)
        self.host, self.port, self.keepalive = host, port, keepalive
        self._connected = False
        self._started = False
        self._success_count = self._failure_count = 0
        self._last_errors: dict[str, str] = {}
        self._last_message_at: dict[str, str] = {}
        # The adapter owns these callbacks for its configured client instance.
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

    def start(self) -> None:
        if self._started:
            return
        self.client.connect(self.host, self.port, self.keepalive)
        self.client.loop_start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return
        try:
            self.client.loop_stop()
        finally:
            try:
                self.client.disconnect()
            finally:
                self._started = False
                self._set_disconnected()

    @staticmethod
    def _reason_failed(reason_code: Any) -> bool:
        if hasattr(reason_code, "is_failure"):
            return bool(reason_code.is_failure)
        try:
            return int(reason_code) != 0
        except (TypeError, ValueError):
            return str(reason_code).casefold() not in ("success", "0", "none")

    def _on_connect(self, client: Any, userdata: Any, flags: Any,
                    reason_code: Any, properties: Any = None) -> None:
        if self._reason_failed(reason_code):
            self._connected = False
            self._set_disconnected()
            self._last_errors["__connection__"] = f"MQTT connect rejected: {reason_code}"
            return
        self._connected = True
        self._last_errors.pop("__connection__", None)
        subscriptions = {}
        for binding in self.bindings:
            subscriptions[binding.topic] = max(subscriptions.get(binding.topic, 0), binding.qos)
        for topic, qos in subscriptions.items():
            result = client.subscribe(topic, qos=qos)
            if isinstance(result, tuple) and result and int(result[0]) != 0:
                self._last_errors[f"__subscribe__:{topic}"] = f"subscribe failed: {result}"
                self._failure_count += 1

    def _on_disconnect(self, client: Any, userdata: Any, disconnect_flags: Any = None,
                       reason_code: Any = None, properties: Any = None) -> None:
        self._connected = False
        if reason_code is not None and self._reason_failed(reason_code):
            self._last_errors["__connection__"] = f"MQTT disconnected: {reason_code}"
        self._set_disconnected()

    def _set_disconnected(self) -> None:
        from avic_core.domain.models import PointQuality
        for binding in self.bindings:
            try:
                self.point_runtime.mark_quality(
                    binding.point_id, PointQuality.BAD_COMMUNICATION,
                    source_driver_id=self.driver_instance_id)
            except Exception as exc:
                self._last_errors[binding.point_id] = f"{type(exc).__name__}: {exc}"

    @staticmethod
    def _extract(payload: bytes, binding: MqttPointBinding) -> Any:
        if len(payload) > _MAX_PAYLOAD_BYTES:
            raise ValueError("MQTT payload exceeds 1 MiB safety limit")
        if binding.payload_format == "raw":
            value: Any = payload.decode("utf-8")
        else:
            value = json.loads(payload.decode("utf-8"))
            for part in binding.value_path.split("."):
                if isinstance(value, dict) and part in value:
                    value = value[part]
                elif isinstance(value, list) and part.isdigit() and int(part) < len(value):
                    value = value[int(part)]
                else:
                    raise ValueError(f"JSON value_path not found: {binding.value_path}")
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = float(value) * float(binding.scale) + float(binding.offset)
            if not isfinite(value):
                raise ValueError("decoded/scaled MQTT value is not finite")
        elif binding.scale != 1.0 or binding.offset != 0.0:
            raise ValueError("scale/offset can only be applied to numeric MQTT values")
        return value

    def _on_message(self, client: Any, userdata: Any, message: Any) -> None:
        from datetime import datetime, timezone
        from avic_core.domain.models import PointQuality
        topic = str(message.topic)
        matched = [b for b in self.bindings if b.topic == topic]
        for binding in matched:
            try:
                value = self._extract(bytes(message.payload), binding)
                sample = self.point_runtime.publish(
                    binding.point_id, value, quality=PointQuality.GOOD,
                    timestamp=datetime.now(timezone.utc),
                    source_driver_id=self.driver_instance_id)
                self._last_errors.pop(binding.point_id, None)
                self._last_message_at[binding.point_id] = sample.timestamp.isoformat() if sample.timestamp else ""
                self._success_count += 1
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                self._last_errors[binding.point_id] = error
                self._failure_count += 1
                try:
                    self.point_runtime.mark_quality(
                        binding.point_id, PointQuality.BAD_CONFIGURATION,
                        source_driver_id=self.driver_instance_id)
                except Exception as quality_exc:
                    self._last_errors[binding.point_id] += (
                        f"; quality update failed: {type(quality_exc).__name__}: {quality_exc}")

    def diagnostics(self) -> dict:
        return {
            "driver_id": "mqtt", "mode": "READ_ONLY_SUBSCRIBE",
            "write_supported": False, "connected": self._connected,
            "started": self._started, "broker": f"{self.host}:{self.port}",
            "configured_points": len(self.bindings),
            "subscribed_topics": len({b.topic for b in self.bindings}),
            "success_count": self._success_count, "failure_count": self._failure_count,
            "last_message_at": dict(self._last_message_at),
            "last_errors": dict(self._last_errors),
        }
