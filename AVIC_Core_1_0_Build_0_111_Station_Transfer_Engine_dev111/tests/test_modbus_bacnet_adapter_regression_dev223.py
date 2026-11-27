from __future__ import annotations

from types import SimpleNamespace

from avic_core.domain.models import PointQuality
from avic_core.drivers.modbus_tcp_adapter import ModbusTcpPointAdapter, ModbusTcpPointBinding
from avic_core.drivers.bacnet_ip_adapter import BacnetIpPointAdapter, BacnetIpPointBinding


class Runtime:
    def __init__(self):
        self.published = []
        self.qualities = []

    def publish(self, point_id, value, *, quality, source_driver_id):
        self.published.append((point_id, value, quality, source_driver_id))
        return SimpleNamespace(value=value, quality=quality)

    def mark_quality(self, point_id, quality, *, source_driver_id):
        self.qualities.append((point_id, quality, source_driver_id))
        return SimpleNamespace(value=None, quality=quality)


class ModbusClient:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def read_holding_registers(self, address, count):
        self.calls.append((3, address, count))
        if self.fail:
            raise TimeoutError("PLC timeout")
        return list(range(address, address + count))

    def read_input_registers(self, address, count):
        self.calls.append((4, address, count))
        return list(range(address, address + count))

    def read_coils(self, address, count):
        self.calls.append((1, address, count))
        return [1] * count

    def read_discrete_inputs(self, address, count):
        self.calls.append((2, address, count))
        return [0] * count


def test_modbus_adapter_coalesces_adjacent_ranges_and_publishes_good_values():
    runtime, client = Runtime(), ModbusClient()
    adapter = ModbusTcpPointAdapter(client, runtime, "modbus-1", [
        ModbusTcpPointBinding("p1", 3, 10),
        ModbusTcpPointBinding("p2", 3, 11),
        ModbusTcpPointBinding("p3", 3, 13),
    ])
    result = adapter.poll_once()
    assert result["group_count"] == 2
    assert client.calls == [(3, 10, 2), (3, 13, 1)]
    assert [item[1] for item in runtime.published] == [10, 11, 13]
    assert all(item[2] is PointQuality.GOOD for item in runtime.published)


def test_modbus_adapter_marks_entire_failed_group_bad_communication():
    runtime, client = Runtime(), ModbusClient(fail=True)
    adapter = ModbusTcpPointAdapter(client, runtime, "modbus-2", [
        ModbusTcpPointBinding("p1", 3, 0),
        ModbusTcpPointBinding("p2", 3, 1),
    ])
    result = adapter.poll_once()
    assert result["failure_count"] == 2
    assert {item[0] for item in runtime.qualities} == {"p1", "p2"}
    assert all(item[1] is PointQuality.BAD_COMMUNICATION for item in runtime.qualities)


class BacnetClient:
    def __init__(self, values):
        self.values = values
        self.calls = []

    def read_property(self, address, device, obj_type, obj_instance, prop, *, array_index=None):
        self.calls.append((address, device, obj_type, obj_instance, prop, array_index))
        value = self.values[(obj_type, obj_instance, prop, array_index)]
        if isinstance(value, Exception):
            raise value
        return value

    def close(self):
        self.closed = True


def test_bacnet_adapter_reads_property_scales_value_and_preserves_array_index():
    runtime = Runtime()
    address = ("192.0.2.10", 47808)
    client = BacnetClient({(0, 1, 85, 0): 20.0})
    adapter = BacnetIpPointAdapter(client, runtime, "bacnet-1", [
        BacnetIpPointBinding("temperature", address, 1234, 0, 1, 85, array_index=0,
                             scale=1.8, offset=32.0)
    ])
    result = adapter.poll_once()
    assert result["success_count"] == 1
    assert runtime.published == [("temperature", 68.0, PointQuality.GOOD, "bacnet-1")]
    assert client.calls == [(address, 1234, 0, 1, 85, 0)]


def test_bacnet_adapter_marks_communication_failure_bad():
    runtime = Runtime()
    address = ("192.0.2.11", 47808)
    client = BacnetClient({(2, 5, 85, None): TimeoutError("BACnet timeout")})
    adapter = BacnetIpPointAdapter(client, runtime, "bacnet-2", [
        BacnetIpPointBinding("value", address, 4321, 2, 5)
    ])
    result = adapter.poll_once()
    assert result["failure_count"] == 1
    assert runtime.qualities == [("value", PointQuality.BAD_COMMUNICATION, "bacnet-2")]
