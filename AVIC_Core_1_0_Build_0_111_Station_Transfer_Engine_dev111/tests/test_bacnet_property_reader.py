from avic_core.network import (BacnetObjectIdentifier, BacnetObjectReader,
                               BacnetProtocolError, trend_iq3_role)


class FakeClient:
    def __init__(self, values):
        self.values = values
        self.calls = []
    def read_property(self, address, device, typ, instance, prop, timeout_seconds=None, array_index=None):
        self.calls.append((typ, instance, prop, array_index))
        value = self.values.get(prop, BacnetProtocolError(f"unsupported property {prop}"))
        if isinstance(value, Exception):
            raise value
        return value


def test_reads_analog_output_properties_and_keeps_identity():
    client = FakeClient({77: "D1", 28: "Supply fan command", 85: 42.5,
                         117: 62, 111: "0000", 103: 0, 81: False})
    obj = BacnetObjectIdentifier(1, 4)
    snapshot = BacnetObjectReader(client).read_snapshot(("10.10.10.2", 47808), 1001, obj)
    assert snapshot.native_identity == "bacnet:object:1:4"
    assert snapshot.value("object_name") == "D1"
    assert snapshot.value("present_value") == 42.5
    assert snapshot.value("units") == 62
    assert snapshot.quality == "good"
    assert len(client.calls) == 7


def test_unavailable_property_is_reported_without_losing_other_values():
    client = FakeClient({77: "BI-1", 85: 1, 111: "0000", 103: 0})
    snap = BacnetObjectReader(client).read_snapshot(("10.10.10.2", 47808), 1001,
                                                    BacnetObjectIdentifier(3, 2))
    assert snap.value("present_value") == 1
    assert not snap.properties["description"].supported
    assert "unsupported property" in snap.properties["description"].error


def test_schedule_reader_uses_schedule_properties_not_point_units():
    client = FakeClient({77: "Z1", 28: "Occupied schedule", 85: 1,
                         123: ["weekly"], 38: ["exception"], 32: "2026-01-01..2026-12-31"})
    snap = BacnetObjectReader(client).read_snapshot(("10.10.10.2", 47808), 1001,
                                                    BacnetObjectIdentifier(17, 1))
    requested = [call[2] for call in client.calls]
    assert requested == [77, 28, 85, 123, 38, 32]
    assert snap.value("weekly_schedule") == ["weekly"]
    assert 117 not in requested


def test_catalog_filters_to_point_and_schedule_objects():
    client = FakeClient({77: "x", 85: 0, 111: "0000", 103: 0, 81: False})
    objects = [BacnetObjectIdentifier(8, 1001), BacnetObjectIdentifier(3, 2),
               BacnetObjectIdentifier(1, 4), BacnetObjectIdentifier(17, 1)]
    result = BacnetObjectReader(client).read_catalog(("10.10.10.2", 47808), 1001, objects)
    assert [x.object_identifier.object_type for x in result] == [3, 1, 17]


def test_trend_iq3_roles_are_conservative():
    assert trend_iq3_role(BacnetObjectIdentifier(3, 2)) == "binary-input"
    assert trend_iq3_role(BacnetObjectIdentifier(1, 4)) == "analog-output"
    assert trend_iq3_role(BacnetObjectIdentifier(17, 1)) == "schedule"
