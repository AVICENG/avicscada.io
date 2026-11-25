import pytest

from avic_core.network import (
    BacnetIpNetworkConfig, DiscoveryMode, DiscoveryPolicy, DiscoveredDevice,
    DiscoveredPoint, PointImportPreview,
)


def test_bacnet_ip_config_defaults_and_validates_subnet():
    cfg = BacnetIpNetworkConfig("plant-net", "Ethernet", "192.168.10.20", "192.168.10.0/24")
    assert cfg.udp_port == 47808
    assert cfg.device_instance is None


def test_bacnet_ip_rejects_address_outside_subnet():
    with pytest.raises(ValueError, match="belong"):
        BacnetIpNetworkConfig("n", "eth0", "192.168.2.10", "192.168.1.0/24")


def test_bacnet_ip_validates_bbmd_foreign_registration():
    with pytest.raises(ValueError, match="BBMD"):
        BacnetIpNetworkConfig("n", "eth0", "10.0.0.2", "10.0.0.0/24", foreign_device_ttl_seconds=60)
    cfg = BacnetIpNetworkConfig("n", "eth0", "10.0.0.2", "10.0.0.0/24", bbmd_address="10.0.0.1", foreign_device_ttl_seconds=60)
    assert cfg.bbmd_address == "10.0.0.1"


def test_discovery_policy_is_read_only_by_default():
    policy = DiscoveryPolicy()
    assert policy.mode == DiscoveryMode.SAFE_READ_ONLY
    assert policy.allow_writes is False
    assert policy.allow_reboot is False


def test_discovery_policy_rejects_control_capabilities():
    with pytest.raises(ValueError, match="read-only"):
        DiscoveryPolicy(allow_writes=True)


def test_device_and_point_preserve_native_identity():
    device = DiscoveredDevice("bacnet/ip", "plant-net", "192.168.10.30", 1234, 5, "Trend", "IQ3", native_identity="device:1234")
    point = DiscoveredPoint("device:1234", "analog-input", 1, "Supply Air Temp", units="degrees-celsius", native_identity="AI:1")
    assert device.model_name == "IQ3"
    assert point.stable_key == "device:1234|analog-input|1"
    assert point.native_identity == "AI:1"


def test_point_import_preview_detects_existing_and_in_batch_duplicates():
    a = DiscoveredPoint("d1", "analog-input", 1, "SAT")
    b = DiscoveredPoint("d1", "analog-input", 2, "RAT")
    preview = PointImportPreview.build([a, b, a], existing_keys={b.stable_key})
    assert preview.discovered_count == 3
    assert preview.new_points == (a,)
    assert preview.duplicate_keys == (a.stable_key, b.stable_key)


def test_interface_kind_excludes_vpn_from_physical_recommendation():
    from avic_core.network.interfaces import _interface_kind
    assert _interface_kind("AdGuard VPN") == "vpn"
    assert _interface_kind("Ethernet") == "ethernet"
    assert _interface_kind("Беспроводная сеть Wi-Fi") == "wifi"
    assert _interface_kind("VMware Network Adapter") == "virtual"
