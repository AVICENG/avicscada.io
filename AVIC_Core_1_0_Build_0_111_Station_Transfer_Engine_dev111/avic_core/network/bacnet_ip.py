"""Minimal BACnet/IP client for safe discovery and read-only property access.

Implements BACnet/IP BVLC + basic NPDU/APDU services using the Python standard
library. It deliberately exposes no write, reboot, or configuration services.
"""
from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket
import struct
import time
import threading
from functools import wraps
from typing import Any

from .contracts import BacnetIpNetworkConfig, DiscoveryPolicy, DiscoveredDevice
from .identity import DeviceIdentityResolver


class BacnetProtocolError(ValueError):
    pass


def _serialized_io(method):
    """Serialize access to the UDP socket and invoke-id space per BACnet client."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        with self._io_lock:
            return method(self, *args, **kwargs)
    return wrapper


@dataclass(frozen=True)
class BacnetIAm:
    device_instance: int
    max_apdu: int
    segmentation: int
    vendor_id: int
    source: tuple[str, int]


@dataclass(frozen=True)
class BacnetObjectIdentifier:
    """Native BACnet object identity returned by Device.Object_List."""
    object_type: int
    instance: int

    @property
    def type_name(self) -> str:
        return _OBJECT_TYPE_NAMES.get(self.object_type, f"unknown-{self.object_type}")

    @property
    def native_identity(self) -> str:
        return f"bacnet:object:{self.object_type}:{self.instance}"


_OBJECT_TYPE_NAMES = {
    0: "analog-input", 1: "analog-output", 2: "analog-value",
    3: "binary-input", 4: "binary-output", 5: "binary-value",
    6: "calendar", 8: "device", 13: "multi-state-input",
    14: "multi-state-output", 15: "notification-class",
    17: "schedule", 19: "trend-log", 20: "life-safety-point",
}


# BACnet application tag numbers used by the safe property decoder.
_APP_UNSIGNED = 2
_APP_SIGNED = 3
_APP_REAL = 4
_APP_DOUBLE = 5
_APP_OCTET_STRING = 6
_APP_CHARACTER_STRING = 7
_APP_BIT_STRING = 8
_APP_ENUMERATED = 9
_APP_BOOLEAN = 1
_APP_OBJECT_IDENTIFIER = 12


def _tag(data: bytes, offset: int) -> tuple[bool, int, int, int, int]:
    if offset >= len(data):
        raise BacnetProtocolError("truncated BACnet tag")
    first = data[offset]
    number = first >> 4
    context = bool(first & 0x08)
    lvt = first & 0x07
    pos = offset + 1
    if number == 15:
        if pos >= len(data):
            raise BacnetProtocolError("truncated extended tag number")
        number = data[pos]
        pos += 1
    if lvt == 5:
        if pos >= len(data):
            raise BacnetProtocolError("truncated extended tag length")
        length = data[pos]
        pos += 1
        if length == 254:
            if pos + 2 > len(data):
                raise BacnetProtocolError("truncated 16-bit tag length")
            length = int.from_bytes(data[pos:pos+2], "big"); pos += 2
        elif length == 255:
            if pos + 4 > len(data):
                raise BacnetProtocolError("truncated 32-bit tag length")
            length = int.from_bytes(data[pos:pos+4], "big"); pos += 4
    else:
        length = lvt
    return context, number, length, pos, pos + length


def _application_values(data: bytes) -> list[tuple[int, Any]]:
    values: list[tuple[int, Any]] = []
    pos = 0
    while pos < len(data):
        context, number, length, start, end = _tag(data, pos)
        if context:
            # Constructed context delimiters are retained as opaque markers.
            values.append((-(number + 1), data[start:end]))
        else:
            raw = data[start:end]
            if number == _APP_BOOLEAN:
                value: Any = bool(length)
            elif number in (_APP_UNSIGNED, _APP_ENUMERATED):
                value = int.from_bytes(raw, "big")
            elif number == _APP_SIGNED:
                value = int.from_bytes(raw, "big", signed=True)
            elif number == _APP_REAL and length == 4:
                value = struct.unpack(">f", raw)[0]
            elif number == _APP_DOUBLE and length == 8:
                value = struct.unpack(">d", raw)[0]
            elif number == _APP_CHARACTER_STRING and length >= 1:
                # Character set 0 is ANSI X3.4 / ASCII; preserve unknown encodings safely.
                enc = raw[0]
                codec = {0: "ascii", 3: "utf-8"}.get(enc, "latin-1")
                value = raw[1:].decode(codec, errors="replace")
            elif number == _APP_OBJECT_IDENTIFIER and length == 4:
                ident = int.from_bytes(raw, "big")
                value = {"object_type": (ident >> 22) & 0x3ff, "instance": ident & 0x3fffff}
            elif number == _APP_BIT_STRING and length >= 1:
                unused = raw[0]
                bits = ''.join(f'{b:08b}' for b in raw[1:])
                value = bits[:max(0, len(bits)-unused)]
            else:
                value = raw
            values.append((number, value))
        if end <= pos or end > len(data):
            raise BacnetProtocolError("invalid BACnet tag length")
        pos = end
    return values


def _parse_npdu_header(packet: bytes, pos: int) -> tuple[int, dict[str, Any]]:
    """Return APDU offset and decoded NPDU addressing fields.

    BACnet NPDU control bits: 0x20 destination specifier, 0x08 source
    specifier, 0x80 network-layer message. Hop count belongs to the
    destination specifier; it is not an independent control bit.
    """
    if pos + 2 > len(packet):
        raise BacnetProtocolError("truncated NPDU header")
    version = packet[pos]
    control = packet[pos + 1]
    if version != 0x01:
        raise BacnetProtocolError(f"unsupported NPDU version 0x{version:02X}")
    pos += 2
    fields: dict[str, Any] = {"npdu_version": version, "npdu_control": f"0x{control:02X}"}

    if control & 0x20:  # destination specifier: DNET, DLEN, DADR, hop count
        if pos + 3 > len(packet):
            raise BacnetProtocolError("truncated NPDU destination specifier")
        dnet = int.from_bytes(packet[pos:pos + 2], "big")
        dlen = packet[pos + 2]
        pos += 3
        if pos + dlen + 1 > len(packet):
            raise BacnetProtocolError("truncated NPDU destination address or hop count")
        dadr = packet[pos:pos + dlen]
        pos += dlen
        hop_count = packet[pos]
        pos += 1
        fields.update({"destination_network": dnet, "destination_address_length": dlen,
                       "destination_address": dadr.hex(" ").upper(), "hop_count": hop_count})

    if control & 0x08:  # source specifier: SNET, SLEN, SADR
        if pos + 3 > len(packet):
            raise BacnetProtocolError("truncated NPDU source specifier")
        snet = int.from_bytes(packet[pos:pos + 2], "big")
        slen = packet[pos + 2]
        pos += 3
        if pos + slen > len(packet):
            raise BacnetProtocolError("truncated NPDU source address")
        sadr = packet[pos:pos + slen]
        pos += slen
        fields.update({"source_network": snet, "source_address_length": slen,
                       "source_address": sadr.hex(" ").upper()})

    if control & 0x80:
        fields["network_layer_message"] = True
        raise BacnetProtocolError("NPDU is a network-layer message, not an APDU")
    return pos, fields


def parse_iam(packet: bytes, source: tuple[str, int]) -> BacnetIAm | None:
    """Parse I-Am in BACnet/IP Original-Unicast/Broadcast or Forwarded-NPDU."""
    if len(packet) < 10 or packet[0] != 0x81:
        return None
    bvlc_len = int.from_bytes(packet[2:4], "big")
    if bvlc_len != len(packet):
        return None
    function = packet[1]
    if function in (0x0A, 0x0B):
        pos = 4
    elif function == 0x04:  # Forwarded-NPDU: original IPv4 address + UDP port precede NPDU
        if len(packet) < 14:
            return None
        source = (socket.inet_ntoa(packet[4:8]), int.from_bytes(packet[8:10], "big"))
        pos = 10
    else:
        return None
    try:
        pos, _ = _parse_npdu_header(packet, pos)
        if pos + 2 > len(packet):
            return None
        apdu = packet[pos:]
        if apdu[0] != 0x10 or apdu[1] != 0x00:  # unconfirmed I-Am
            return None
        vals = _application_values(apdu[2:])
    except (BacnetProtocolError, IndexError, ValueError):
        return None
    if len(vals) < 4 or vals[0][0] != _APP_OBJECT_IDENTIFIER:
        return None
    obj = vals[0][1]
    if not isinstance(obj, dict) or obj["object_type"] != 8:
        return None
    try:
        return BacnetIAm(obj["instance"], int(vals[1][1]), int(vals[2][1]), int(vals[3][1]), source)
    except (TypeError, ValueError, KeyError):
        return None


def diagnose_bacnet_packet(packet: bytes) -> dict[str, Any]:
    """Decode BACnet/IP envelope fields and explain why a datagram is not I-Am."""
    result: dict[str, Any] = {"bvlc_type": None, "bvlc_function": None,
                              "bvlc_length": None, "npdu_version": None,
                              "npdu_control": None, "apdu_type": None,
                              "apdu_service": None, "reason": None}
    if len(packet) < 4:
        result["reason"] = "UDP datagram shorter than BVLC header"
        return result
    result["bvlc_type"] = f"0x{packet[0]:02X}"
    result["bvlc_function"] = f"0x{packet[1]:02X}"
    result["bvlc_length"] = int.from_bytes(packet[2:4], "big")
    if packet[0] != 0x81:
        result["reason"] = "BVLC type is not BACnet/IPv4 (0x81)"
        return result
    if result["bvlc_length"] != len(packet):
        result["reason"] = f"BVLC length mismatch: header={result['bvlc_length']}, UDP={len(packet)}"
        return result
    function = packet[1]
    if function in (0x0A, 0x0B):
        pos = 4
    elif function == 0x04:
        if len(packet) < 10:
            result["reason"] = "Truncated BVLC Forwarded-NPDU origin address"
            return result
        result["forwarded_from"] = f"{socket.inet_ntoa(packet[4:8])}:{int.from_bytes(packet[8:10], 'big')}"
        pos = 10
    else:
        result["reason"] = f"Unsupported BVLC function 0x{function:02X} for I-Am parsing"
        return result
    try:
        pos, npdu_fields = _parse_npdu_header(packet, pos)
        result.update(npdu_fields)
    except BacnetProtocolError as exc:
        result["reason"] = str(exc)
        return result
    if pos >= len(packet):
        result["reason"] = "NPDU has no APDU payload"
        return result
    result["apdu_type"] = f"0x{packet[pos]:02X}"
    if packet[pos] == 0x10 and pos + 1 < len(packet):
        result["apdu_service"] = f"0x{packet[pos+1]:02X}"
        if packet[pos+1] != 0x00:
            result["reason"] = "Unconfirmed request is not I-Am (service choice is not 0x00)"
        else:
            result["reason"] = "I-Am APDU envelope detected; application payload validation required"
    else:
        result["reason"] = "APDU is not an unconfirmed I-Am request"
    return result

def _unsigned_app(value: int) -> bytes:
    n = max(1, (value.bit_length() + 7) // 8)
    raw = value.to_bytes(n, "big")
    return bytes([(2 << 4) | n]) + raw


def _context_tag(number: int, raw: bytes) -> bytes:
    n = len(raw)
    if n <= 4:
        return bytes([(number << 4) | 0x08 | n]) + raw
    if n <= 253:
        return bytes([(number << 4) | 0x08 | 5, n]) + raw
    raise ValueError("context value too large")


def _object_id(object_type: int, instance: int) -> bytes:
    if not 0 <= object_type <= 1023 or not 0 <= instance <= 0x3fffff:
        raise ValueError("invalid BACnet object identifier")
    return ((object_type << 22) | instance).to_bytes(4, "big")


def _bvll(apdu: bytes, function: int) -> bytes:
    npdu = b"\x01\x00" + apdu
    body = bytes([0x81, function]) + (len(npdu) + 4).to_bytes(2, "big") + npdu
    return body


class BacnetIpClient:
    """Explicitly-started, read-only BACnet/IP client. No control services exist."""
    def __init__(self, config: BacnetIpNetworkConfig, policy: DiscoveryPolicy | None = None, identity_resolver: DeviceIdentityResolver | None = None):
        self.config = config
        self.policy = policy or DiscoveryPolicy()
        self.identity_resolver = identity_resolver or DeviceIdentityResolver()
        if self.policy.allow_writes or self.policy.allow_reboot or self.policy.allow_configuration_changes:
            raise ValueError("BACnet discovery client only supports read-only policy")
        self._socket: socket.socket | None = None
        self._invoke_id = 1
        self._io_lock = threading.RLock()
        self.last_discovery_diagnostics: dict[str, Any] = {
            "interface_name": config.interface_name,
            "local_endpoint": f"{config.local_address}:{config.udp_port}",
            "broadcast_endpoint": None,
            "request_bytes": 0,
            "received_udp_packets": 0,
            "valid_iam_packets": 0,
            "ignored_packets": 0,
            "self_packets": 0,
            "packet_details": [],
        }

    def __enter__(self) -> "BacnetIpClient":
        self.open(); return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @_serialized_io
    def open(self) -> None:
        if self._socket is not None: return
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        try:
            # Do not share BACnet's well-known UDP port with another local process.
            # On Windows this makes a competing BDT/other BACnet process fail clearly
            # instead of creating ambiguous delivery between two sockets.
            exclusive = getattr(socket, "SO_EXCLUSIVEADDRUSE", None)
            if exclusive is not None:
                sock.setsockopt(socket.SOL_SOCKET, exclusive, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.bind((self.config.local_address, self.config.udp_port))
        except Exception:
            sock.close()
            raise
        self._socket = sock
        endpoint = sock.getsockname() if hasattr(sock, "getsockname") else (self.config.local_address, self.config.udp_port)
        self.last_discovery_diagnostics["local_endpoint"] = f"{endpoint[0]}:{endpoint[1]}"

    @_serialized_io
    def close(self) -> None:
        if self._socket is not None:
            self._socket.close(); self._socket = None

    @_serialized_io
    def discover(self, timeout_seconds: float | None = None, low_limit: int | None = None, high_limit: int | None = None) -> list[BacnetIAm]:
        """Broadcast Who-Is on the configured IPv4 subnet and collect I-Am replies."""
        if self._socket is None: self.open()
        assert self._socket is not None
        if low_limit is not None and not 0 <= low_limit <= 4_194_302: raise ValueError("invalid low_limit")
        if high_limit is not None and not 0 <= high_limit <= 4_194_302: raise ValueError("invalid high_limit")
        if low_limit is not None and high_limit is not None and low_limit > high_limit: raise ValueError("low_limit exceeds high_limit")
        payload = b""
        if low_limit is not None: payload += _context_tag(0, _unsigned_app(low_limit)[1:])
        if high_limit is not None: payload += _context_tag(1, _unsigned_app(high_limit)[1:])
        request = _bvll(b"\x10\x08" + payload, 0x0B)
        net = ipaddress.ip_network(self.config.subnet_cidr, strict=False)
        target = (str(net.broadcast_address), self.config.udp_port)
        sent = self._socket.sendto(request, target)
        self.last_discovery_diagnostics.update({
            "interface_name": self.config.interface_name,
            "local_endpoint": f"{self.config.local_address}:{self.config.udp_port}",
            "broadcast_endpoint": f"{target[0]}:{target[1]}",
            "request_bytes": sent if isinstance(sent, int) else len(request),
            "received_udp_packets": 0,
            "valid_iam_packets": 0,
            "ignored_packets": 0,
            "self_packets": 0,
            "packet_details": [],
        })
        deadline = time.monotonic() + (timeout_seconds or self.policy.request_timeout_seconds)
        found: dict[tuple[str, int], BacnetIAm] = {}
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0: break
            self._socket.settimeout(remaining)
            try: packet, source = self._socket.recvfrom(65535)
            except socket.timeout: break
            self.last_discovery_diagnostics["received_udp_packets"] += 1
            # Windows may deliver the broadcast request back to the same bound
            # socket. It is diagnostic traffic from AVIC, not a device response.
            is_self_request = (
                packet == request
                and source[0] == self.config.local_address
                and source[1] == self.config.udp_port
            )
            parse_error = None
            iam = None
            if is_self_request:
                self.last_discovery_diagnostics["self_packets"] += 1
            else:
                try:
                    iam = parse_iam(packet, source)
                except (BacnetProtocolError, ValueError, IndexError, struct.error) as exc:
                    parse_error = f"{type(exc).__name__}: {exc}"
            details = self.last_discovery_diagnostics["packet_details"]
            if len(details) < 100:
                envelope = diagnose_bacnet_packet(packet)
                classification = "SELF_REQUEST" if is_self_request else ("I-AM" if iam is not None else "UNRECOGNIZED")
                reason = ("Собственный Who-Is запрос AVIC; не является ответом контроллера"
                          if is_self_request else (parse_error or ("I-Am parsed" if iam is not None else envelope.get("reason"))))
                details.append({
                    "source_ip": source[0], "source_port": source[1],
                    "length": len(packet), "hex": packet.hex(" ").upper(),
                    "classification": classification,
                    "parse_error": parse_error,
                    "decode": envelope,
                    "reason": reason,
                })
            if is_self_request:
                continue
            if iam is None:
                self.last_discovery_diagnostics["ignored_packets"] += 1
                continue
            if low_limit is not None and iam.device_instance < low_limit: continue
            if high_limit is not None and iam.device_instance > high_limit: continue
            self.last_discovery_diagnostics["valid_iam_packets"] += 1
            found[(source[0], iam.device_instance)] = iam
        self.last_discovery_diagnostics["devices_found"] = len(found)
        return sorted(found.values(), key=lambda x: (x.device_instance, x.source[0]))

    def discover_devices(self, timeout_seconds: float | None = None) -> list[DiscoveredDevice]:
        devices = []
        for iam in self.discover(timeout_seconds):
            identity = self.identity_resolver.resolve(protocol="bacnet/ip", vendor_id=iam.vendor_id)
            devices.append(DiscoveredDevice(protocol="bacnet/ip", network_id=self.config.network_id,
                address=f"{iam.source[0]}:{iam.source[1]}", device_instance=iam.device_instance,
                vendor_id=iam.vendor_id, vendor_name=identity.manufacturer, reachable=True,
                native_identity=f"bacnet:device:{iam.device_instance}",
                metadata={"max_apdu": iam.max_apdu, "segmentation": iam.segmentation,
                          "identity": {"manufacturer": identity.manufacturer,
                                       "model": identity.model,
                                       "manufacturer_source": identity.manufacturer_source,
                                       "model_source": identity.model_source,
                                       "confidence": identity.confidence.value}}))
        return devices

    @_serialized_io
    def read_property(self, address: tuple[str, int], device_instance: int, object_type: int,
                      object_instance: int, property_id: int, timeout_seconds: float | None = None,
                      array_index: int | None = None) -> Any:
        """Issue confirmed ReadProperty and decode the first application value."""
        if self._socket is None: self.open()
        assert self._socket is not None
        invoke = self._invoke_id; self._invoke_id = (self._invoke_id % 255) + 1
        body = bytes([0x00, 0x05, invoke, 0x0C]) + _context_tag(0, _object_id(object_type, object_instance)) + _context_tag(1, property_id.to_bytes(1 if property_id < 256 else 2, "big"))
        if array_index is not None:
            if not 0 <= array_index <= 0xFFFFFFFF:
                raise ValueError("array_index must be between 0 and 4294967295")
            body += _context_tag(2, array_index.to_bytes(max(1, (array_index.bit_length()+7)//8), "big"))
        self._socket.sendto(_bvll(body, 0x0A), address)
        self._socket.settimeout(timeout_seconds or self.policy.request_timeout_seconds)
        deadline = time.monotonic() + (timeout_seconds or self.policy.request_timeout_seconds)
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0: raise TimeoutError("BACnet ReadProperty timeout")
            self._socket.settimeout(remaining)
            packet, source = self._socket.recvfrom(65535)
            if source != address or len(packet) < 12 or packet[0] != 0x81: continue
            if packet[1] not in (0x0A, 0x0B):
                continue
            try:
                pos, _npdu_fields = _parse_npdu_header(packet, 4)
            except BacnetProtocolError:
                continue
            apdu = packet[pos:]
            if len(apdu) < 3: continue
            if apdu[0] == 0x38 and apdu[1] == invoke:
                raise BacnetProtocolError("segmented ReadProperty ComplexACK is not supported by this transport profile")
            if apdu[0] == 0x30 and apdu[1] == invoke:  # ComplexACK
                if apdu[2] != 0x0C: continue
                # Return raw application values inside opening/closing context tag 3.
                data = apdu[3:]
                start = next((i+1 for i,b in enumerate(data) if b == 0x3E), None)
                if start is None: raise BacnetProtocolError("ReadProperty ACK missing value opening tag")
                end = data.find(b"\x3f", start)
                if end < 0: raise BacnetProtocolError("ReadProperty ACK missing value closing tag")
                values = _application_values(data[start:end])
                return values[0][1] if len(values) == 1 else [v for _,v in values]
            if apdu[0] == 0x50 and apdu[1] == invoke:
                raise BacnetProtocolError(f"BACnet Error response: {apdu[2:].hex()}")
            if apdu[0] == 0x70 and apdu[1] == invoke:
                raise BacnetProtocolError(f"BACnet Reject response: {apdu[2:].hex()}")


    @_serialized_io
    def read_object_list(self, address: tuple[str, int], device_instance: int,
                         timeout_seconds: float | None = None, max_objects: int = 4096) -> list[BacnetObjectIdentifier]:
        """Read Device.Object_List using BACnet array-index reads (index 0 = item count).

        The cap prevents a malformed or unexpected device response from causing an
        unbounded request loop. Every request is read-only.
        """
        if not 1 <= max_objects <= 100_000:
            raise ValueError("max_objects must be between 1 and 100000")
        count = self.read_property(address, device_instance, 8, device_instance, 76,
                                   timeout_seconds=timeout_seconds, array_index=0)
        if not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= max_objects:
            raise BacnetProtocolError(f"invalid or excessive Object_List count: {count!r}")
        objects: list[BacnetObjectIdentifier] = []
        for index in range(1, count + 1):
            value = self.read_property(address, device_instance, 8, device_instance, 76,
                                       timeout_seconds=timeout_seconds, array_index=index)
            if not isinstance(value, dict) or not {"object_type", "instance"}.issubset(value):
                raise BacnetProtocolError(f"invalid Object_List item at index {index}: {value!r}")
            objects.append(BacnetObjectIdentifier(int(value["object_type"]), int(value["instance"])))
        return objects

    @_serialized_io
    def read_object_name(self, address: tuple[str, int], device_instance: int,
                         obj: BacnetObjectIdentifier, timeout_seconds: float | None = None) -> str | None:
        """Read Object_Name for one object; unsupported properties remain explicit errors."""
        value = self.read_property(address, device_instance, obj.object_type, obj.instance, 77, timeout_seconds)
        return value if isinstance(value, str) else None

    @_serialized_io
    def read_device_identity(self, address: tuple[str, int], device_instance: int) -> dict[str, Any]:
        """Read standard Device object identity properties; unsupported properties are reported, not hidden."""
        props = {"object_name": 77, "vendor_id": 118, "vendor_name": 119,
                 "model_name": 70, "firmware_revision": 44}
        result: dict[str, Any] = {"device_instance": device_instance}
        for name, property_id in props.items():
            try:
                result[name] = self.read_property(address, device_instance, 8, device_instance, property_id)
            except (TimeoutError, BacnetProtocolError) as exc:
                result[name] = None
                result.setdefault("property_errors", {})[name] = str(exc)
        return result
