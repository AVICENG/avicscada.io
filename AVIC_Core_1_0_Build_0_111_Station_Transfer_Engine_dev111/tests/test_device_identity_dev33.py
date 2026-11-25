from avic_core.network.identity import (DeviceIdentityResolver, IdentityConfidence,
                                        VendorRecord, VendorRegistry)


def test_bacnet_vendor_id_resolves_trend_manufacturer_without_guessing_model():
    identity = DeviceIdentityResolver().resolve(protocol="bacnet/ip", vendor_id=91)
    assert identity.manufacturer == "Trend Control Systems"
    assert identity.manufacturer_source == "bacnet/ip.vendor_id:91"
    assert identity.model is None
    assert identity.confidence == IdentityConfidence.CONFIRMED


def test_model_is_only_set_when_reported_by_device():
    resolver = DeviceIdentityResolver()
    unknown = resolver.resolve(protocol="modbus/tcp", vendor_id=91)
    assert unknown.manufacturer is None  # BACnet IDs are not reused for Modbus.
    assert unknown.model is None
    reported = resolver.resolve(protocol="bacnet/ip", vendor_id=91,
                                model_name="IQ3")
    assert reported.model == "IQ3"
    assert reported.model_source == "bacnet/ip.model_name"


def test_registry_is_protocol_scoped_and_extensible():
    registry = VendorRegistry([VendorRecord("Example", "modbus", "0x1234")])
    resolver = DeviceIdentityResolver(registry)
    assert resolver.resolve(protocol="modbus/tcp", vendor_id="0x1234").manufacturer == "Example"
    assert resolver.resolve(protocol="bacnet/ip", vendor_id="0x1234").manufacturer is None


def test_mac_is_recorded_as_evidence_but_does_not_guess_vendor_or_model():
    identity = DeviceIdentityResolver().resolve(protocol="modbus/tcp",
                                                mac_address="00-10-70-03-05-B2")
    assert identity.manufacturer is None
    assert identity.model is None
    assert any(e.field == "mac_address" for e in identity.evidence)
