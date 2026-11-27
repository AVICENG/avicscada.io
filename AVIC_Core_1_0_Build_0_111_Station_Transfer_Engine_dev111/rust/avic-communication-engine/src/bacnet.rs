//! Experimental read-only BACnet/IP client adapter.
//! BACnet-RS upstream is actively developed and is not production-certified.
//! This module intentionally exposes discovery and property reads only.
use bacnet_rs::client::BacnetClient;
use bacnet_rs::object::PropertyValue;
use serde_json::{json, Value};
use std::net::SocketAddr;

#[derive(Clone, Debug, PartialEq)]
pub struct BacnetDeviceSnapshot {
    pub address: String,
    pub device_instance: u32,
    pub vendor_id: u16,
    pub vendor_name: String,
    pub max_apdu: u32,
    pub segmentation: String,
}

#[derive(Clone, Debug, PartialEq)]
pub struct BacnetPointSnapshot {
    pub object_identifier: String,
    pub object_type_name: String,
    pub object_instance: u32,
    pub object_name: Option<String>,
    pub description: Option<String>,
    pub present_value: Option<Value>,
    pub units: Option<String>,
    pub status_flags: Option<Vec<bool>>,
}

#[derive(Debug)]
pub enum BacnetDriverError {
    Stack(String),
    InvalidAddress,
}
impl std::fmt::Display for BacnetDriverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Stack(v) => write!(f, "BACnet stack: {v}"),
            Self::InvalidAddress => write!(f, "invalid BACnet/IP socket address"),
        }
    }
}
impl std::error::Error for BacnetDriverError {}

pub struct BacnetIpReadOnlyClient {
    client: BacnetClient,
}
impl BacnetIpReadOnlyClient {
    pub fn new() -> Result<Self, BacnetDriverError> {
        let client = BacnetClient::new().map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        Ok(Self { client })
    }

    pub fn discover(&self, address: SocketAddr) -> Result<BacnetDeviceSnapshot, BacnetDriverError> {
        if address.port() == 0 { return Err(BacnetDriverError::InvalidAddress); }
        let info = self.client.discover_device(address)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        Ok(BacnetDeviceSnapshot {
            address: info.address.to_string(),
            device_instance: info.device_id,
            vendor_id: info.vendor_id,
            vendor_name: info.vendor_name,
            max_apdu: info.max_apdu,
            segmentation: format!("{:?}", info.segmentation),
        })
    }

    /// Enumerate the device object list and read the stack's common object
    /// properties (including Present_Value where supported by the object).
    pub fn read_object_snapshots(
        &self, address: SocketAddr, device_instance: u32,
    ) -> Result<Vec<BacnetPointSnapshot>, BacnetDriverError> {
        let identifiers = self.client.read_object_list(address, device_instance)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        let objects = self.client.read_objects_properties(address, &identifiers)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        Ok(objects.into_iter().map(|item| BacnetPointSnapshot {
            object_identifier: format!("{:?}", item.object_identifier),
            object_type_name: format!("{:?}", item.object_identifier.object_type),
            object_instance: item.object_identifier.instance,
            object_name: item.object_name,
            description: item.description,
            present_value: item.present_value.as_ref().map(property_value_to_json),
            units: item.units,
            status_flags: item.status_flags,
        }).collect())
    }
}

fn property_value_to_json(value: &PropertyValue) -> Value {
    match value {
        PropertyValue::Null => Value::Null,
        PropertyValue::Boolean(v) => json!(v),
        PropertyValue::UnsignedInteger(v) | PropertyValue::Enumerated(v) => json!(v),
        PropertyValue::SignedInt(v) => json!(v),
        PropertyValue::Real(v) => if v.is_finite() { json!(v) } else { Value::Null },
        PropertyValue::Double(v) => if v.is_finite() { json!(v) } else { Value::Null },
        PropertyValue::CharacterString(v) => json!(v),
        PropertyValue::BitString(v) => json!(v),
        PropertyValue::OctetString(v) => json!(v),
        PropertyValue::ObjectIdentifier(v) => json!(format!("{:?}", v)),
        PropertyValue::Date(v) => json!(format!("{:?}", v)),
        PropertyValue::Time(v) => json!(format!("{:?}", v)),
        PropertyValue::Array(v) | PropertyValue::List(v) =>
            Value::Array(v.iter().map(property_value_to_json).collect()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bacnet_values_keep_numeric_and_boolean_types() {
        assert_eq!(property_value_to_json(&PropertyValue::Real(21.5)), json!(21.5));
        assert_eq!(property_value_to_json(&PropertyValue::Boolean(true)), json!(true));
        assert_eq!(property_value_to_json(&PropertyValue::UnsignedInteger(7)), json!(7));
        assert_eq!(property_value_to_json(&PropertyValue::Null), Value::Null);
    }
    #[test]
    fn bacnet_non_finite_values_never_become_json_numbers() {
        assert_eq!(property_value_to_json(&PropertyValue::Real(f32::NAN)), Value::Null);
        assert_eq!(property_value_to_json(&PropertyValue::Double(f64::INFINITY)), Value::Null);
    }
}
