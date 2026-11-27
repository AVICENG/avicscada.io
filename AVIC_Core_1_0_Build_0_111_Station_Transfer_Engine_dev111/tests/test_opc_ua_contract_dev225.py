import pytest

from avic_core.network.opc_ua import (
    OpcUaNetworkConfig, OpcUaNodeBinding, parse_node_id,
)


def _config(**overrides):
    values = {
        "endpoint_url": "opc.tcp://192.0.2.10:4840/UA/Plant",
        "application_uri": "urn:avic:station:client",
        "client_certificate_path": "certs/client.der",
        "client_private_key_ref": "secretstore://opcua/client-key",
        "trust_store_path": "certs/trusted",
    }
    values.update(overrides)
    return OpcUaNetworkConfig(**values)


@pytest.mark.parametrize("node_id,kind,identifier", [
    ("ns=0;i=2258", "i", 2258),
    ("ns=2;s=Plant.AHU-01.SupplyTemp", "s", "Plant.AHU-01.SupplyTemp"),
    ("ns=3;g=12345678-1234-5678-1234-567812345678", "g",
     "12345678-1234-5678-1234-567812345678"),
    ("ns=4;b=YWJj", "b", "YWJj"),
])
def test_parse_all_standard_nodeid_identifier_types(node_id, kind, identifier):
    parsed = parse_node_id(node_id)
    assert parsed.identifier_type == kind
    assert parsed.identifier == identifier
    assert parsed.canonical == node_id


@pytest.mark.parametrize("node_id", [
    "", "i=2258", "ns=-1;i=1", "ns=65536;i=1", "ns=1;i=-1",
    "ns=1;i=4294967296", "ns=1;g=not-a-guid", "ns=1;b=@@@",
    "ns=1;s=", "ns=1;s=bad\x00node",
])
def test_rejects_malformed_or_out_of_range_nodeids(node_id):
    with pytest.raises((ValueError, TypeError)):
        parse_node_id(node_id)


def test_secure_endpoint_defaults_and_bounds():
    config = _config()
    assert config.security_mode == "SignAndEncrypt"
    assert config.security_policy_uri.endswith("Basic256Sha256")
    assert config.max_message_size == 4 * 1024 * 1024


@pytest.mark.parametrize("endpoint", [
    "http://192.0.2.10:4840",
    "opc.tcp://",
    "opc.tcp://192.0.2.10",
    "opc.tcp://user:password@192.0.2.10:4840",
    "opc.tcp://192.0.2.10:99999",
    "opc.tcp://192.0.2.10:4840?token=x",
])
def test_rejects_unsafe_or_invalid_endpoint_url(endpoint):
    with pytest.raises(ValueError):
        _config(endpoint_url=endpoint)


def test_rejects_none_security_mode_and_unapproved_policy():
    with pytest.raises(ValueError, match="None is forbidden"):
        _config(security_mode="None")
    with pytest.raises(ValueError, match="approved secure"):
        _config(security_policy_uri="http://opcfoundation.org/UA/SecurityPolicy#None")


def test_rejects_missing_identity_and_secret_reference():
    with pytest.raises(ValueError, match="application_uri"):
        _config(application_uri="")
    with pytest.raises(ValueError, match="client_private_key_ref"):
        _config(client_private_key_ref="")


def test_node_binding_is_read_only_and_numeric_scaling_is_finite():
    binding = OpcUaNodeBinding(
        point_id="point-1", node_id="ns=2;s=Plant.Temp",
        data_type="double", scale=0.1, offset=-2.0,
    )
    assert binding.access == "read"
    with pytest.raises(ValueError, match="read-only"):
        OpcUaNodeBinding(point_id="point-1", node_id="ns=2;s=Plant.Temp", access="write")
    with pytest.raises(ValueError, match="finite"):
        OpcUaNodeBinding(point_id="point-1", node_id="ns=2;s=Plant.Temp", scale=float("nan"))


def test_boolean_and_string_bindings_cannot_apply_numeric_scale():
    with pytest.raises(ValueError, match="only valid"):
        OpcUaNodeBinding(point_id="p", node_id="ns=2;s=Ready", data_type="boolean", scale=2)
    with pytest.raises(ValueError, match="unsupported"):
        OpcUaNodeBinding(point_id="p", node_id="ns=2;s=Ready", data_type="variant")
