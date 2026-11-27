//! Experimental read-only BACnet/IP client adapter.
//! BACnet-RS upstream is actively developed and is not production-certified.
//! This module intentionally exposes discovery and property reads only.
use bacnet_rs::client::BacnetClient;
use bacnet_rs::property::PropertyValue;
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
    pub route: Option<String>,
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
    DeviceInstanceMismatch,
}
impl std::fmt::Display for BacnetDriverError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Stack(v) => write!(f, "BACnet stack: {v}"),
            Self::InvalidAddress => write!(f, "invalid BACnet/IP socket address"),
            Self::DeviceInstanceMismatch => write!(f, "BACnet Device Instance mismatch"),
        }
    }
}
impl std::error::Error for BacnetDriverError {}

pub struct BacnetIpReadOnlyClient {
    client: BacnetClient,
}
impl BacnetIpReadOnlyClient {
    pub fn new(local_bind: SocketAddr) -> Result<Self, BacnetDriverError> {
        if local_bind.port() == 0 { return Err(BacnetDriverError::InvalidAddress); }
        let client = BacnetClient::new_with_local_addr(local_bind).map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
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
            route: info.route.map(|v| format!("{:?}", v)),
        })
    }

    /// Discover a device and read its object list using the target returned by I-Am.
    /// This preserves routed BACnet destination network/address metadata.
    pub fn read_device_snapshot(
        &self, address: SocketAddr, device_instance: u32,
    ) -> Result<(BacnetDeviceSnapshot, Vec<BacnetPointSnapshot>), BacnetDriverError> {
        if address.port() == 0 { return Err(BacnetDriverError::InvalidAddress); }
        let info = self.client.discover_device(address)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        if info.device_id != device_instance {
            return Err(BacnetDriverError::DeviceInstanceMismatch);
        }
        let identifiers = self.client.read_object_list(info.target(), device_instance)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        let objects = self.client.read_objects_properties(info.target(), &identifiers)
            .map_err(|e| BacnetDriverError::Stack(e.to_string()))?;
        let device = BacnetDeviceSnapshot {
            address: info.address.to_string(),
            device_instance: info.device_id,
            vendor_id: info.vendor_id,
            vendor_name: info.vendor_name,
            max_apdu: info.max_apdu,
            segmentation: format!("{:?}", info.segmentation),
            route: info.route.map(|v| format!("{:?}", v)),
        };
        let snapshots = objects.into_iter().map(|item| BacnetPointSnapshot {
            object_identifier: format!("{:?}", item.object_identifier),
            object_type_name: format!("{:?}", item.object_identifier.object_type),
            object_instance: item.object_identifier.instance,
            object_name: item.object_name,
            description: item.description,
            present_value: item.present_value.as_ref().map(property_value_to_json),
            units: item.units.map(|v| format!("{:?}", v)),
            status_flags: item.status_flags,
        }).collect();
        Ok((device, snapshots))
    }

    pub fn read_object_snapshots(
        &self, address: SocketAddr, device_instance: u32,
    ) -> Result<Vec<BacnetPointSnapshot>, BacnetDriverError> {
        self.read_device_snapshot(address, device_instance).map(|(_, objects)| objects)
    }
}

fn property_value_to_json(value: &PropertyValue) -> Value {
    match value {
        PropertyValue::Null => Value::Null,
        PropertyValue::Boolean(v) => json!(v),
        PropertyValue::Unsigned(v) | PropertyValue::Enumerated(v) => json!(v),
        PropertyValue::Signed(v) => json!(v),
        PropertyValue::Real(v) => if v.is_finite() { json!(v) } else { Value::Null },
        PropertyValue::Double(v) => if v.is_finite() { json!(v) } else { Value::Null },
        PropertyValue::CharacterString(v) => json!(v),
        PropertyValue::BitString(v) => json!(v),
        PropertyValue::OctetString(v) => json!(v),
        PropertyValue::ObjectIdentifier(v) => json!(format!("{:?}", v)),
        PropertyValue::Date(year, month, day, weekday) => json!({"year":year,"month":month,"day":day,"weekday":weekday}),
        PropertyValue::Time(hour, minute, second, hundredths) => json!({"hour":hour,"minute":minute,"second":second,"hundredths":hundredths}),
        PropertyValue::Unknown(v) => json!(v),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn bacnet_values_keep_numeric_and_boolean_types() {
        assert_eq!(property_value_to_json(&PropertyValue::Real(21.5)), json!(21.5));
        assert_eq!(property_value_to_json(&PropertyValue::Boolean(true)), json!(true));
        assert_eq!(property_value_to_json(&PropertyValue::Unsigned(7)), json!(7));
        assert_eq!(property_value_to_json(&PropertyValue::Null), Value::Null);
    }
    #[test]
    fn bacnet_non_finite_values_never_become_json_numbers() {
        assert_eq!(property_value_to_json(&PropertyValue::Real(f32::NAN)), Value::Null);
        assert_eq!(property_value_to_json(&PropertyValue::Double(f64::INFINITY)), Value::Null);
    }
}
