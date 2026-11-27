from __future__ import annotations

import pytest

from avic_core.drivers.rust_point_adapter import (
    RustDriverConfigurationError,
    RustDriverPointAdapter,
)


def binding(point_id, function=3, address=0, count=1, data_type="uint16"):
    return {
        "point_id": point_id, "function": function, "address": address,
        "count": count, "data_type": data_type,
    }


def test_modbus_planner_merges_adjacent_registers_without_gaps():
    batches = RustDriverPointAdapter._plan_modbus_batches([
        binding("p2", address=2), binding("p0", address=0, count=2),
        binding("p3", address=3),
    ])
    assert len(batches) == 1
    assert (batches[0]["function"], batches[0]["address"], batches[0]["count"]) == (3, 0, 4)
    assert [item["point_id"] for item in batches[0]["bindings"]] == ["p0", "p2", "p3"]


def test_modbus_planner_never_merges_different_functions_or_address_gaps():
    batches = RustDriverPointAdapter._plan_modbus_batches([
        binding("holding", function=3, address=0),
        binding("input", function=4, address=1),
        binding("gap", function=3, address=3),
    ])
    assert [(b["function"], b["address"], b["count"]) for b in batches] == [
        (3, 0, 1), (3, 3, 1), (4, 1, 1),
    ]


def test_modbus_planner_splits_at_protocol_register_limit():
    batches = RustDriverPointAdapter._plan_modbus_batches([
        binding("first", address=0, count=124),
        binding("second", address=124, count=2),
    ])
    assert [(b["address"], b["count"]) for b in batches] == [(0, 124), (124, 2)]


def test_modbus_planner_rejects_invalid_ranges_and_multi_bit_point_bindings():
    with pytest.raises(RustDriverConfigurationError):
        RustDriverPointAdapter._plan_modbus_batches([binding("bad", address=65535, count=2)])
    with pytest.raises(RustDriverConfigurationError):
        RustDriverPointAdapter._plan_modbus_batches([binding("bad-bit", function=1, count=2)])


def test_poll_modbus_batches_issues_one_transport_read_for_contiguous_points():
    adapter = RustDriverPointAdapter.__new__(RustDriverPointAdapter)
    adapter.bindings = (
        binding("p0", address=10),
        binding("p1", address=11),
        binding("p2", address=12),
    )
    adapter._modbus_batches_last_poll = 0
    adapter._modbus_batch_requests = 0
    calls = []

    def read_range(function, address, count):
        calls.append((function, address, count))
        return [101, 202, 303]

    adapter._read_modbus_range = read_range
    values, errors = adapter._poll_modbus_batches()

    assert calls == [(3, 10, 3)]
    assert values == {"p0": 101.0, "p1": 202.0, "p2": 303.0}
    assert errors == {}
    assert adapter._modbus_batch_requests == 1
    assert adapter._modbus_batches_last_poll == 1
