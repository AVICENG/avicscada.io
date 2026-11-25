from avic_core.drivers import (
    BUILTIN_DRIVERS, DriverCatalogEntry, DriverLifecycle, get_driver, list_builtin_drivers,
)


def test_builtin_driver_catalog_has_only_three_product_drivers():
    entries = list_builtin_drivers()
    assert entries == BUILTIN_DRIVERS
    ids = [entry.driver_id for entry in entries]
    assert len(ids) == len(set(ids))
    assert set(ids) == {"trend-ip", "bacnet-ip", "modbus-tcp"}


def test_trend_ip_is_not_misrepresented_as_trend_over_bacnet():
    item = get_driver("trend-ip")
    assert item is not None
    assert item.protocol == "Trend vCNC over TCP"
    assert item.lifecycle == DriverLifecycle.PLANNED
    assert item.read_supported is False
    assert item.discovery_supported is False
    assert item.write_supported is False
    assert get_driver("trend-iq3-bacnet") is None


def test_bacnet_and_modbus_are_read_only_transport_foundations():
    for driver_id in ("bacnet-ip", "modbus-tcp"):
        item = get_driver(driver_id)
        assert item is not None
        assert item.lifecycle == DriverLifecycle.READ_ONLY_TRANSPORT
        assert item.read_supported is True
        assert item.write_supported is False


def test_modbus_is_not_misrepresented_as_a_complete_driver_yet():
    item = get_driver("modbus-tcp")
    assert item is not None
    assert item.discovery_supported is False
    assert "PointRuntime adapter" in item.notes


def test_catalog_rejects_planned_driver_with_capabilities():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry("future", "Future", "Future", DriverLifecycle.PLANNED, True)


def test_catalog_never_authorizes_field_writes():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry("unsafe", "Unsafe", "X", DriverLifecycle.READ_ONLY_INTEGRATION, True, write_supported=True)
