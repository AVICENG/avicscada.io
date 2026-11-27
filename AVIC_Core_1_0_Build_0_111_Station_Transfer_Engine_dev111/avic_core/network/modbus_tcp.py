"""Explicit, bounded, read-only Modbus TCP client and register decoders."""
from __future__ import annotations
import socket
import struct
import threading
from typing import Literal

class ModbusProtocolError(ValueError):
    pass

_BYTE_ORDERS = ("big", "little")


def decode_registers(registers: list[int] | tuple[int, ...], data_type: str = "uint16", *,
                     byte_order: Literal["big", "little"] = "big",
                     word_order: Literal["big", "little"] = "big"):
    if byte_order not in _BYTE_ORDERS or word_order not in _BYTE_ORDERS:
        raise ValueError("byte_order and word_order must be big or little")
    if not registers or any(not isinstance(x, int) or not 0 <= x <= 65535 for x in registers):
        raise ValueError("registers must contain 16-bit unsigned integers")
    sizes = {"uint16": 1, "int16": 1, "uint32": 2, "int32": 2, "float32": 2,
             "uint64": 4, "int64": 4, "float64": 4}
    if data_type not in sizes or len(registers) != sizes[data_type]:
        raise ValueError("register count does not match supported data_type")
    words = list(registers)
    if word_order == "little" and len(words) > 1:
        words.reverse()
    raw = b"".join(x.to_bytes(2, "big") for x in words)
    if byte_order == "little":
        raw = b"".join(raw[i:i+2][::-1] for i in range(0, len(raw), 2))
    fmt = {"uint16": ">H", "int16": ">h", "uint32": ">I", "int32": ">i",
           "float32": ">f", "uint64": ">Q", "int64": ">q", "float64": ">d"}[data_type]
    return struct.unpack(fmt, raw)[0]


class ModbusTcpClient:
    """No write methods are implemented. Each read is explicit and bounded."""
    def __init__(self, host: str, port: int = 502, *, unit_id: int = 1, timeout: float = 2.0):
        import ipaddress
        ipaddress.ip_address(host)
        if not 1 <= port <= 65535 or not 0 <= unit_id <= 247 or not 0.1 <= timeout <= 10:
            raise ValueError("invalid Modbus TCP port, unit_id or timeout")
        self.host, self.port, self.unit_id, self.timeout = host, port, unit_id, timeout
        self._transaction_id = 0
        self._transaction_lock = threading.Lock()

    def _next_transaction_id(self) -> int:
        # Reserve each MBAP transaction identifier atomically when polling groups concurrently.
        with self._transaction_lock:
            self._transaction_id = (self._transaction_id + 1) & 0xffff
            return self._transaction_id

    def _read(self, function: int, address: int, count: int) -> list[int]:
        if function not in (1, 2, 3, 4):
            raise ValueError("only Modbus read functions 1..4 are supported")
        max_count = 2000 if function in (1, 2) else 125
        if not 0 <= address <= 65535 or not 1 <= count <= max_count or address + count > 65536:
            raise ValueError("invalid Modbus address/count")
        tid = self._next_transaction_id()
        pdu = struct.pack(">BHH", function, address, count)
        request = struct.pack(">HHHB", tid, 0, len(pdu) + 1, self.unit_id) + pdu
        with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
            sock.settimeout(self.timeout)
            sock.sendall(request)
            header = self._recv_exact(sock, 7)
            r_tid, protocol, length, unit = struct.unpack(">HHHB", header)
            if r_tid != tid or protocol != 0 or unit != self.unit_id or not 2 <= length <= 254:
                raise ModbusProtocolError("invalid Modbus TCP MBAP header")
            body = self._recv_exact(sock, length - 1)
        response_function = body[0]
        if response_function == (function | 0x80):
            code = body[1] if len(body) > 1 else -1
            raise ModbusProtocolError(f"Modbus exception response: {code}")
        if response_function != function:
            raise ModbusProtocolError("unexpected Modbus function in response")
        if function in (3, 4):
            if len(body) < 2 or body[1] != count * 2 or len(body) != 2 + count * 2:
                raise ModbusProtocolError("invalid register response length")
            return list(struct.unpack(">" + "H" * count, body[2:]))
        expected = (count + 7) // 8
        if len(body) < 2 or body[1] != expected or len(body) != 2 + expected:
            raise ModbusProtocolError("invalid bit response length")
        return [((body[2 + i // 8] >> (i % 8)) & 1) for i in range(count)]

    @staticmethod
    def _recv_exact(sock: socket.socket, size: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < size:
            part = sock.recv(size - len(chunks))
            if not part:
                raise ModbusProtocolError("connection closed during Modbus response")
            chunks.extend(part)
        return bytes(chunks)

    def read_holding_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read(3, address, count)

    def read_input_registers(self, address: int, count: int = 1) -> list[int]:
        return self._read(4, address, count)

    def read_coils(self, address: int, count: int = 1) -> list[int]:
        return self._read(1, address, count)

    def read_discrete_inputs(self, address: int, count: int = 1) -> list[int]:
        return self._read(2, address, count)

    def read_device_identification(self, *, read_code: int = 1, max_objects: int = 32) -> dict[str, str]:
        """Read Modbus Encapsulated Interface Transport / MEI 0x0E device identity.

        Uses function 0x2B/MEI 0x0E only. No write or control request is sent.
        """
        if read_code not in (1, 2, 3, 4) or not 1 <= max_objects <= 64:
            raise ValueError("invalid Modbus device-identification read_code/max_objects")
        objects: dict[str, str] = {}
        next_id = 0
        for _ in range(max_objects):
            # Share the atomic MBAP allocator with normal reads during concurrent polling.
            tid = self._next_transaction_id()
            pdu = bytes((0x2B, 0x0E, read_code, next_id))
            request = struct.pack(">HHHB", tid, 0, len(pdu) + 1, self.unit_id) + pdu
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(request)
                header = self._recv_exact(sock, 7)
                r_tid, protocol, length, unit = struct.unpack(">HHHB", header)
                if r_tid != tid or protocol != 0 or unit != self.unit_id or not 2 <= length <= 254:
                    raise ModbusProtocolError("invalid Modbus device-identification MBAP header")
                body = self._recv_exact(sock, length - 1)
            if body and body[0] == 0xAB:
                if len(body) != 2:
                    raise ModbusProtocolError("malformed Modbus device-identification exception")
                raise ModbusProtocolError(f"Modbus device-identification exception: {body[1]}")
            if len(body) < 7 or body[0:2] != bytes((0x2B, 0x0E)):
                raise ModbusProtocolError("invalid Modbus MEI 0x0E response")
            if body[2] != read_code:
                raise ModbusProtocolError("Modbus MEI response read-code mismatch")
            if body[3] not in (0x01, 0x02, 0x03, 0x81, 0x82, 0x83):
                raise ModbusProtocolError("invalid Modbus MEI conformity level")
            more_follows = body[4]
            if more_follows not in (0x00, 0xFF):
                raise ModbusProtocolError("invalid Modbus MEI more-follows flag")
            next_object = body[5]
            count = body[6]
            pos = 7
            for _item in range(count):
                if pos + 2 > len(body):
                    raise ModbusProtocolError("truncated Modbus device-identification object")
                object_id, size = body[pos], body[pos + 1]
                pos += 2
                if pos + size > len(body):
                    raise ModbusProtocolError("truncated Modbus device-identification value")
                if str(object_id) in objects:
                    raise ModbusProtocolError("duplicate Modbus device-identification object")
                objects[str(object_id)] = body[pos:pos + size].decode("utf-8", errors="replace")
                pos += size
            if pos != len(body):
                raise ModbusProtocolError("unexpected trailing bytes in Modbus device-identification response")
            if more_follows == 0:
                return objects
            if next_object <= next_id:
                raise ModbusProtocolError("invalid Modbus device-identification continuation")
            next_id = next_object
        raise ModbusProtocolError("Modbus device-identification object limit exceeded")
