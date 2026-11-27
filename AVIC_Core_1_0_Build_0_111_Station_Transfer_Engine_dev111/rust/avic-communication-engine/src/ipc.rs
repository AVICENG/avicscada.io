//! Versioned, bounded AVIC Driver IPC framing and envelope validation.
use serde::{Deserialize, Serialize};
use std::io::{Read, Write};
use uuid::Uuid;

pub const IPC_CONTRACT: &str = "avic.driver.ipc";
pub const IPC_VERSION: u16 = 1;
pub const MAX_FRAME_BYTES: usize = 1024 * 1024;

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct DriverEnvelope {
    pub contract: String,
    pub version: u16,
    pub message_id: Uuid,
    pub kind: String,
    pub installation_id: String,
    pub project_id: String,
    pub station_id: String,
    pub driver_instance_id: String,
    pub worker_id: Uuid,
    pub generation: u64,
    pub sequence: u64,
    pub sent_at: String,
    pub correlation_id: Option<Uuid>,
    pub payload: serde_json::Value,
}

#[derive(Debug, PartialEq)]
pub enum IpcError {
    Io(String),
    InvalidLength,
    FrameTooLarge(usize),
    InvalidJson(String),
    InvalidEnvelope(&'static str),
    StaleGeneration,
    NonMonotonicSequence,
}

impl std::fmt::Display for IpcError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(v) => write!(f, "IPC I/O: {v}"),
            Self::InvalidLength => write!(f, "IPC frame length is invalid"),
            Self::FrameTooLarge(v) => write!(f, "IPC frame exceeds limit: {v}"),
            Self::InvalidJson(v) => write!(f, "IPC JSON invalid: {v}"),
            Self::InvalidEnvelope(v) => write!(f, "IPC envelope invalid: {v}"),
            Self::StaleGeneration => write!(f, "IPC worker generation is stale"),
            Self::NonMonotonicSequence => write!(f, "IPC sequence is not increasing"),
        }
    }
}
impl std::error::Error for IpcError {}

impl DriverEnvelope {
    pub fn validate(&self) -> Result<(), IpcError> {
        if self.contract != IPC_CONTRACT { return Err(IpcError::InvalidEnvelope("unknown contract")); }
        if self.version != IPC_VERSION { return Err(IpcError::InvalidEnvelope("unsupported major version")); }
        if self.kind.is_empty() || self.kind.len() > 64 { return Err(IpcError::InvalidEnvelope("invalid message kind")); }
        for value in [&self.installation_id, &self.project_id, &self.station_id, &self.driver_instance_id] {
            if value.trim().is_empty() || value.len() > 128 {
                return Err(IpcError::InvalidEnvelope("invalid scope identity"));
            }
        }
        if self.generation == 0 { return Err(IpcError::InvalidEnvelope("generation must be positive")); }
        // Validate the calendar/time fields, not just the RFC3339 punctuation.
        // The wire contract deliberately requires the canonical UTC "Z" form.
        let timestamp_is_utc = self.sent_at.ends_with('Z')
            && chrono::DateTime::parse_from_rfc3339(&self.sent_at)
                .map(|parsed| parsed.offset().local_minus_utc() == 0)
                .unwrap_or(false);
        if !timestamp_is_utc {
            return Err(IpcError::InvalidEnvelope("sent_at must be a valid UTC RFC3339 timestamp"));
        }
        if !self.payload.is_object() { return Err(IpcError::InvalidEnvelope("payload must be an object")); }
        Ok(())
    }
}

/// Write one 4-byte big-endian length-prefixed JSON envelope.
pub fn write_frame<W: Write>(writer: &mut W, envelope: &DriverEnvelope) -> Result<(), IpcError> {
    envelope.validate()?;
    let body = serde_json::to_vec(envelope).map_err(|e| IpcError::InvalidJson(e.to_string()))?;
    if body.is_empty() { return Err(IpcError::InvalidLength); }
    if body.len() > MAX_FRAME_BYTES { return Err(IpcError::FrameTooLarge(body.len())); }
    writer.write_all(&(body.len() as u32).to_be_bytes()).map_err(|e| IpcError::Io(e.to_string()))?;
    writer.write_all(&body).map_err(|e| IpcError::Io(e.to_string()))?;
    writer.flush().map_err(|e| IpcError::Io(e.to_string()))
}

/// Read one frame. Returns None only when EOF occurs before any header byte.
pub fn read_frame<R: Read>(reader: &mut R) -> Result<Option<DriverEnvelope>, IpcError> {
    let mut header = [0u8; 4];
    let first = reader.read(&mut header[..1]).map_err(|e| IpcError::Io(e.to_string()))?;
    if first == 0 { return Ok(None); }
    reader.read_exact(&mut header[1..]).map_err(|e| IpcError::Io(e.to_string()))?;
    let length = u32::from_be_bytes(header) as usize;
    if length == 0 { return Err(IpcError::InvalidLength); }
    if length > MAX_FRAME_BYTES { return Err(IpcError::FrameTooLarge(length)); }
    let mut body = vec![0u8; length];
    reader.read_exact(&mut body).map_err(|e| IpcError::Io(e.to_string()))?;
    let envelope: DriverEnvelope = serde_json::from_slice(&body)
        .map_err(|e| IpcError::InvalidJson(e.to_string()))?;
    envelope.validate()?;
    Ok(Some(envelope))
}

/// Fences old worker processes and rejects duplicate/out-of-order events.
/// Gaps are reported to the caller so it can record diagnostics without
/// silently treating the stream as continuous.
#[derive(Debug, Default)]
pub struct SequenceGuard {
    generation: Option<u64>,
    last_sequence: Option<u64>,
}
impl SequenceGuard {
    pub fn accept(&mut self, generation: u64, sequence: u64) -> Result<bool, IpcError> {
        if generation == 0 { return Err(IpcError::StaleGeneration); }
        match self.generation {
            Some(current) if generation < current => return Err(IpcError::StaleGeneration),
            Some(current) if generation > current => {
                self.generation = Some(generation);
                self.last_sequence = Some(sequence);
                return Ok(false);
            }
            None => {
                self.generation = Some(generation);
                self.last_sequence = Some(sequence);
                return Ok(false);
            }
            _ => {}
        }
        if let Some(last) = self.last_sequence {
            if sequence <= last { return Err(IpcError::NonMonotonicSequence); }
            let gap = sequence > last.saturating_add(1);
            self.last_sequence = Some(sequence);
            return Ok(gap);
        }
        self.last_sequence = Some(sequence);
        Ok(false)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn envelope() -> DriverEnvelope {
        DriverEnvelope {
            contract: IPC_CONTRACT.into(), version: IPC_VERSION,
            message_id: Uuid::nil(), kind: "sample".into(),
            installation_id: "install-1".into(), project_id: "project-1".into(),
            station_id: "station-1".into(), driver_instance_id: "driver-1".into(),
            worker_id: Uuid::from_u128(1), generation: 1, sequence: 1,
            sent_at: "2026-11-27T10:00:00Z".into(), correlation_id: None,
            payload: serde_json::json!({"point_external_id":"p1","value":23.5,"quality":"GOOD"}),
        }
    }
    #[test] fn round_trip_frame() {
        let mut bytes = Vec::new(); write_frame(&mut bytes, &envelope()).unwrap();
        let decoded = read_frame(&mut bytes.as_slice()).unwrap().unwrap();
        assert_eq!(decoded, envelope());
    }
    #[test] fn rejects_non_utc_or_malformed_timestamp() {
        let mut e = envelope(); e.sent_at = "2026-11-27T10:00:00+03:00".into();
        assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))));
        let mut e = envelope(); e.sent_at = "2026-11-27T10:00:00+00:00".into();
        assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))));
        let mut e = envelope(); e.sent_at = "not-a-time".into();
        assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))));
    }
    #[test] fn rejects_impossible_calendar_and_clock_values() {
        for invalid in [
            "2026-13-27T10:00:00Z",
            "2026-02-30T10:00:00Z",
            "2026-11-27T25:00:00Z",
            "2026-11-27T10:61:00Z",
            "2026-11-27T10:00:61Z",
        ] {
            let mut e = envelope();
            e.sent_at = invalid.into();
            assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))), "{invalid}");
        }
    }
    #[test] fn accepts_valid_utc_rfc3339_fractional_seconds() {
        let mut e = envelope();
        e.sent_at = "2026-11-27T10:00:00.125Z".into();
        assert!(e.validate().is_ok());
    }
    #[test] fn rejects_bad_contract_and_generation() {
        let mut e = envelope(); e.contract = "other".into();
        assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))));
        let mut e = envelope(); e.generation = 0;
        assert!(matches!(e.validate(), Err(IpcError::InvalidEnvelope(_))));
    }
    #[test] fn rejects_oversized_frame_before_allocation() {
        let bytes = ((MAX_FRAME_BYTES as u32) + 1).to_be_bytes().to_vec();
        assert!(matches!(read_frame(&mut bytes.as_slice()), Err(IpcError::FrameTooLarge(_))));
    }
    #[test] fn sequence_guard_fences_old_worker_and_detects_gaps() {
        let mut g = SequenceGuard::default();
        assert!(!g.accept(4, 1).unwrap());
        assert!(g.accept(4, 3).unwrap());
        assert!(matches!(g.accept(4, 3), Err(IpcError::NonMonotonicSequence)));
        assert!(matches!(g.accept(3, 4), Err(IpcError::StaleGeneration)));
        assert!(!g.accept(5, 1).unwrap());
    }
}
