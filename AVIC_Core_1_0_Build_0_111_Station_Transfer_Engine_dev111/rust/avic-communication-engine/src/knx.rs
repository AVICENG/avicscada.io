//! Experimental read-only KNXnet/IP tunnelling adapter.
use knxide::dpt::{DptId, DptValue};
use knxide::{Client, GroupAddress, TunnelOptions};
use serde_json::{json, Value};
use std::net::SocketAddr;
use std::str::FromStr;
use std::time::Duration;
use tokio::runtime::{Builder, Runtime};

#[derive(Debug)]
pub enum KnxDriverError {
    Runtime(String),
    Connect(String),
    InvalidGroupAddress(String),
    InvalidDpt(String),
    Read(String),
}
impl std::fmt::Display for KnxDriverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Runtime(v) => write!(f, "KNX runtime: {v}"),
            Self::Connect(v) => write!(f, "KNX tunnel connect: {v}"),
            Self::InvalidGroupAddress(v) => write!(f, "invalid KNX group address: {v}"),
            Self::InvalidDpt(v) => write!(f, "invalid KNX DPT: {v}"),
            Self::Read(v) => write!(f, "KNX group read: {v}"),
        }
    }
}
impl std::error::Error for KnxDriverError {}

#[derive(Clone, Debug, PartialEq)]
pub struct KnxGroupSample {
    pub group_address: String,
    pub dpt: String,
    pub value: Value,
    pub display_value: String,
}

pub struct KnxIpReadOnlyClient {
    runtime: Runtime,
    client: Client,
}
impl KnxIpReadOnlyClient {
    pub fn connect(gateway: SocketAddr, local_bind: SocketAddr) -> Result<Self, KnxDriverError> {
        if gateway.port() == 0 { return Err(KnxDriverError::Connect("gateway port must be non-zero".into())); }
        let runtime = Builder::new_multi_thread().enable_all().build()
            .map_err(|e| KnxDriverError::Runtime(e.to_string()))?;
        let options = TunnelOptions { bind: local_bind, ..TunnelOptions::default() };
        let client = runtime.block_on(Client::connect(gateway, options))
            .map_err(|e| KnxDriverError::Connect(e.to_string()))?;
        Ok(Self { runtime, client })
    }

    /// Read a commissioned group address using its configured DPT.
    /// No GroupValue_Write or device restart operation is exposed here.
    pub fn read_group(
        &self, group_address: &str, dpt: &str, timeout: Duration,
    ) -> Result<KnxGroupSample, KnxDriverError> {
        if timeout.is_zero() { return Err(KnxDriverError::Read("timeout must be positive".into())); }
        let address = GroupAddress::from_str(group_address)
            .map_err(|_| KnxDriverError::InvalidGroupAddress(group_address.into()))?;
        let dpt_id = DptId::from_str(dpt)
            .map_err(|_| KnxDriverError::InvalidDpt(dpt.into()))?;
        let value = self.runtime.block_on(self.client.group_read_value(address, dpt_id, timeout))
            .map_err(|e| KnxDriverError::Read(e.to_string()))?;
        Ok(KnxGroupSample {
            group_address: address.to_string(),
            dpt: dpt.into(),
            value: dpt_value_to_json(&value),
            display_value: dpt_id.format(&value).to_string(),
        })
    }
}

fn dpt_value_to_json(value: &DptValue) -> Value {
    match value {
        DptValue::Bool(v) => json!(v),
        DptValue::Unsigned(v) => json!(v),
        DptValue::Signed(v) => json!(v),
        DptValue::Float(v) => if v.is_finite() { json!(v) } else { Value::Null },
        DptValue::String(v) => json!(v),
        other => json!(other.to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn group_address_parser_accepts_three_level_and_rejects_bad_input() {
        assert_eq!(GroupAddress::from_str("1/2/3").unwrap().to_string(), "1/2/3");
        assert!(GroupAddress::from_str("32/0/0").is_err());
        assert!(GroupAddress::from_str("1/x/3").is_err());
    }
    #[test]
    fn dpt_value_conversion_preserves_numeric_and_boolean_types() {
        assert_eq!(dpt_value_to_json(&DptValue::Bool(true)), json!(true));
        assert_eq!(dpt_value_to_json(&DptValue::Float(20.25)), json!(20.25));
        assert_eq!(dpt_value_to_json(&DptValue::Unsigned(5)), json!(5));
    }
}
