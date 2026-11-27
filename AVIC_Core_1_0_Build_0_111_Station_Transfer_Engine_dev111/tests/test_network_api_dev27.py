from types import SimpleNamespace
from fastapi.testclient import TestClient
import avic_core.ui.app as ui_app
from avic_core.ui import create_ui_app


def test_bacnet_discovery_is_explicit_and_read_only(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, config, policy):
            assert config.udp_port == 47808
            assert policy.allow_writes is False
            self.last_discovery_diagnostics = {"received_udp_packets": 1, "valid_iam_packets": 1}
        def __enter__(self): return self
        def __exit__(self, *_): pass
        def discover(self, timeout, low, high):
            return [SimpleNamespace(device_instance=1001, source=("192.168.1.50", 47808),
                                    max_apdu=1476, segmentation=3, vendor_id=5)]
    monkeypatch.setattr(ui_app, "BacnetIpClient", FakeClient)
    monkeypatch.setattr(ui_app, "get_interface", lambda name: {"id": "Ethernet", "name": "Ethernet", "ipv4": "192.168.1.10", "subnet_cidr": "192.168.1.0/24", "mac": "00:11:22:33:44:55"})
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.post("/api/network/bacnet/discover", json={
        "network_id": "lan1", "interface_id": "Ethernet"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["write_enabled"] is False
    assert data["devices"][0]["device_instance"] == 1001
    assert data["diagnostics"]["valid_iam_packets"] == 1


def test_modbus_api_performs_single_read_only_request(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, host, port, unit_id, timeout):
            assert host == "192.168.1.20"
        def read_holding_registers(self, address, count):
            assert (address, count) == (20, 1)
            return [321]
    monkeypatch.setattr(ui_app, "ModbusTcpClient", FakeClient)
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.post("/api/network/modbus/read", json={
        "host": "192.168.1.20", "address": 20, "count": 1, "function": 3,
        "data_type": "uint16"
    })
    assert response.status_code == 200
    assert response.json()["registers"] == [321]
    assert response.json()["decoded_value"] == 321
    assert response.json()["write_enabled"] is False


def test_network_interfaces_endpoint_returns_detected_adapters(monkeypatch, tmp_path):
    monkeypatch.setattr(ui_app, "list_ipv4_interfaces", lambda: [{"id": "Ethernet", "name": "Ethernet", "ipv4": "10.10.10.100", "subnet_cidr": "10.10.10.0/24", "broadcast": "10.10.10.255", "recommended": True}])
    response = TestClient(create_ui_app(data_dir=str(tmp_path))).get("/api/network/interfaces")
    assert response.status_code == 200
    assert response.json()["interfaces"][0]["ipv4"] == "10.10.10.100"


def test_driver_catalog_api_exposes_runtime_integration_without_overstating_readiness(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/api/drivers/catalog")
    assert response.status_code == 200
    payload = response.json()
    assert payload["field_io_enabled"] is False
    drivers = {item["driver_id"]: item for item in payload["drivers"]}
    assert len(drivers) == 16
    assert drivers["modbus-tcp"]["runtime_start_supported"] is True
    assert drivers["bacnet-ip"]["runtime_start_supported"] is True
    assert drivers["knxnet-ip"]["runtime_start_supported"] is True
    assert drivers["mqtt"]["runtime_start_supported"] is True
    assert drivers["s7comm"]["runtime_start_supported"] is False
    assert drivers["opc-ua-client"]["runtime_start_supported"] is False
    assert all(item["write_supported"] is False for item in drivers.values())
