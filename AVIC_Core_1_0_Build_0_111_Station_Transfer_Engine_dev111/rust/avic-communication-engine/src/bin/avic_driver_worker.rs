use avic_communication_engine::ipc::{
    read_frame, write_frame, DriverEnvelope, SequenceGuard, IPC_CONTRACT, IPC_VERSION,
};
use avic_communication_engine::{
    bacnet::BacnetIpReadOnlyClient,
    knx::KnxIpReadOnlyClient,
    s7::S7IpReadOnlyClient,
    ModbusTcpClient, ModbusTcpConfig,
};
use chrono::{SecondsFormat, Utc};
use serde_json::{json, Value};
use std::collections::HashMap;
use std::io::{stdin, stdout, BufReader, BufWriter};
use std::net::SocketAddr;
use std::time::Duration;
use uuid::Uuid;

#[derive(Clone)]
struct Scope {
    installation_id: String,
    project_id: String,
    station_id: String,
    driver_instance_id: String,
    worker_id: Uuid,
    generation: u64,
}

struct Worker {
    scope: Option<Scope>,
    incoming: SequenceGuard,
    outgoing_sequence: u64,
    sequence_gaps: u64,
    configured: bool,
    protocol: Option<String>,
    started: bool,
    // Session key includes endpoint, Unit ID and timeout. Sessions are owned by
    // this isolated DriverInstance worker and reused across point reads.
    modbus_clients: HashMap<String, ModbusTcpClient>,
    s7_clients: HashMap<String, S7IpReadOnlyClient>,
}

impl Worker {
    fn new() -> Self {
        Self { scope: None, incoming: SequenceGuard::default(), outgoing_sequence: 0,
               sequence_gaps: 0, configured: false, protocol: None, started: false,
               modbus_clients: HashMap::new(), s7_clients: HashMap::new() }
    }

    fn handle(&mut self, request: DriverEnvelope) -> (String, Value, bool) {
        if let Err(e) = request.validate() {
            return ("error".into(), json!({"code":"INVALID_ENVELOPE","message":e.to_string()}), false);
        }
        if let Some(scope) = &self.scope {
            if request.installation_id != scope.installation_id
                || request.project_id != scope.project_id
                || request.station_id != scope.station_id
                || request.driver_instance_id != scope.driver_instance_id
                || request.worker_id != scope.worker_id
                || request.generation != scope.generation {
                return ("error".into(), json!({"code":"SCOPE_MISMATCH"}), false);
            }
        } else {
            if request.kind != "initialize" {
                return ("error".into(), json!({"code":"INITIALIZE_REQUIRED"}), false);
            }
            self.scope = Some(Scope {
                installation_id: request.installation_id.clone(),
                project_id: request.project_id.clone(),
                station_id: request.station_id.clone(),
                driver_instance_id: request.driver_instance_id.clone(),
                worker_id: request.worker_id,
                generation: request.generation,
            });
        }
        match self.incoming.accept(request.generation, request.sequence) {
            Ok(gap) => { if gap { self.sequence_gaps = self.sequence_gaps.saturating_add(1); } },
            Err(e) => return ("error".into(), json!({"code":"SEQUENCE_REJECTED","message":e.to_string()}), false),
        }

        match request.kind.as_str() {
            "initialize" => ("initialized".into(), json!({"protocol":"avic.driver.ipc","version":1,"worker_version":env!("CARGO_PKG_VERSION")}), false),
            "configure" => {
                if self.started {
                    return ("error".into(), json!({"code":"STOP_REQUIRED_BEFORE_CONFIGURE"}), false);
                }
                if contains_secret_key(&request.payload) {
                    return ("error".into(), json!({"code":"SECRET_IN_CONFIG"}), false);
                }
                let protocol = match request.payload.get("protocol").and_then(Value::as_str) {
                    Some(v) if ["modbus-tcp", "bacnet-ip", "knxnet-ip", "s7comm"].contains(&v) => v.to_string(),
                    _ => return ("error".into(), json!({"code":"UNSUPPORTED_PROTOCOL"}), false),
                };
                self.protocol = Some(protocol.clone());
                self.configured = true;
                ("configured".into(), json!({"configured":true,"protocol":protocol}), false)
            }
            "start" => {
                if !self.configured { return ("error".into(), json!({"code":"CONFIGURE_REQUIRED"}), false); }
                self.started = true;
                ("status".into(), json!({"state":"RUNNING","write_supported":false}), false)
            }
            "stop" => {
                self.started = false;
                self.modbus_clients.clear();
                self.s7_clients.clear();
                ("status".into(), json!({"state":"STOPPED","write_supported":false}), false)
            }
            "get_status" => ("status".into(), json!({
                "state": if self.started {"RUNNING"} else {"STOPPED"},
                "configured":self.configured, "protocol":self.protocol, "sequence_gaps":self.sequence_gaps, "write_supported":false
            }), false),
            "read" => {
                if !self.started { return ("error".into(), json!({"code":"DRIVER_NOT_RUNNING"}), false); }
                if contains_secret_key(&request.payload) {
                    return ("error".into(), json!({"code":"SECRET_IN_REQUEST"}), false);
                }
                let requested_protocol = request.payload.get("protocol").and_then(Value::as_str);
                if requested_protocol != self.protocol.as_deref() {
                    return ("error".into(), json!({"code":"PROTOCOL_SCOPE_MISMATCH"}), false);
                }
                match read_protocol(&request.payload, &mut self.modbus_clients, &mut self.s7_clients) {
                    Ok(value) => ("read_result".into(), json!({"transport_ok":true,"result":value}), false),
                    Err(message) => ("read_error".into(), json!({"transport_ok":false,"message":message}), false),
                }
            }
            "write" | "write_point" => ("error".into(), json!({"code":"WRITE_DISABLED"}), false),
            "shutdown" => {
                self.started = false;
                self.modbus_clients.clear();
                ("status".into(), json!({"state":"STOPPED","shutdown":true}), true)
            }
            _ => ("error".into(), json!({"code":"UNSUPPORTED_COMMAND"}), false),
        }
    }

    fn response(&mut self, request: &DriverEnvelope, kind: String, payload: Value) -> DriverEnvelope {
        self.outgoing_sequence += 1;
        let scope = self.scope.as_ref().expect("scope initialized");
        DriverEnvelope {
            contract: IPC_CONTRACT.into(), version: IPC_VERSION,
            message_id: Uuid::new_v4(), kind,
            installation_id: scope.installation_id.clone(),
            project_id: scope.project_id.clone(),
            station_id: scope.station_id.clone(),
            driver_instance_id: scope.driver_instance_id.clone(),
            worker_id: scope.worker_id, generation: scope.generation,
            sequence: self.outgoing_sequence,
            sent_at: Utc::now().to_rfc3339_opts(SecondsFormat::Millis, true),
            correlation_id: Some(request.message_id), payload,
        }
    }
}

fn contains_secret_key(value: &Value) -> bool {
    match value {
        Value::Object(map) => map.iter().any(|(key, child)| {
            let normalized: String = key.chars().filter(|c| c.is_ascii_alphanumeric())
                .flat_map(char::to_lowercase).collect();
            let secret = ["password","passwd","secret","token","privatekey","credential",
                "credentials","apikey","accesstoken","refreshtoken","authorization",
                "bearer","tlskey","clientsecret","clientkey"]
                .iter().any(|needle| normalized == *needle || normalized.ends_with(needle));
            secret || contains_secret_key(child)
        }),
        Value::Array(items) => items.iter().any(contains_secret_key),
        _ => false,
    }
}

fn required_str<'a>(p: &'a Value, key: &str) -> Result<&'a str, String> {
    p.get(key).and_then(Value::as_str).filter(|s| !s.trim().is_empty())
        .ok_or_else(|| format!("missing/invalid {key}"))
}
fn required_u64(p: &Value, key: &str) -> Result<u64, String> {
    p.get(key).and_then(Value::as_u64).ok_or_else(|| format!("missing/invalid {key}"))
}

fn read_protocol(p: &Value, modbus_clients: &mut HashMap<String, ModbusTcpClient>, s7_clients: &mut HashMap<String, S7IpReadOnlyClient>) -> Result<Value, String> {
    match required_str(p, "protocol")? {
        "modbus-tcp" => {
            let host = required_str(p, "host")?;
            let port = u16::try_from(required_u64(p, "port")?).map_err(|_| "invalid port".to_string())?;
            let unit_id = u8::try_from(required_u64(p, "unit_id")?).map_err(|_| "invalid unit_id".to_string())?;
            let function = u8::try_from(required_u64(p, "function")?).map_err(|_| "invalid function".to_string())?;
            let address = u16::try_from(required_u64(p, "address")?).map_err(|_| "invalid address".to_string())?;
            let count = u16::try_from(required_u64(p, "count")?).map_err(|_| "invalid count".to_string())?;
            let timeout_ms = p.get("timeout_ms").and_then(Value::as_u64).unwrap_or(2000);
            if !(100..=10000).contains(&timeout_ms) { return Err("Modbus timeout_ms must be 100..10000".into()); }
            let session_key = format!("{host}:{port}/{unit_id}/{timeout_ms}");
            if !modbus_clients.contains_key(&session_key) {
                let config = ModbusTcpConfig::new(host, port, unit_id, Duration::from_millis(timeout_ms))
                    .map_err(|e| e.to_string())?;
                modbus_clients.insert(session_key.clone(), ModbusTcpClient::new(config));
            }
            let client = modbus_clients.get_mut(&session_key).expect("session inserted");
            match function {
                1 => Ok(json!({"function":1,"values":client.read_coils(address,count).map_err(|e|e.to_string())?})),
                2 => Ok(json!({"function":2,"values":client.read_discrete_inputs(address,count).map_err(|e|e.to_string())?})),
                3 => Ok(json!({"function":3,"values":client.read_holding_registers(address,count).map_err(|e|e.to_string())?})),
                4 => Ok(json!({"function":4,"values":client.read_input_registers(address,count).map_err(|e|e.to_string())?})),
                _ => Err("only Modbus FC01/02/03/04 reads are enabled".into()),
            }
        }
        "s7comm" => {
            let host = required_str(p, "host")?;
            let port = u16::try_from(p.get("port").and_then(Value::as_u64).unwrap_or(102))
                .map_err(|_| "invalid S7 port".to_string())?;
            let plc_type = required_str(p, "plc_type")?;
            let rack = u8::try_from(p.get("rack").and_then(Value::as_u64).unwrap_or(0))
                .map_err(|_| "invalid S7 rack".to_string())?;
            let slot = u8::try_from(p.get("slot").and_then(Value::as_u64).unwrap_or(1))
                .map_err(|_| "invalid S7 slot".to_string())?;
            let db_number = u16::try_from(required_u64(p, "db_number")?)
                .map_err(|_| "invalid S7 DB number".to_string())?;
            let offset = u16::try_from(p.get("offset").and_then(Value::as_u64).unwrap_or(0))
                .map_err(|_| "invalid S7 DB offset".to_string())?;
            let count = u16::try_from(required_u64(p, "count")?)
                .map_err(|_| "invalid S7 byte count".to_string())?;
            let timeout_ms = p.get("timeout_ms").and_then(Value::as_u64).unwrap_or(3000);
            if port == 0 || !(100..=30000).contains(&timeout_ms) || count == 0 || count > 200 {
                return Err("S7 port, timeout or byte count out of range".into());
            }
            let key = format!("{host}:{port}/{plc_type}/{rack}/{slot}/{timeout_ms}");
            if !s7_clients.contains_key(&key) {
                let client = S7IpReadOnlyClient::connect(host, port, plc_type, rack, slot, timeout_ms)
                    .map_err(|e| e.to_string())?;
                s7_clients.insert(key.clone(), client);
            }
            let client = s7_clients.get_mut(&key).expect("S7 session inserted");
            let bytes = client.read_db_bytes(db_number, offset, count).map_err(|e| e.to_string())?;
            Ok(json!({"plc_type":plc_type,"db_number":db_number,"offset":offset,
                "count":bytes.len(),"bytes":bytes}))
        }
        "bacnet-ip" => {
            let address: SocketAddr = required_str(p, "address")?.parse().map_err(|_| "invalid BACnet address".to_string())?;
            let device_instance = u32::try_from(required_u64(p, "device_instance")?)
                .map_err(|_| "invalid BACnet device instance".to_string())?;
            let local_bind: SocketAddr = required_str(p, "local_bind")?.parse().map_err(|_| "invalid BACnet local bind".to_string())?;
            let timeout_ms = p.get("timeout_ms").and_then(Value::as_u64).unwrap_or(3000);
            if !(100..=30000).contains(&timeout_ms) { return Err("BACnet timeout_ms must be 100..30000".into()); }
            let client = BacnetIpReadOnlyClient::new(local_bind, Duration::from_millis(timeout_ms)).map_err(|e| e.to_string())?;
            let (device, objects) = client.read_device_snapshot(address, device_instance).map_err(|e| e.to_string())?;
            let rows: Vec<Value> = objects.into_iter().map(|o| json!({
                "object_identifier":o.object_identifier, "object_type_name":o.object_type_name,
                "object_instance":o.object_instance, "object_name":o.object_name,
                "description":o.description, "present_value":o.present_value,
                "units":o.units, "status_flags":o.status_flags
            })).collect();
            Ok(json!({"device":{"address":device.address,"device_instance":device.device_instance,
                "vendor_id":device.vendor_id,"vendor_name":device.vendor_name,
                "max_apdu":device.max_apdu,"segmentation":device.segmentation,"route":device.route},"objects":rows}))
        }
        "knxnet-ip" => {
            let gateway: SocketAddr = required_str(p, "gateway")?.parse().map_err(|_| "invalid KNX gateway".to_string())?;
            let local_bind: SocketAddr = required_str(p, "local_bind")?.parse().map_err(|_| "invalid KNX local bind".to_string())?;
            let group_address = required_str(p, "group_address")?;
            let dpt = required_str(p, "dpt")?;
            let timeout_ms = p.get("timeout_ms").and_then(Value::as_u64).unwrap_or(2000);
            if !(100..=30000).contains(&timeout_ms) { return Err("KNX timeout_ms must be 100..30000".into()); }
            let client = KnxIpReadOnlyClient::connect(gateway, local_bind).map_err(|e| e.to_string())?;
            let read_result = client.read_group(group_address, dpt, Duration::from_millis(timeout_ms));
            client.close();
            let sample = read_result.map_err(|e| e.to_string())?;
            Ok(json!({"group_address":sample.group_address,"dpt":sample.dpt,
                "value":sample.value,"display_value":sample.display_value}))
        }
        other => Err(format!("unsupported protocol: {other}")),
    }
}

fn main() {
    let stdin = stdin();
    let stdout = stdout();
    let mut input = BufReader::new(stdin.lock());
    let mut output = BufWriter::new(stdout.lock());
    let mut worker = Worker::new();
    loop {
        let request = match read_frame(&mut input) {
            Ok(Some(frame)) => frame,
            Ok(None) => break,
            Err(_) => break,
        };
        let (kind, payload, should_exit) = worker.handle(request.clone());
        if worker.scope.is_none() { break; }
        let response = worker.response(&request, kind, payload);
        if write_frame(&mut output, &response).is_err() { break; }
        if should_exit { break; }
    }
}
