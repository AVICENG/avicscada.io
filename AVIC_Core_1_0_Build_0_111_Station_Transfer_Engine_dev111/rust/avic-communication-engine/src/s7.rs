//! Siemens S7comm read-only adapter over ISO-on-TCP (TCP/102).
//! This legacy S7comm path is not equivalent to secure S7CommPlus/TLS.
use std::time::Duration;
use tokio::runtime::{Builder, Runtime};
use tokio_s7::client::{S7Client, S7Config};
use tokio_s7::types::PlcType;

#[derive(Debug)]
pub enum S7DriverError { InvalidConfig(&'static str), Runtime(String), Connect(String), Read(String) }
impl std::fmt::Display for S7DriverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::InvalidConfig(v) => write!(f, "invalid S7 configuration: {v}"),
            Self::Runtime(v) => write!(f, "S7 runtime: {v}"),
            Self::Connect(v) => write!(f, "S7 connect: {v}"),
            Self::Read(v) => write!(f, "S7 read: {v}"),
        }
    }
}
impl std::error::Error for S7DriverError {}

pub fn parse_plc_type(value: &str) -> Result<PlcType, S7DriverError> {
    match value.to_ascii_lowercase().as_str() {
        "s200" => Ok(PlcType::S200),
        "s200smart" | "s200-smart" => Ok(PlcType::S200Smart),
        "s300" | "s7-300" => Ok(PlcType::S300),
        "s400" | "s7-400" => Ok(PlcType::S400),
        "s1200" | "s7-1200" => Ok(PlcType::S1200),
        "s1500" | "s7-1500" => Ok(PlcType::S1500),
        _ => Err(S7DriverError::InvalidConfig("unsupported PLC family")),
    }
}

pub fn validate_db_read(db_number: u16, offset: u16, count: u16) -> Result<String, S7DriverError> {
    if db_number == 0 || count == 0 || count > 200
        || (offset as u32 + count as u32) > 65536 {
        return Err(S7DriverError::InvalidConfig("DB number, offset or read length out of range"));
    }
    Ok(format!("DB{db_number}.{offset}"))
}

pub struct S7IpReadOnlyClient { runtime: Runtime, client: S7Client }
impl S7IpReadOnlyClient {
    pub fn connect(host: &str, port: u16, plc_type: &str, rack: u8, slot: u8,
                   timeout_ms: u64) -> Result<Self, S7DriverError> {
        if host.trim().is_empty() || port == 0 || !(100..=30000).contains(&timeout_ms) {
            return Err(S7DriverError::InvalidConfig("host, port or timeout out of range"));
        }
        let plc = parse_plc_type(plc_type)?;
        let runtime = Builder::new_multi_thread().enable_all().build()
            .map_err(|e| S7DriverError::Runtime(e.to_string()))?;
        let config = S7Config::new(host).with_port(port).with_plc_type(plc)
            .with_rack_slot(rack, slot).with_timeout(timeout_ms).with_auto_reconnect(true);
        let mut client = S7Client::new(config);
        runtime.block_on(client.connect()).map_err(|e| S7DriverError::Connect(e.to_string()))?;
        Ok(Self { runtime, client })
    }

    /// Read a bounded byte range from a standard (non-optimized) DB.
    pub fn read_db_bytes(&mut self, db_number: u16, offset: u16, count: u16)
        -> Result<Vec<u8>, S7DriverError> {
        let address = validate_db_read(db_number, offset, count)?;
        self.runtime.block_on(self.client.read_bytes(&address, count))
            .map_err(|e| S7DriverError::Read(e.to_string()))
    }
}
impl Drop for S7IpReadOnlyClient {
    fn drop(&mut self) { let _ = self.runtime.block_on(self.client.disconnect()); }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test] fn parses_supported_cpu_families() {
        assert!(matches!(parse_plc_type("S7-300"), Ok(PlcType::S300)));
        assert!(matches!(parse_plc_type("S7-1500"), Ok(PlcType::S1500)));
        assert!(matches!(parse_plc_type("S7-1200"), Ok(PlcType::S1200)));
        assert!(parse_plc_type("S7-999").is_err());
    }
    #[test] fn validates_absolute_db_byte_address_and_bounds() {
        assert_eq!(validate_db_read(1, 0, 4).unwrap(), "DB1.0");
        assert_eq!(validate_db_read(10, 100, 20).unwrap(), "DB10.100");
        assert!(validate_db_read(0, 0, 4).is_err());
        assert!(validate_db_read(1, 0, 0).is_err());
        assert!(validate_db_read(1, 0, 201).is_err());
        assert!(validate_db_read(1, 65535, 2).is_err());
    }
}
