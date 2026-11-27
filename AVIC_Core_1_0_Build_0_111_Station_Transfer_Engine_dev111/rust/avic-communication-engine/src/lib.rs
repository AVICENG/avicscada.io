//! AVIC Communication Engine pilot.
//! This first implementation is intentionally read-only and supports Modbus TCP FC03.
//! It is a benchmarkable transport kernel, not yet the production Driver SDK/IPC worker.

use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream, ToSocketAddrs};
use std::time::Duration;

#[derive(Debug)]
pub enum ModbusError {
    Io(std::io::Error),
    InvalidArgument(&'static str),
    Protocol(&'static str),
    Exception(u8),
}
impl std::fmt::Display for ModbusError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io(e) => write!(f, "I/O: {e}"),
            Self::InvalidArgument(s) => write!(f, "invalid argument: {s}"),
            Self::Protocol(s) => write!(f, "Modbus protocol: {s}"),
            Self::Exception(c) => write!(f, "Modbus exception response: {c}"),
        }
    }
}
impl std::error::Error for ModbusError {}
impl From<std::io::Error> for ModbusError {
    fn from(value: std::io::Error) -> Self { Self::Io(value) }
}

#[derive(Clone, Debug)]
pub struct ModbusTcpConfig {
    pub address: SocketAddr,
    pub unit_id: u8,
    pub timeout: Duration,
}
impl ModbusTcpConfig {
    pub fn new(host: &str, port: u16, unit_id: u8, timeout: Duration) -> Result<Self, ModbusError> {
        if port == 0 || unit_id > 247 || timeout.is_zero() {
            return Err(ModbusError::InvalidArgument("port, unit_id or timeout out of range"));
        }
        let address = (host, port).to_socket_addrs()?.next()
            .ok_or(ModbusError::InvalidArgument("host did not resolve"))?;
        Ok(Self { address, unit_id, timeout })
    }
}

pub struct ModbusTcpClient {
    config: ModbusTcpConfig,
    transaction_id: u16,
}
impl ModbusTcpClient {
    pub fn new(config: ModbusTcpConfig) -> Self { Self { config, transaction_id: 0 } }

    /// Read holding registers only (function code 03). No write API is exposed.
    pub fn read_holding_registers(&mut self, address: u16, count: u16) -> Result<Vec<u16>, ModbusError> {
        if count == 0 || count > 125 || (address as u32 + count as u32) > 65536 {
            return Err(ModbusError::InvalidArgument("FC03 count must be 1..125 and address range must fit"));
        }
        self.transaction_id = self.transaction_id.wrapping_add(1);
        let tid = self.transaction_id;
        let mut request = Vec::with_capacity(12);
        request.extend_from_slice(&tid.to_be_bytes());
        request.extend_from_slice(&0u16.to_be_bytes());
        request.extend_from_slice(&6u16.to_be_bytes());
        request.push(self.config.unit_id);
        request.push(3);
        request.extend_from_slice(&address.to_be_bytes());
        request.extend_from_slice(&count.to_be_bytes());

        let mut stream = TcpStream::connect_timeout(&self.config.address, self.config.timeout)?;
        stream.set_read_timeout(Some(self.config.timeout))?;
        stream.set_write_timeout(Some(self.config.timeout))?;
        stream.write_all(&request)?;

        let mut header = [0u8; 7];
        stream.read_exact(&mut header)?;
        let response_tid = u16::from_be_bytes([header[0], header[1]]);
        let protocol = u16::from_be_bytes([header[2], header[3]]);
        let length = u16::from_be_bytes([header[4], header[5]]);
        let unit = header[6];
        if response_tid != tid || protocol != 0 || unit != self.config.unit_id || !(2..=254).contains(&length) {
            return Err(ModbusError::Protocol("invalid MBAP header"));
        }
        let mut body = vec![0u8; length as usize - 1];
        stream.read_exact(&mut body)?;
        // Modbus exception responses have a two-byte PDU and MBAP length 3,
        // independent of the requested register count.
        if body.first() == Some(&0x83) {
            if length != 3 || body.len() != 2 {
                return Err(ModbusError::Protocol("invalid Modbus exception response length"));
            }
            return Err(ModbusError::Exception(body[1]));
        }
        if length as usize != 3 + count as usize * 2 {
            return Err(ModbusError::Protocol("unexpected MBAP response length"));
        }
        if body.len() != 2 + count as usize * 2 || body[0] != 3 || body[1] as usize != count as usize * 2 {
            return Err(ModbusError::Protocol("invalid FC03 response payload"));
        }
        let mut registers = Vec::with_capacity(count as usize);
        for pair in body[2..].chunks_exact(2) {
            registers.push(u16::from_be_bytes([pair[0], pair[1]]));
        }
        Ok(registers)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn test_server(pdu: Vec<u8>, wrong_transaction_id: bool) -> (SocketAddr, std::thread::JoinHandle<()>) {
        use std::net::TcpListener;
        let listener = TcpListener::bind(("127.0.0.1", 0)).unwrap();
        let address = listener.local_addr().unwrap();
        let handle = std::thread::spawn(move || {
            let (mut stream, _) = listener.accept().unwrap();
            let mut request = [0u8; 12];
            stream.read_exact(&mut request).unwrap();
            let mut tid = u16::from_be_bytes([request[0], request[1]]);
            if wrong_transaction_id { tid = tid.wrapping_add(1); }
            let length = (1 + pdu.len()) as u16;
            let mut response = Vec::with_capacity(7 + pdu.len());
            response.extend_from_slice(&tid.to_be_bytes());
            response.extend_from_slice(&0u16.to_be_bytes());
            response.extend_from_slice(&length.to_be_bytes());
            response.push(request[6]);
            response.extend_from_slice(&pdu);
            stream.write_all(&response).unwrap();
        });
        (address, handle)
    }

    #[test]
    fn reads_valid_fc03_response() {
        let (address, server) = test_server(vec![3, 4, 0, 10, 0, 20], false);
        let config = ModbusTcpConfig { address, unit_id: 1, timeout: Duration::from_secs(1) };
        let mut client = ModbusTcpClient::new(config);
        assert_eq!(client.read_holding_registers(0, 2).unwrap(), vec![10, 20]);
        server.join().unwrap();
    }

    #[test]
    fn parses_fc03_exception_response() {
        let (address, server) = test_server(vec![0x83, 2], false);
        let config = ModbusTcpConfig { address, unit_id: 1, timeout: Duration::from_secs(1) };
        let mut client = ModbusTcpClient::new(config);
        assert!(matches!(client.read_holding_registers(0, 2), Err(ModbusError::Exception(2))));
        server.join().unwrap();
    }

    #[test]
    fn rejects_wrong_transaction_id() {
        let (address, server) = test_server(vec![3, 4, 0, 10, 0, 20], true);
        let config = ModbusTcpConfig { address, unit_id: 1, timeout: Duration::from_secs(1) };
        let mut client = ModbusTcpClient::new(config);
        assert!(matches!(client.read_holding_registers(0, 2), Err(ModbusError::Protocol("invalid MBAP header"))));
        server.join().unwrap();
    }

    #[test]
    fn rejects_invalid_unit_and_timeout() {
        assert!(ModbusTcpConfig::new("127.0.0.1", 502, 248, Duration::from_secs(1)).is_err());
        assert!(ModbusTcpConfig::new("127.0.0.1", 502, 1, Duration::ZERO).is_err());
    }

    #[test]
    fn validates_port_and_address_range() {
        assert!(ModbusTcpConfig::new("127.0.0.1", 0, 1, Duration::from_secs(1)).is_err());
        let cfg = ModbusTcpConfig::new("127.0.0.1", 502, 1, Duration::from_secs(1)).unwrap();
        let mut client = ModbusTcpClient::new(cfg);
        assert!(matches!(client.read_holding_registers(0, 0), Err(ModbusError::InvalidArgument(_))));
        assert!(matches!(client.read_holding_registers(65535, 2), Err(ModbusError::InvalidArgument(_))));
        assert!(matches!(client.read_holding_registers(0, 126), Err(ModbusError::InvalidArgument(_))));
    }
}
