import pytest
from avic_core.network import PhysicalMedium, PhysicalNetwork, ProtocolChannel, DeviceNetworkBinding


def test_one_ethernet_network_can_have_multiple_protocol_channels():
    net = PhysicalNetwork("lan1", "Building Ethernet", PhysicalMedium.ETHERNET)
    bacnet = ProtocolChannel("bacnet1", net.network_id, "BACnet/IP", "UDP", 47808)
    modbus = ProtocolChannel("modbus1", net.network_id, "Modbus TCP", "TCP", 502)
    assert bacnet.network_id == modbus.network_id == net.network_id


def test_device_binding_keeps_channel_identity():
    binding = DeviceNetworkBinding("meter-01", "modbus1", "192.168.1.30:502", "modbus:unit:1")
    assert binding.native_identity == "modbus:unit:1"


def test_invalid_protocol_channel_port_is_rejected():
    with pytest.raises(ValueError):
        ProtocolChannel("x", "lan1", "Modbus TCP", "TCP", 70000)
