"""Siemens S7 target policy: C-only, disabled until a C engine is accepted."""
from avic_core.drivers.catalog import DriverLifecycle, get_driver


def test_s7_is_not_advertised_as_operational_before_c_worker_acceptance():
    entry = get_driver("s7comm")
    assert entry is not None
    assert entry.lifecycle is DriverLifecycle.PLANNED
    assert entry.read_supported is False
    assert entry.discovery_supported is False
    assert entry.write_supported is False
    assert "C-only" in entry.notes
    assert "Rust/Python" in entry.notes
