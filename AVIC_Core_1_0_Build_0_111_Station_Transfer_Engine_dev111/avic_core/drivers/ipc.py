"""AVIC Driver IPC v1 framing and envelope validation (Python reference codec).

The supervisor remains the trust boundary: a valid frame is not permission to
publish a point. Station ownership, driver generation, RBAC, licensing, quality
and point binding must still be checked by Core before Point Runtime publication.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
import struct
import uuid
from typing import BinaryIO, Any

IPC_CONTRACT = "avic.driver.ipc"
IPC_VERSION = 1
MAX_FRAME_BYTES = 1024 * 1024


class DriverIpcError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DriverEnvelope:
    contract: str
    version: int
    message_id: str
    kind: str
    installation_id: str
    project_id: str
    station_id: str
    driver_instance_id: str
    worker_id: str
    generation: int
    sequence: int
    sent_at: str
    correlation_id: str | None
    payload: dict[str, Any]

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "DriverEnvelope":
        expected = {
            "contract", "version", "message_id", "kind", "installation_id",
            "project_id", "station_id", "driver_instance_id", "worker_id",
            "generation", "sequence", "sent_at", "correlation_id", "payload",
        }
        if set(raw) != expected:
            raise DriverIpcError("IPC envelope fields do not match v1 schema")
        item = cls(**raw)
        item.validate()
        return item

    def validate(self) -> None:
        if self.contract != IPC_CONTRACT or isinstance(self.version, bool) or self.version != IPC_VERSION:
            raise DriverIpcError("unsupported IPC contract/version")
        if not isinstance(self.kind, str) or not self.kind or len(self.kind) > 64:
            raise DriverIpcError("invalid message kind")
        for value in (self.installation_id, self.project_id, self.station_id, self.driver_instance_id):
            if not isinstance(value, str) or not value.strip() or len(value) > 128:
                raise DriverIpcError("invalid scope identity")
        try:
            uuid.UUID(self.message_id)
            uuid.UUID(self.worker_id)
            if self.correlation_id is not None:
                uuid.UUID(self.correlation_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise DriverIpcError("invalid message/worker/correlation UUID") from exc
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation <= 0:
            raise DriverIpcError("generation must be positive")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise DriverIpcError("sequence must be non-negative")
        if not isinstance(self.sent_at, str):
            raise DriverIpcError("sent_at must be UTC RFC3339")
        try:
            parsed = datetime.fromisoformat(self.sent_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise DriverIpcError("sent_at must be UTC RFC3339") from exc
        if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0 or not self.sent_at.endswith("Z"):
            raise DriverIpcError("sent_at must be UTC RFC3339")
        if not isinstance(self.payload, dict):
            raise DriverIpcError("payload must be an object")


def encode_frame(envelope: DriverEnvelope) -> bytes:
    envelope.validate()
    body = json.dumps(
        {name: getattr(envelope, name) for name in envelope.__dataclass_fields__},
        separators=(",", ":"), ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")
    if not body or len(body) > MAX_FRAME_BYTES:
        raise DriverIpcError("IPC frame length out of bounds")
    return struct.pack(">I", len(body)) + body


def _read_exact(stream: BinaryIO, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = stream.read(size - len(chunks))
        if not chunk:
            break
        chunks.extend(chunk)
    return bytes(chunks)


def read_frame(stream: BinaryIO) -> DriverEnvelope | None:
    header = _read_exact(stream, 4)
    if header == b"":
        return None
    if len(header) != 4:
        raise DriverIpcError("truncated IPC frame header")
    (length,) = struct.unpack(">I", header)
    if length == 0 or length > MAX_FRAME_BYTES:
        raise DriverIpcError("IPC frame length out of bounds")
    body = _read_exact(stream, length)
    if len(body) != length:
        raise DriverIpcError("truncated IPC frame body")
    try:
        raw = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DriverIpcError("invalid IPC JSON") from exc
    if not isinstance(raw, dict):
        raise DriverIpcError("IPC envelope must be an object")
    return DriverEnvelope.from_mapping(raw)


class SequenceGuard:
    """Reject stale generations and duplicate/out-of-order events; report gaps."""
    def __init__(self) -> None:
        self.generation: int | None = None
        self.last_sequence: int | None = None

    def accept(self, generation: int, sequence: int) -> bool:
        if generation <= 0 or sequence < 0:
            raise DriverIpcError("invalid generation or sequence")
        if self.generation is not None and generation < self.generation:
            raise DriverIpcError("stale worker generation")
        if self.generation is None or generation > self.generation:
            self.generation, self.last_sequence = generation, sequence
            return False
        assert self.last_sequence is not None
        if sequence <= self.last_sequence:
            raise DriverIpcError("non-monotonic IPC sequence")
        gap = sequence > self.last_sequence + 1
        self.last_sequence = sequence
        return gap
