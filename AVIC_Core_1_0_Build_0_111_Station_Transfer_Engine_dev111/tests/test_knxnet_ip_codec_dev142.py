import math,struct
import pytest
from avic_core.network.knxnet_ip import *

def test_frame_roundtrip_and_length_validation():
    p=encode_frame(0x0205,b"abc"); assert decode_frame(p).payload==b"abc"
    with pytest.raises(KnxProtocolError): decode_frame(p[:-1])

def test_connect_request_hpai_and_cri():
    f=decode_frame(build_connect_request("192.0.2.10",3671))
    assert f.service_type==0x0205
    assert f.payload==bytes((8,1,192,0,2,10,0x0e,0x57,4,4,2,0))

def test_parse_connect_response_success_and_failure():
    ok=encode_frame(0x0206,bytes((2,0,8,1,192,0,2,20,0x0e,0x57,4,4,0x11,1)))
    r=parse_connect_response(ok)
    assert (r.channel_id,r.data_host,r.data_port,r.individual_address)==(2,"192.0.2.20",3671,0x1101)
    bad=parse_connect_response(encode_frame(0x0206,bytes((1,0x24))))
    assert bad.status==0x24 and bad.data_host is None

def test_tunneling_ack_roundtrip():
    a=parse_tunneling_ack(build_tunneling_ack(3,255))
    assert (a.channel_id,a.sequence,a.status)==(3,255,0)

@pytest.mark.parametrize("addr,value",[("1/2/3",0x0a03),("0/0/0",0),("31/7/255",0xffff)])
def test_three_level_group_address(addr,value):
    assert parse_group_address(addr)==value
    assert format_group_address(value)==addr

def test_two_level_group_address():
    x=parse_group_address("2/1000","two_level")
    assert format_group_address(x,"two_level")=="2/1000"

@pytest.mark.parametrize("addr",["32/0/0","1/8/0","1/0/256","1//2","1/2"])
def test_invalid_three_level_group_address(addr):
    with pytest.raises(ValueError): parse_group_address(addr)

def test_dpt_1_001():
    assert decode_datapoint(b"\x01","1.001") is True
    assert decode_datapoint(b"\x00","1.001") is False

def test_dpt_5_001():
    assert decode_datapoint(b"\xff","5.001")==100.0
    assert decode_datapoint(b"\x80","5.001")==pytest.approx(50.19607843)

def test_dpt_9_001_signed_temperature():
    assert decode_datapoint(bytes.fromhex("0c7e"),"9.001")==pytest.approx(23.0)
    assert decode_datapoint(bytes.fromhex("860c"),"9.001")==pytest.approx(-5.0)
    with pytest.raises(KnxProtocolError): decode_datapoint(bytes.fromhex("7fff"),"9.001")

def test_dpt_14_and_unknown_type():
    assert decode_datapoint(struct.pack(">f",21.5),"14.000")==pytest.approx(21.5)
    with pytest.raises(KnxProtocolError): decode_datapoint(struct.pack(">f",math.inf),"14.000")
    with pytest.raises(KnxProtocolError): decode_datapoint(b"\x01","9.999")

def test_invalid_connect_response_crd():
    p=encode_frame(0x0206,bytes((2,0,8,1,192,0,2,20,0x0e,0x57,3,4,0x11,1)))
    with pytest.raises(KnxProtocolError): parse_connect_response(p)
