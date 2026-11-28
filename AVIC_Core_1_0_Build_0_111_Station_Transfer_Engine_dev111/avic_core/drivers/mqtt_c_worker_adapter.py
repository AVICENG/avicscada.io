"""Event-driven Point Runtime adapter for the AVIC MQTT Paho C Worker.

The native worker owns MQTT networking and emits bounded AVIC IPC events. This
adapter owns topic-to-point routing, payload validation and Point Runtime writes.
"""
from __future__ import annotations

from datetime import datetime, timezone
from math import isfinite
import threading
from typing import Any

from avic_core.drivers.mqtt_adapter import MqttPointAdapter, MqttPointBinding, mqtt_topic_matches
from avic_core.drivers.rust_worker import RustDriverWorker


class MqttCWorkerPointAdapter:
    """Read-only MQTT event consumer; no MQTT publish/control API is exposed."""

    MAX_PAYLOAD_BYTES = 262_144

    def __init__(
        self, *, worker_command, core, driver_instance_id: str,
        config: dict[str, Any], bindings: list[MqttPointBinding],
        installation_id: str, project_id: str, station_id: str,
        generation: int = 1, timeout_seconds: float = 8.0,
    ) -> None:
        from avic_core.domain.models import PointQuality

        if not bindings:
            raise ValueError("MQTT C Worker requires at least one point binding")
        if len({item.point_id for item in bindings}) != len(bindings):
            raise ValueError("duplicate MQTT point_id binding")
        self.core = core
        self.point_runtime = core.point_runtime
        self.driver_instance_id = driver_instance_id
        self.bindings = tuple(bindings)
        self._by_topic: dict[str, list[MqttPointBinding]] = {}
        for binding in self.bindings:
            self._by_topic.setdefault(binding.topic, []).append(binding)
        self._PointQuality = PointQuality
        self._worker_config = {
            "protocol": "mqtt",
            "host": str(config["host"]),
            "port": int(config.get("port", 8883 if config.get("tls_ca_certs") else 1883)),
            "keepalive": int(config.get("keepalive", 60)),
            "client_id": str(config.get("client_id") or f"avic-{driver_instance_id[:12]}"),
            "mqtt_version": str(config.get("protocol", "3.1.1")),
            "tls_ca_file": str(config["tls_ca_certs"]) if config.get("tls_ca_certs") else None,
            "bindings": [
                {
                    "point_id": item.point_id, "topic": item.topic, "qos": item.qos,
                    "payload_format": item.payload_format, "value_path": item.value_path,
                    "scale": item.scale, "offset": item.offset,
                }
                for item in self.bindings
            ],
        }
        self._worker = RustDriverWorker(
            worker_command, installation_id=installation_id, project_id=project_id,
            station_id=station_id, driver_instance_id=driver_instance_id,
            generation=generation, timeout_seconds=timeout_seconds,
        )
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()
        self._started = False
        self._connected = False
        self._success_count = 0
        self._failure_count = 0
        self._unknown_topic_count = 0
        self._last_errors: dict[str, str] = {}
        self._last_message_at: dict[str, str] = {}

    def start(self) -> None:
        with self._lock:
            if self._started:
                return
            self._worker.start(self._worker_config)
            self._stop.clear()
            self._thread = threading.Thread(
                target=self._consume_events, name=f"avic-mqtt-c-{self.driver_instance_id[:8]}",
                daemon=True,
            )
            self._thread.start()
            self._started = True

    @staticmethod
    def _parse_timestamp(value: Any) -> datetime:
        if not isinstance(value, str) or not value.endswith("Z"):
            raise ValueError("MQTT event timestamp must be UTC RFC3339")
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
        if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
            raise ValueError("MQTT event timestamp must be UTC")
        return parsed

    @staticmethod
    def _extract(payload: bytes, binding: MqttPointBinding) -> Any:
        if len(payload) > MqttCWorkerPointAdapter.MAX_PAYLOAD_BYTES:
            raise ValueError("MQTT payload exceeds 256 KiB safety limit")
        return MqttPointAdapter._extract(payload, binding)

    def _mark_all(self, quality, reason: str) -> None:
        for binding in self.bindings:
            try:
                self.point_runtime.mark_quality(
                    binding.point_id, quality, source_driver_id=self.driver_instance_id,
                )
            except Exception as exc:
                self._last_errors[binding.point_id] = (
                    f"{reason}; quality update failed: {type(exc).__name__}: {exc}"
                )

    def _consume_sample(self, payload: dict[str, Any]) -> None:
        topic = payload.get("topic")
        bindings = [item for item in self.bindings
                    if isinstance(topic, str) and mqtt_topic_matches(item.topic, topic)]
        if not bindings:
            self._unknown_topic_count += 1
            return
        body = payload.get("payload")
        if not isinstance(body, str):
            raise ValueError("MQTT IPC sample payload must be UTF-8 text")
        raw = body.encode("utf-8")
        if len(raw) > self.MAX_PAYLOAD_BYTES:
            raise ValueError("MQTT payload exceeds 256 KiB safety limit")
        timestamp = self._parse_timestamp(payload.get("received_at"))
        qos = payload.get("qos")
        if isinstance(qos, bool) or qos not in (0, 1, 2):
            raise ValueError("MQTT IPC sample has invalid QoS")
        for binding in bindings:
            try:
                value = self._extract(raw, binding)
                sample = self.point_runtime.publish(
                    binding.point_id, value, quality=self._PointQuality.GOOD,
                    timestamp=timestamp, source_driver_id=self.driver_instance_id,
                )
                self._last_errors.pop(binding.point_id, None)
                self._last_message_at[binding.point_id] = (
                    sample.timestamp.isoformat() if sample.timestamp else timestamp.isoformat()
                )
                self._success_count += 1
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                self._last_errors[binding.point_id] = error
                self._failure_count += 1
                try:
                    self.point_runtime.mark_quality(
                        binding.point_id, self._PointQuality.BAD_CONFIGURATION,
                        source_driver_id=self.driver_instance_id,
                    )
                except Exception:
                    pass

    def _consume_events(self) -> None:
        while not self._stop.is_set():
            try:
                event = self._worker.next_event(timeout_seconds=0.25)
            except Exception as exc:
                self._last_errors["__worker__"] = f"{type(exc).__name__}: {exc}"
                self._failure_count += 1
                self._connected = False
                self._mark_all(self._PointQuality.BAD_COMMUNICATION, self._last_errors["__worker__"])
                return
            if event is None:
                continue
            try:
                if event.kind == "status":
                    connected = event.payload.get("connected")
                    if isinstance(connected, bool):
                        self._connected = connected
                        if not connected:
                            self._mark_all(self._PointQuality.BAD_COMMUNICATION, "MQTT broker disconnected")
                    continue
                if event.kind == "fault":
                    detail = str(event.payload.get("message") or "MQTT C Worker fault")
                    self._last_errors["__worker__"] = detail[:512]
                    self._connected = False
                    self._failure_count += 1
                    self._mark_all(self._PointQuality.BAD_COMMUNICATION, detail)
                    continue
                if event.kind != "sample":
                    continue
                self._consume_sample(event.payload)
            except Exception as exc:
                self._failure_count += 1
                self._last_errors["__event__"] = f"{type(exc).__name__}: {exc}"

    def stop(self) -> None:
        with self._lock:
            if not self._started:
                return
            self._stop.set()
            thread = self._thread
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=2.0)
            if thread.is_alive():
                raise TimeoutError("MQTT C Worker event consumer did not stop")
        self._worker.close()
        self._mark_all(self._PointQuality.STALE, "MQTT driver stopped")
        with self._lock:
            self._thread = None
            self._started = False
            self._connected = False

    def close(self) -> None:
        self.stop()

    def diagnostics(self) -> dict:
        return {
            "driver_id": "mqtt", "mode": "C_PAHO_READ_ONLY_EVENT_WORKER",
            "write_supported": False, "connected": self._connected,
            "started": self._started, "broker": f"{self._worker_config['host']}:{self._worker_config['port']}",
            "configured_points": len(self.bindings), "subscribed_topics": len(self._by_topic),
            "success_count": self._success_count, "failure_count": self._failure_count,
            "unknown_topic_count": self._unknown_topic_count,
            "last_message_at": dict(self._last_message_at),
            "last_errors": dict(self._last_errors), "worker": self._worker.diagnostics(),
        }
