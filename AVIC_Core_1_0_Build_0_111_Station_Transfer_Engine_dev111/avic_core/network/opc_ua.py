"""Strict, read-only OPC UA connection and NodeId contracts.

Transport is intentionally not advertised until the native open62541 worker
is integrated and passes independent-server acceptance.
"""
from __future__ import annotations

import base64
from dataclasses import dataclass
import math
import re
from urllib.parse import urlsplit


_SECURE_POLICIES = {
    "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256",
    "http://opcfoundation.org/UA/SecurityPolicy#Aes128_Sha256_RsaOaep",
    "http://opcfoundation.org/UA/SecurityPolicy#Aes256_Sha256_RsaPss",
}
_NODE_ID_RE = re.compile(r"^ns=(0|[1-9][0-9]*);([isgb])=(.*)$", re.DOTALL)


@dataclass(frozen=True, slots=True)
class OpcUaNetworkConfig:
    endpoint_url: str
    application_uri: str
    client_certificate_path: str
    client_private_key_ref: str
    trust_store_path: str
    security_policy_uri: str = "http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256"
    security_mode: str = "SignAndEncrypt"
    timeout_seconds: float = 5.0
    max_message_size: int = 4 * 1024 * 1024
    max_chunk_count: int = 64

    def __post_init__(self) -> None:
        parsed = urlsplit(self.endpoint_url)
        if parsed.scheme.lower() != "opc.tcp" or not parsed.hostname:
            raise ValueError("endpoint_url must be an opc.tcp:// endpoint")
        if parsed.username is not None or parsed.password is not None:
            raise ValueError("OPC UA endpoint URL must not contain credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("OPC UA endpoint URL must not contain query or fragment")
        try:
            port = parsed.port
        except ValueError as exc:
            raise ValueError("OPC UA endpoint has an invalid port") from exc
        if port is None or not 1 <= port <= 65535:
            raise ValueError("OPC UA endpoint port must be between 1 and 65535")
        if self.security_mode not in {"Sign", "SignAndEncrypt"}:
            raise ValueError("OPC UA security mode must be Sign or SignAndEncrypt; None is forbidden")
        if self.security_policy_uri not in _SECURE_POLICIES:
            raise ValueError("OPC UA security policy is not in the approved secure policy set")
        for name, value in (
            ("application_uri", self.application_uri),
            ("client_certificate_path", self.client_certificate_path),
            ("client_private_key_ref", self.client_private_key_ref),
            ("trust_store_path", self.trust_store_path),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not self.application_uri.startswith("urn:"):
            raise ValueError("application_uri must be a stable URN")
        if not math.isfinite(float(self.timeout_seconds)) or not 0.1 <= self.timeout_seconds <= 60:
            raise ValueError("timeout_seconds must be between 0.1 and 60")
        if isinstance(self.max_message_size, bool) or not 8192 <= self.max_message_size <= 64 * 1024 * 1024:
            raise ValueError("max_message_size must be between 8192 and 67108864")
        if isinstance(self.max_chunk_count, bool) or not 1 <= self.max_chunk_count <= 4096:
            raise ValueError("max_chunk_count must be between 1 and 4096")


@dataclass(frozen=True, slots=True)
class OpcUaNodeId:
    namespace_index: int
    identifier_type: str
    identifier: int | str

    @property
    def canonical(self) -> str:
        return f"ns={self.namespace_index};{self.identifier_type}={self.identifier}"


def parse_node_id(value: str) -> OpcUaNodeId:
    """Parse the explicit OPC UA NodeId text form without guessing namespaces."""
    if not isinstance(value, str):
        raise TypeError("NodeId must be a string")
    match = _NODE_ID_RE.fullmatch(value.strip())
    if not match:
        raise ValueError("NodeId must use ns=<index>;<i|s|g|b>=<identifier>")
    namespace = int(match.group(1))
    if namespace > 65535:
        raise ValueError("NodeId namespace index must be between 0 and 65535")
    kind, raw = match.group(2), match.group(3)
    if not raw:
        raise ValueError("NodeId identifier must not be empty")
    if kind == "i":
        if not re.fullmatch(r"0|[1-9][0-9]*", raw):
            raise ValueError("numeric NodeId must be an unsigned decimal integer")
        number = int(raw)
        if number > 0xFFFFFFFF:
            raise ValueError("numeric NodeId exceeds UInt32")
        identifier: int | str = number
    elif kind == "g":
        import uuid
        try:
            identifier = str(uuid.UUID(raw))
        except (ValueError, AttributeError) as exc:
            raise ValueError("guid NodeId must contain a valid UUID") from exc
    elif kind == "b":
        try:
            decoded = base64.b64decode(raw, validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("byte-string NodeId must contain valid base64") from exc
        if not decoded:
            raise ValueError("byte-string NodeId must not be empty")
        identifier = base64.b64encode(decoded).decode("ascii")
    else:
        if any(ord(char) < 0x20 for char in raw):
            raise ValueError("string NodeId contains a control character")
        identifier = raw
    return OpcUaNodeId(namespace, kind, identifier)


@dataclass(frozen=True, slots=True)
class OpcUaNodeBinding:
    point_id: str
    node_id: str
    data_type: str = "auto"
    scale: float = 1.0
    offset: float = 0.0
    access: str = "read"

    def __post_init__(self) -> None:
        if not isinstance(self.point_id, str) or not self.point_id.strip():
            raise ValueError("point_id is required")
        parse_node_id(self.node_id)
        if self.data_type not in {
            "auto", "boolean", "int16", "uint16", "int32", "uint32",
            "int64", "uint64", "float", "double", "string", "datetime",
        }:
            raise ValueError("unsupported OPC UA binding data_type")
        if self.access != "read":
            raise ValueError("OPC UA point bindings are read-only; writes require Command Gateway")
        if not math.isfinite(float(self.scale)) or not math.isfinite(float(self.offset)):
            raise ValueError("OPC UA scale and offset must be finite")
        if self.data_type in {"boolean", "string", "datetime", "auto"} and (
            float(self.scale) != 1.0 or float(self.offset) != 0.0
        ):
            raise ValueError("scale/offset is only valid for explicitly numeric OPC UA data types")
