from __future__ import annotations

import io
import json
import struct
import uuid

import pytest

from avic_core.drivers.ipc import (
    DriverEnvelope, DriverIpcError, SequenceGuard, encode_frame, read_frame, write_frame,
    MAX_FRAME_BYTES,
)


def envelope(**changes):
    values = dict(
        contract="avic.driver.ipc", version=1, message_id=str(uuid.uuid4()),
        kind="sample", installation_id="install-1", project_id="project-1",
        station_id="station-1", driver_instance_id="driver-1",
        worker_id=str(uuid.uuid4()), generation=1, sequence=1,
        sent_at="2026-11-27T10:00:00Z", correlation_id=None,
        payload={"point_external_id": "p1", "value": 23.5, "quality": "GOOD"},
    )
    values.update(changes)
    return DriverEnvelope(**values)


def test_round_trip_length_prefixed_json():
    original = envelope()
    assert read_frame(io.BytesIO(encode_frame(original))) == original


def test_clean_eof_and_truncated_header():
    assert read_frame(io.BytesIO(b"")) is None
    with pytest.raises(DriverIpcError, match="header"):
        read_frame(io.BytesIO(b"\x00\x00"))


def test_rejects_truncated_body_and_oversized_length():
    with pytest.raises(DriverIpcError, match="body"):
        read_frame(io.BytesIO(struct.pack(">I", 10) + b"{}"))
    with pytest.raises(DriverIpcError, match="length"):
        read_frame(io.BytesIO(struct.pack(">I", MAX_FRAME_BYTES + 1)))


def test_rejects_unknown_contract_and_non_utc_timestamp():
    with pytest.raises(DriverIpcError, match="contract"):
        encode_frame(envelope(contract="other"))
    with pytest.raises(DriverIpcError, match="UTC"):
        encode_frame(envelope(sent_at="2026-11-27T10:00:00+03:00"))


def test_rejects_unknown_or_missing_envelope_fields():
    raw = {name: getattr(envelope(), name) for name in envelope().__dataclass_fields__}
    raw["unexpected"] = True
    with pytest.raises(DriverIpcError, match="fields"):
        DriverEnvelope.from_mapping(raw)


def test_sequence_guard_fences_generations_and_reports_gaps():
    guard = SequenceGuard()
    assert guard.accept(4, 1) is False
    assert guard.accept(4, 3) is True
    with pytest.raises(DriverIpcError, match="non-monotonic"):
        guard.accept(4, 3)
    with pytest.raises(DriverIpcError, match="stale"):
        guard.accept(3, 4)
    assert guard.accept(5, 1) is False


def test_write_frame_matches_encode_frame():
    import io
    item = DriverEnvelope(
        contract="avic.driver.ipc", version=1, message_id=str(uuid.uuid4()),
        kind="sample", installation_id="install-1", project_id="project-1",
        station_id="station-1", driver_instance_id="driver-1",
        worker_id=str(uuid.uuid4()), generation=1, sequence=1,
        sent_at="2026-11-27T10:00:00Z", correlation_id=None, payload={"value": 1},
    )
    stream = io.BytesIO()
    write_frame(stream, item)
    assert stream.getvalue() == encode_frame(item)
