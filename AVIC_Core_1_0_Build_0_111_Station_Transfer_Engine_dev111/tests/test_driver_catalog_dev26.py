from avic_core.drivers import (
    BUILTIN_DRIVERS, DriverCatalogEntry, DriverCategory, DriverLifecycle,
    get_driver, list_builtin_drivers, list_drivers_by_category,
)


def test_catalog_has_unique_ids_and_all_entries_have_license_keys():
    entries = list_builtin_drivers()
    ids = [entry.driver_id for entry in entries]
    assert entries == BUILTIN_DRIVERS
    assert len(ids) == len(set(ids))
    assert all(entry.license_feature.startswith("driver.") for entry in entries)


def test_requested_open_protocol_families_are_in_catalog():
    expected = {
        "trend-ip", "bacnet-ip", "bacnet-mstp", "modbus-tcp", "modbus-rtu",
        "lonworks", "mbus", "knxnet-ip", "mqtt", "s7comm", "opc-ua-client", "opc-ua-server",
        "opc-da-gateway", "obix", "snmp", "haystack", "rest-api",
    }
    assert {entry.driver_id for entry in list_builtin_drivers()} == expected


def test_excluded_proprietary_families_are_not_in_catalog():
    ids = {entry.driver_id for entry in list_builtin_drivers()}
    excluded = {"niagara-fox", "fox", "ccn", "andover", "n2"}
    assert ids.isdisjoint(excluded)


def test_only_existing_read_only_transports_advertise_read_capability():
    expected = {"bacnet-ip", "modbus-tcp", "modbus-rtu", "knxnet-ip", "mqtt"}
    actual = {entry.driver_id for entry in BUILTIN_DRIVERS if entry.read_supported}
    assert actual == expected
    assert all(not entry.write_supported for entry in BUILTIN_DRIVERS)


def test_trend_ip_is_native_vcnc_not_bacnet():
    item = get_driver("trend-ip")
    assert item is not None
    assert item.protocol == "Trend vCNC over TCP"
    assert item.lifecycle == DriverLifecycle.PLANNED
    assert not item.read_supported and not item.discovery_supported and not item.write_supported
    assert get_driver("trend-iq3-bacnet") is None


def test_existing_bacnet_modbus_foundations_remain_honest():
    for driver_id in ("bacnet-ip", "modbus-tcp", "modbus-rtu"):
        item = get_driver(driver_id)
        assert item is not None
        assert item.lifecycle == DriverLifecycle.READ_ONLY_TRANSPORT
        assert item.read_supported
        assert not item.write_supported


def test_knxnet_ip_is_read_only_runtime_not_write_capable():
    item = get_driver("knxnet-ip")
    assert item is not None
    assert item.lifecycle == DriverLifecycle.READ_ONLY_TRANSPORT
    assert item.read_supported
    assert not item.discovery_supported
    assert not item.write_supported


def test_mbus_is_catalogued_as_planned_wired_only_read_only_driver():
    item = get_driver("mbus")
    assert item is not None
    assert item.protocol == "EN 13757-2/-3 wired Meter-Bus"
    assert item.lifecycle == DriverLifecycle.PLANNED
    assert item.category == DriverCategory.BUILDING_AUTOMATION
    assert not item.read_supported
    assert not item.discovery_supported
    assert not item.write_supported
    assert "libmbus" in item.notes
    assert "Wireless M-Bus" in item.notes


def test_category_tree_groups_semantic_layer_separately():
    assert [x.driver_id for x in list_drivers_by_category(DriverCategory.SEMANTIC)] == ["haystack"]


def test_catalog_rejects_planned_driver_with_capabilities():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry(
            "future", "Future", "Future", DriverLifecycle.PLANNED, True,
            license_feature="driver.future",
        )


def test_catalog_requires_license_feature_key():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry("future", "Future", "Future", DriverLifecycle.PLANNED, False)


def test_catalog_never_authorizes_field_writes():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry(
            "unsafe", "Unsafe", "X", DriverLifecycle.READ_ONLY_INTEGRATION, True,
            write_supported=True, license_feature="driver.unsafe",
        )
