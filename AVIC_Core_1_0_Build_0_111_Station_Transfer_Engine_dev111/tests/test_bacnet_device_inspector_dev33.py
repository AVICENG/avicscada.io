from avic_core.network import BacnetObjectIdentifier, BacnetDeviceInspector


class FakeInspectorClient:
    def read_device_identity(self, address, device_instance):
        return {"device_instance": device_instance, "vendor_id": 91,
                "vendor_name": "Trend Control Systems", "model_name": "IQ3",
                "firmware_revision": "1.2"}

    def read_object_list(self, address, device_instance, max_objects=4096):
        return [BacnetObjectIdentifier(8, device_instance),
                BacnetObjectIdentifier(3, 2)]

    def read_object_name(self, address, device_instance, obj):
        return {8: "Trend Controller", 3: "Outside Air"}[obj.object_type]

    def read_property(self, address, device, typ, instance, prop,
                      timeout_seconds=None, array_index=None):
        values = {77: "Outside Air", 28: "Outdoor temperature", 85: 21.5,
                  117: 62, 111: "0000", 103: 0, 81: False}
        return values[prop]


def test_generic_bacnet_inspector_reads_identity_object_list_and_point_snapshot():
    result = BacnetDeviceInspector(FakeInspectorClient()).inspect(
        ("10.10.10.2", 47808), 1001)
    assert result.device_identity["model_name"] == "IQ3"
    assert len(result.objects) == 2
    assert result.objects[1]["object_name"] == "Outside Air"
    assert len(result.point_snapshots) == 1
    assert result.point_snapshots[0].value("present_value") == 21.5
    assert result.point_snapshots[0].quality == "good"
