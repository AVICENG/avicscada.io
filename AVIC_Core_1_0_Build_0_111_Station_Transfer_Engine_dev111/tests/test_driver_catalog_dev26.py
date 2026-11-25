from avic_core.drivers import (
    BUILTIN_DRIVERS, DriverCatalogEntry, DriverLifecycle, get_driver, list_builtin_drivers,
)

def test_builtin_driver_catalog_is_stable_and_unique():
    entries = list_builtin_drivers()
    assert entries == BUILTIN_DRIVERS
    ids = [entry.driver_id for entry in entries]
    assert len(ids) == len(set(ids))
    assert {"bacnet-ip", "trend-iq3-bacnet", "modbus-tcp"}.issubset(ids)

def test_bacnet_and_trend_are_read_only_catalog_entries():
    for driver_id in ("bacnet-ip", "trend-iq3-bacnet"):
        item = get_driver(driver_id)
        assert item is not None
        assert item.read_supported is True
        assert item.write_supported is False

def test_modbus_is_read_only_transport_not_a_complete_driver_yet():
    item = get_driver("modbus-tcp")
    assert item is not None
    assert item.lifecycle == DriverLifecycle.READ_ONLY_TRANSPORT
    assert item.read_supported is True
    assert item.discovery_supported is False

def test_catalog_rejects_planned_driver_with_capabilities():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry("future", "Future", "Future", DriverLifecycle.PLANNED, True)

def test_catalog_never_authorizes_field_writes():
    import pytest
    with pytest.raises(ValueError):
        DriverCatalogEntry("unsafe", "Unsafe", "X", DriverLifecycle.READ_ONLY_INTEGRATION, True, write_supported=True)
