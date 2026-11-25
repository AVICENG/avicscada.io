import socket
import struct
import threading
import pytest
from avic_core.network import ModbusTcpClient, ModbusProtocolError, decode_registers


def test_decode_registers_supports_signed_float_and_word_order():
    assert decode_registers([0xFFFE], "int16") == -2
    assert decode_registers([0x3F80, 0x0000], "float32") == 1.0
    assert decode_registers([0x0000, 0x3F80], "float32", word_order="little") == 1.0


def test_decode_rejects_wrong_register_count_and_order():
    with pytest.raises(ValueError):
        decode_registers([1], "float32")
    with pytest.raises(ValueError):
        decode_registers([1], "uint16", byte_order="middle")


def test_modbus_tcp_reads_holding_registers_against_local_test_server():
    server = socket.socket()
    server.bind(("127.0.0.1", 0)); server.listen(1)
    port = server.getsockname()[1]
    def serve():
        conn, _ = server.accept()
        with conn:
            req = conn.recv(260)
            tid, proto, length, unit = struct.unpack(">HHHB", req[:7])
            function, address, count = struct.unpack(">BHH", req[7:12])
            assert (proto, unit, function, address, count) == (0, 7, 3, 10, 2)
            pdu = bytes([3, 4]) + struct.pack(">HH", 123, 456)
            conn.sendall(struct.pack(">HHHB", tid, 0, len(pdu)+1, unit) + pdu)
        server.close()
    thread = threading.Thread(target=serve, daemon=True); thread.start()
    values = ModbusTcpClient("127.0.0.1", port, unit_id=7).read_holding_registers(10, 2)
    thread.join(timeout=2)
    assert values == [123, 456]


def test_modbus_read_client_rejects_invalid_count_before_network_io():
    client = ModbusTcpClient("127.0.0.1")
    with pytest.raises(ValueError):
        client.read_holding_registers(0, 126)


def test_modbus_has_no_write_api():
    client = ModbusTcpClient("127.0.0.1")
    assert not hasattr(client, "write_register")
    assert not hasattr(client, "write_coil")
