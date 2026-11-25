from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

import avic_core.ui.app as ui_app
from avic_core.network import NetworkPlan, assess_deployment_binding
from avic_core.ui import create_ui_app


def test_manual_network_plan_accepts_future_dispatch_host():
    plan = NetworkPlan("BMS LAN", "192.168.10.0/24", "192.168.10.20",
                       "192.168.10.1", ("192.168.10.1", "1.1.1.1"))
    assert plan.as_dict() == {
        "name": "BMS LAN", "addressing_mode": "manual", "station_ipv4": "192.168.10.20",
        "subnet_cidr": "192.168.10.0/24", "gateway_ipv4": "192.168.10.1",
        "dns_servers": ["192.168.10.1", "1.1.1.1"],
    }


@pytest.mark.parametrize("station,subnet,gateway", [
    ("192.168.20.20", "192.168.10.0/24", "192.168.10.1"),
    ("192.168.10.20", "192.168.10.0/24", "192.168.20.1"),
    ("192.168.10.1", "192.168.10.0/24", "192.168.10.1"),
])
def test_network_plan_rejects_invalid_station_or_gateway(station, subnet, gateway):
    with pytest.raises(ValueError):
        NetworkPlan("LAN", subnet, station, gateway)


def test_deployment_binding_distinguishes_exact_ip_subnet_and_not_present():
    plan = NetworkPlan("LAN", "10.20.0.0/24", "10.20.0.15")
    exact = assess_deployment_binding(plan, [{"id": "eth0", "name": "Ethernet", "ipv4": "10.20.0.15", "subnet_cidr": "10.20.0.0/24"}])
    mismatch = assess_deployment_binding(plan, [{"id": "eth1", "name": "Ethernet 2", "ipv4": "10.20.0.16", "subnet_cidr": "10.20.0.0/24"}])
    absent = assess_deployment_binding(plan, [{"id": "wifi", "name": "Wi-Fi", "ipv4": "192.168.1.10", "subnet_cidr": "192.168.1.0/24"}])
    assert exact["status"] == "BOUND" and exact["exact_binding"] is True
    assert mismatch["status"] == "SUBNET_PRESENT_ADDRESS_MISMATCH"
    assert absent["status"] == "PLANNED_NOT_PRESENT"
    assert all(x["configuration_changed"] is False for x in (exact, mismatch, absent))


def _create_station(client: TestClient) -> str:
    project = client.post("/api/projects", json={"name": "Объект DEV92"})
    assert project.status_code == 201, project.text
    station = client.post("/api/stations", json={"project_id": project.json()["id"], "name": "Main Station"})
    assert station.status_code == 201, station.text
    return station.json()["id"]


def test_manual_network_api_persists_plan_without_local_interface(monkeypatch, tmp_path):
    monkeypatch.setattr(ui_app, "list_ipv4_interfaces", lambda: [])
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station_id = _create_station(client)
    response = client.post(f"/api/stations/{station_id}/networks", json={
        "station_id": station_id, "name": "BMS LAN", "addressing_mode": "manual",
        "station_ipv4": "192.168.10.20", "subnet_cidr": "192.168.10.0/24",
        "gateway_ipv4": "192.168.10.1", "dns_servers": ["192.168.10.1"],
    })
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["addressing_mode"] == "manual"
    assert data["station_ipv4"] == "192.168.10.20"
    assert data["interface_id"] == ""
    assert data["deployment_binding"] == "PLANNED_NOT_PRESENT"


def test_manual_network_api_rejects_gateway_outside_subnet(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station_id = _create_station(client)
    response = client.post(f"/api/stations/{station_id}/networks", json={
        "station_id": station_id, "name": "Bad LAN", "addressing_mode": "manual",
        "station_ipv4": "192.168.10.20", "subnet_cidr": "192.168.10.0/24",
        "gateway_ipv4": "192.168.20.1",
    })
    assert response.status_code == 400


def test_deployment_check_reports_planned_not_present(monkeypatch, tmp_path):
    monkeypatch.setattr(ui_app, "list_ipv4_interfaces", lambda: [{
        "id": "eth0", "name": "Ethernet", "ipv4": "10.0.0.10", "subnet_cidr": "10.0.0.0/24"
    }])
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station_id = _create_station(client)
    created = client.post(f"/api/stations/{station_id}/networks", json={
        "station_id": station_id, "name": "BMS LAN", "addressing_mode": "manual",
        "station_ipv4": "192.168.10.20", "subnet_cidr": "192.168.10.0/24",
    }).json()
    result = client.get(f"/api/network/{created['id']}/deployment-check")
    assert result.status_code == 200, result.text
    assert result.json()["status"] == "PLANNED_NOT_PRESENT"
    assert result.json()["configuration_changed"] is False


def test_ping_api_is_explicit_and_bounded(monkeypatch, tmp_path):
    monkeypatch.setattr(ui_app, "ping_ipv4", lambda address, timeout: {
        "address": address, "reachable": True, "status": "REACHABLE", "rtt_ms": 1.2,
        "configuration_changed": False,
    })
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    result = client.post("/api/network/ping", json={"address": "192.168.10.50", "timeout_seconds": 1.5})
    assert result.status_code == 200
    assert result.json()["reachable"] is True
    assert result.json()["configuration_changed"] is False
    invalid = client.post("/api/network/ping", json={"address": "192.168.10.50", "timeout_seconds": 30})
    assert invalid.status_code == 422


def test_bacnet_unicast_inspection_can_target_routed_ipv4(monkeypatch, tmp_path):
    class FakeClient:
        def __init__(self, config, policy):
            assert config.local_address == "192.168.10.20"
            assert policy.allow_writes is False
        def __enter__(self): return self
        def __exit__(self, *_): pass

    class FakeInspector:
        def __init__(self, client):
            pass
        def inspect(self, endpoint, device_instance, max_objects):
            assert endpoint == ("192.168.20.50", 47808)
            assert device_instance == 100
            return type("Inspection", (), {
                "device_identity": {"vendor_id": 5, "vendor_name": "Trend", "model_name": "IQ3",
                                    "firmware_revision": None, "property_errors": {}},
                "objects": [], "point_snapshots": [], "warnings": [],
            })()

    monkeypatch.setattr(ui_app, "get_interface", lambda _id: {
        "id": "Ethernet", "name": "Ethernet", "ipv4": "192.168.10.20",
        "subnet_cidr": "192.168.10.0/24", "mac": "00:11:22:33:44:55",
    })
    monkeypatch.setattr(ui_app, "BacnetIpClient", FakeClient)
    monkeypatch.setattr(ui_app, "BacnetDeviceInspector", FakeInspector)
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.post("/api/network/bacnet/inspect", json={
        "network_id": "plant-lan", "interface_id": "Ethernet", "address": "192.168.20.50",
        "device_instance": 100,
    })
    assert response.status_code == 200, response.text
    assert response.json()["address_scope"] == "routed_unicast"
    assert response.json()["write_enabled"] is False


def test_auto_network_creation_still_binds_detected_interface(monkeypatch, tmp_path):
    monkeypatch.setattr(ui_app, "get_interface", lambda _id: {
        "id": "Ethernet", "name": "Ethernet", "ipv4": "192.168.10.20",
        "subnet_cidr": "192.168.10.0/24", "mac": "00:11:22:33:44:55",
    })
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    station_id = _create_station(client)
    response = client.post(f"/api/stations/{station_id}/networks", json={
        "station_id": station_id, "name": "Auto LAN", "addressing_mode": "auto", "interface_id": "Ethernet",
    })
    assert response.status_code == 201, response.text
    assert response.json()["interface_id"] == "Ethernet"
    assert response.json()["station_ipv4"] == "192.168.10.20"
    assert response.json()["deployment_binding"] == "BOUND"
