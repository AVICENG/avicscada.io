use serde::{Deserialize, Serialize};
use std::io::{self, BufRead, Read, Write};
use std::net::{IpAddr, SocketAddr, TcpStream};
use std::time::Duration;

#[derive(Debug, Deserialize)]
struct Request {
    request_id: u64,
    operation: String,
    host: Option<String>,
    port: Option<u16>,
    unit_id: Option<u8>,
    timeout_ms: Option<u64>,
    function: Option<u8>,
    address: Option<u16>,
    count: Option<u16>,
}

#[derive(Debug, Serialize)]
struct Response {
    request_id: u64,
    ok: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    values: Option<Vec<u16>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    error: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    engine: Option<&'static str>,
    #[serde(skip_serializing_if = "Option::is_none")]
    capabilities: Option<Vec<&'static str>>,
}

impl Response {
    fn success(request_id: u64, values: Option<Vec<u16>>) -> Self {
        Self { request_id, ok: true, values, error: None, engine: None, capabilities: None }
    }

    fn failure(request_id: u64, error: impl Into<String>) -> Self {
        Self { request_id, ok: false, values: None, error: Some(error.into()), engine: None, capabilities: None }
    }
}

fn read_exact(stream: &mut TcpStream, size: usize) -> Result<Vec<u8>, String> {
    let mut buffer = vec![0_u8; size];
    stream.read_exact(&mut buffer).map_err(|e| format!("Modbus TCP receive failed: {e}"))?;
    Ok(buffer)
}

fn modbus_read(
    host: &str, port: u16, unit_id: u8, timeout_ms: u64,
    function: u8, address: u16, count: u16, transaction_id: u16,
) -> Result<Vec<u16>, String> {
    let ip: IpAddr = host.parse().map_err(|_| "host must be a literal IPv4/IPv6 address".to_string())?;
    if port == 0 || unit_id > 247 || !(100..=10_000).contains(&timeout_ms) {
        return Err("invalid Modbus TCP port, unit_id, or timeout_ms".into());
    }
    let max_count = if function == 1 || function == 2 { 2000 } else { 125 };
    if !(1..=4).contains(&function) || count == 0 || count > max_count
        || u32::from(address) + u32::from(count) > 65_536 {
        return Err("invalid Modbus read function or address/count".into());
    }

    let timeout = Duration::from_millis(timeout_ms);
    let socket = SocketAddr::new(ip, port);
    let mut stream = TcpStream::connect_timeout(&socket, timeout)
        .map_err(|e| format!("Modbus TCP connect failed: {e}"))?;
    stream.set_read_timeout(Some(timeout)).map_err(|e| e.to_string())?;
    stream.set_write_timeout(Some(timeout)).map_err(|e| e.to_string())?;

    let mut request = Vec::with_capacity(12);
    request.extend_from_slice(&transaction_id.to_be_bytes());
    request.extend_from_slice(&0_u16.to_be_bytes());
    request.extend_from_slice(&6_u16.to_be_bytes());
    request.push(unit_id);
    request.push(function);
    request.extend_from_slice(&address.to_be_bytes());
    request.extend_from_slice(&count.to_be_bytes());
    stream.write_all(&request).map_err(|e| format!("Modbus TCP send failed: {e}"))?;

    let header = read_exact(&mut stream, 7)?;
    let response_tid = u16::from_be_bytes([header[0], header[1]]);
    let protocol_id = u16::from_be_bytes([header[2], header[3]]);
    let length = u16::from_be_bytes([header[4], header[5]]);
    let response_unit = header[6];
    if response_tid != transaction_id || protocol_id != 0 || response_unit != unit_id
        || !(2..=254).contains(&length) {
        return Err("invalid Modbus TCP MBAP response header".into());
    }
    let body = read_exact(&mut stream, usize::from(length - 1))?;
    let response_function = body[0];
    if response_function == (function | 0x80) {
        let code = body.get(1).copied().unwrap_or(255);
        return Err(format!("Modbus exception response: {code}"));
    }
    if response_function != function {
        return Err("unexpected Modbus function in response".into());
    }

    if function == 3 || function == 4 {
        let expected_bytes = usize::from(count) * 2;
        if body.len() != expected_bytes + 2 || usize::from(body[1]) != expected_bytes {
            return Err("invalid Modbus register response length".into());
        }
        let mut values = Vec::with_capacity(usize::from(count));
        for chunk in body[2..].chunks_exact(2) {
            values.push(u16::from_be_bytes([chunk[0], chunk[1]]));
        }
        Ok(values)
    } else {
        let expected_bytes = (usize::from(count) + 7) / 8;
        if body.len() != expected_bytes + 2 || usize::from(body[1]) != expected_bytes {
            return Err("invalid Modbus bit response length".into());
        }
        let mut values = Vec::with_capacity(usize::from(count));
        for index in 0..usize::from(count) {
            values.push(if ((body[2 + index / 8] >> (index % 8)) & 1) == 1 { 1 } else { 0 });
        }
        Ok(values)
    }
}

fn handle(request: Request) -> (Response, bool) {
    match request.operation.as_str() {
        "health" => (
            Response {
                request_id: request.request_id, ok: true, values: None, error: None,
                engine: Some("avic-communication-engine"),
                capabilities: Some(vec!["modbus-tcp-read-1-4"]),
            }, false
        ),
        "shutdown" => (Response::success(request.request_id, None), true),
        "modbus_read" => {
            let result = modbus_read(
                request.host.as_deref().unwrap_or(""),
                request.port.unwrap_or(502),
                request.unit_id.unwrap_or(1),
                request.timeout_ms.unwrap_or(2000),
                request.function.unwrap_or(0),
                request.address.unwrap_or(0),
                request.count.unwrap_or(0),
                (request.request_id as u16).wrapping_add(1),
            );
            match result {
                Ok(values) => (Response::success(request.request_id, Some(values)), false),
                Err(error) => (Response::failure(request.request_id, error), false),
            }
        }
        other => (Response::failure(request.request_id, format!("unsupported operation: {other}")), false),
    }
}

fn main() {
    let stdin = io::stdin();
    let stdout = io::stdout();
    let mut output = stdout.lock();
    for line in stdin.lock().lines() {
        let line = match line { Ok(value) => value, Err(_) => break };
        if line.trim().is_empty() { continue; }
        let parsed: Result<Request, _> = serde_json::from_str(&line);
        let (response, shutdown) = match parsed {
            Ok(request) => handle(request),
            Err(error) => (Response::failure(0, format!("invalid request JSON: {error}")), false),
        };
        if serde_json::to_writer(&mut output, &response).is_err() { break; }
        if output.write_all(b"\n").and_then(|_| output.flush()).is_err() { break; }
        if shutdown { break; }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::net::TcpListener;
    use std::thread;

    fn fake_server(body: Vec<u8>, wrong_tid: bool) -> (u16, thread::JoinHandle<()>) {
        let listener = TcpListener::bind(("127.0.0.1", 0)).unwrap();
        let port = listener.local_addr().unwrap().port();
        let handle = thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let request = read_exact(&mut stream, 12).unwrap();
            let tid = u16::from_be_bytes([request[0], request[1]]);
            let response_tid = if wrong_tid { tid.wrapping_add(1) } else { tid };
            let mut response = Vec::new();
            response.extend_from_slice(&response_tid.to_be_bytes());
            response.extend_from_slice(&0_u16.to_be_bytes());
            response.extend_from_slice(&((body.len() + 1) as u16).to_be_bytes());
            response.push(request[6]);
            response.extend_from_slice(&body);
            stream.write_all(&response).unwrap();
        });
        (port, handle)
    }

    #[test]
    fn reads_holding_registers_and_validates_mbap() {
        let (port, server) = fake_server(vec![3, 4, 0x12, 0x34, 0x56, 0x78], false);
        let values = modbus_read("127.0.0.1", port, 1, 1000, 3, 0, 2, 17).unwrap();
        assert_eq!(values, vec![0x1234, 0x5678]);
        server.join().unwrap();
    }

    #[test]
    fn reads_coils_as_individual_bits() {
        let (port, server) = fake_server(vec![1, 1, 0b0000_0101], false);
        let values = modbus_read("127.0.0.1", port, 1, 1000, 1, 0, 3, 18).unwrap();
        assert_eq!(values, vec![1, 0, 1]);
        server.join().unwrap();
    }

    #[test]
    fn rejects_wrong_transaction_id() {
        let (port, server) = fake_server(vec![3, 2, 0, 7], true);
        let error = modbus_read("127.0.0.1", port, 1, 1000, 3, 0, 1, 19).unwrap_err();
        assert!(error.contains("MBAP"));
        server.join().unwrap();
    }

    #[test]
    fn reports_modbus_exception_response() {
        let (port, server) = fake_server(vec![0x83, 2], false);
        let error = modbus_read("127.0.0.1", port, 1, 1000, 3, 0, 1, 20).unwrap_err();
        assert!(error.contains("exception response: 2"));
        server.join().unwrap();
    }
}
