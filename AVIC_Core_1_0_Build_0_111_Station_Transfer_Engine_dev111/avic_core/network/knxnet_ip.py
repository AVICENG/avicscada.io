"""Strict KNXnet/IP packet primitives and common KNX DPT decoders."""
from __future__ import annotations
import ipaddress, math, struct
from dataclasses import dataclass

class KnxProtocolError(ValueError): pass

HEADER_SIZE=6
VERSION=0x10
CONNECT_REQ=0x0205
CONNECT_RES=0x0206
TUNNELING_ACK=0x0421
HOST_PROTOCOL_UDP_IPV4=0x01
CONNECTION_TYPE_TUNNEL=0x04
KNX_LAYER_LINK=0x02

@dataclass(frozen=True, slots=True)
class KnxNetIpFrame:
    service_type:int
    payload:bytes

@dataclass(frozen=True, slots=True)
class KnxConnectResponse:
    channel_id:int
    status:int
    data_host:str|None
    data_port:int|None
    individual_address:int|None

@dataclass(frozen=True, slots=True)
class KnxTunnelingAck:
    channel_id:int
    sequence:int
    status:int

def encode_frame(service_type:int,payload:bytes)->bytes:
    if not 0<=service_type<=65535: raise ValueError("service_type must be uint16")
    total=HEADER_SIZE+len(payload)
    if total>65535: raise ValueError("KNXnet/IP frame too large")
    return struct.pack(">BBHH",6,VERSION,service_type,total)+payload

def decode_frame(packet:bytes)->KnxNetIpFrame:
    if len(packet)<6: raise KnxProtocolError("KNXnet/IP datagram shorter than header")
    hlen,version,service,length=struct.unpack(">BBHH",packet[:6])
    if hlen!=6 or version!=VERSION: raise KnxProtocolError("unsupported KNXnet/IP header")
    if length!=len(packet): raise KnxProtocolError(f"KNXnet/IP length mismatch: {length} != {len(packet)}")
    return KnxNetIpFrame(service,packet[6:])

def encode_hpai(host:str,port:int)->bytes:
    try: addr=ipaddress.IPv4Address(host).packed
    except ipaddress.AddressValueError as exc: raise ValueError("HPAI requires IPv4") from exc
    if not 1<=port<=65535: raise ValueError("UDP port out of range")
    return bytes((8,HOST_PROTOCOL_UDP_IPV4))+addr+struct.pack(">H",port)

def build_connect_request(local_host:str,local_port:int)->bytes:
    return encode_frame(CONNECT_REQ,encode_hpai(local_host,local_port)+bytes((4,CONNECTION_TYPE_TUNNEL,KNX_LAYER_LINK,0)))

def _hpai(data:bytes,pos:int):
    if pos+8>len(data): raise KnxProtocolError("truncated HPAI")
    if data[pos]!=8 or data[pos+1]!=HOST_PROTOCOL_UDP_IPV4: raise KnxProtocolError("unsupported HPAI")
    return str(ipaddress.IPv4Address(data[pos+2:pos+6])),int.from_bytes(data[pos+6:pos+8],"big"),pos+8

def parse_connect_response(packet:bytes)->KnxConnectResponse:
    f=decode_frame(packet)
    if f.service_type!=CONNECT_RES: raise KnxProtocolError("not CONNECT_RES")
    d=f.payload
    if len(d)<2: raise KnxProtocolError("truncated CONNECT_RES")
    channel,status=d[:2]
    if status: return KnxConnectResponse(channel,status,None,None,None)
    host,port,pos=_hpai(d,2)
    if pos+4!=len(d) or d[pos]!=4 or d[pos+1]!=CONNECTION_TYPE_TUNNEL:
        raise KnxProtocolError("invalid tunnelling CRD")
    return KnxConnectResponse(channel,status,host,port,int.from_bytes(d[pos+2:pos+4],"big"))

def build_tunneling_ack(channel_id:int,sequence:int,status:int=0)->bytes:
    if any(not 0<=x<=255 for x in (channel_id,sequence,status)): raise ValueError("ACK fields must be bytes")
    return encode_frame(TUNNELING_ACK,bytes((4,channel_id,sequence,status)))

def parse_tunneling_ack(packet:bytes)->KnxTunnelingAck:
    f=decode_frame(packet)
    if f.service_type!=TUNNELING_ACK or len(f.payload)!=4 or f.payload[0]!=4:
        raise KnxProtocolError("invalid TUNNELING_ACK")
    return KnxTunnelingAck(*f.payload[1:])

def parse_group_address(value:str|int,style:str="three_level")->int:
    if isinstance(value,bool): raise ValueError("boolean is not a group address")
    if isinstance(value,int):
        if not 0<=value<=65535: raise ValueError("group address out of range")
        return value
    try: p=[int(x) for x in value.strip().split("/")]
    except (ValueError,AttributeError) as exc: raise ValueError("invalid group address") from exc
    if style=="three_level" and len(p)==3:
        a,b,c=p
        if not(0<=a<=31 and 0<=b<=7 and 0<=c<=255): raise ValueError("3-level address component out of range")
        return (a<<11)|(b<<8)|c
    if style=="two_level" and len(p)==2:
        a,b=p
        if not(0<=a<=31 and 0<=b<=2047): raise ValueError("2-level address component out of range")
        return (a<<11)|b
    raise ValueError("group address does not match selected style")

def format_group_address(address:int,style:str="three_level")->str:
    if isinstance(address,bool) or not isinstance(address,int) or not 0<=address<=65535: raise ValueError("invalid group address")
    main=(address>>11)&31
    if style=="three_level": return f"{main}/{(address>>8)&7}/{address&255}"
    if style=="two_level": return f"{main}/{address&2047}"
    raise ValueError("style must be two_level or three_level")

def decode_datapoint(payload: bytes, datapoint_type: str):
    """Decode common KNX datapoint main types with strict payload validation.

    Supported DPTs: 1.xxx, 5.001/5.003/5.004, 6.001, 7.001, 8.001,
    9.001, 12.001, 13.001, 14.000, 16.000 and 17.001.
    """
    if not isinstance(payload, bytes):
        raise KnxProtocolError("KNX datapoint payload must be bytes")
    dpt = datapoint_type.strip().upper().replace("DPT-", "").replace("DPT", "")
    try:
        if dpt.startswith("1.") and len(dpt.split(".")) == 2:
            if len(payload) != 1 or payload[0] & 0xFE:
                raise KnxProtocolError("DPT 1.xxx requires a one-bit payload")
            return bool(payload[0] & 1)
        if dpt == "5.001":
            if len(payload) != 1: raise KnxProtocolError("DPT 5.001 requires one byte")
            return payload[0] * 100.0 / 255.0
        if dpt == "5.003":
            if len(payload) != 1: raise KnxProtocolError("DPT 5.003 requires one byte")
            return payload[0] * 360.0 / 255.0
        if dpt == "5.004":
            if len(payload) != 1: raise KnxProtocolError("DPT 5.004 requires one byte")
            return payload[0]
        if dpt == "6.001":
            if len(payload) != 1: raise KnxProtocolError("DPT 6.001 requires one byte")
            return int.from_bytes(payload, "big", signed=True)
        if dpt == "7.001":
            if len(payload) != 2: raise KnxProtocolError("DPT 7.001 requires two bytes")
            return int.from_bytes(payload, "big")
        if dpt == "8.001":
            if len(payload) != 2: raise KnxProtocolError("DPT 8.001 requires two bytes")
            return int.from_bytes(payload, "big", signed=True)
        if dpt == "9.001":
            if len(payload) != 2: raise KnxProtocolError("DPT 9.001 requires two bytes")
            raw = int.from_bytes(payload, "big")
            if raw == 0x7FFF: raise KnxProtocolError("DPT 9.001 invalid data pattern")
            mantissa = raw & 0x07FF
            if raw & 0x8000: mantissa -= 2048
            return 0.01 * mantissa * (2 ** ((raw >> 11) & 15))
        if dpt == "12.001":
            if len(payload) != 4: raise KnxProtocolError("DPT 12.001 requires four bytes")
            return int.from_bytes(payload, "big")
        if dpt == "13.001":
            if len(payload) != 4: raise KnxProtocolError("DPT 13.001 requires four bytes")
            return int.from_bytes(payload, "big", signed=True)
        if dpt == "14.000":
            if len(payload) != 4: raise KnxProtocolError("DPT 14.000 requires four bytes")
            value = struct.unpack(">f", payload)[0]
            if not math.isfinite(value): raise KnxProtocolError("DPT 14.000 value must be finite")
            return value
        if dpt == "16.000":
            if len(payload) != 14: raise KnxProtocolError("DPT 16.000 requires fourteen bytes")
            return payload.rstrip(b"\x00").decode("latin-1")
        if dpt == "17.001":
            if len(payload) != 1 or payload[0] & 0xC0:
                raise KnxProtocolError("DPT 17.001 requires reserved bits 7..6 to be zero")
            return payload[0] & 0x3F
        if dpt == "18.001":
            if len(payload) != 1 or payload[0] & 0x40:
                raise KnxProtocolError("DPT 18.001 requires reserved bit 6 to be zero")
            return {
                "command": "learn" if payload[0] & 0x80 else "activate",
                "scene_number": payload[0] & 0x3F,
            }
    except (OverflowError, struct.error) as exc:
        raise KnxProtocolError(f"invalid {dpt} payload") from exc
    raise KnxProtocolError(f"unsupported KNX datapoint type: {datapoint_type}")

__all__=["KnxProtocolError","KnxNetIpFrame","KnxConnectResponse","KnxTunnelingAck","encode_frame","decode_frame","encode_hpai","build_connect_request","parse_connect_response","build_tunneling_ack","parse_tunneling_ack","parse_group_address","format_group_address","decode_datapoint"]
