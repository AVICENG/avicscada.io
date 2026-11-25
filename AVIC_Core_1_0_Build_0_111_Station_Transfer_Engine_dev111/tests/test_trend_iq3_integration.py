from avic_core.network import (BacnetObjectIdentifier, BacnetProtocolError,
    TrendIQ3Integration, TrendIQ3Profile)

class FakeIQ3:
    def __init__(self): self.reads=[]
    def read_object_list(self, address, device_instance, max_objects=4096):
        assert device_instance == 1001
        return [BacnetObjectIdentifier(8,1001), BacnetObjectIdentifier(3,2),
                BacnetObjectIdentifier(1,4), BacnetObjectIdentifier(1,5),
                BacnetObjectIdentifier(17,1), BacnetObjectIdentifier(17,2)]
    def read_property(self, address, device, typ, inst, prop, timeout_seconds=None, array_index=None):
        self.reads.append((typ,inst,prop))
        vals={77:f"obj-{typ}-{inst}",28:"test",85:0,117:62,111:"0000",103:0,81:False,
              123:["weekly"],38:["exception"],32:"period"}
        if prop not in vals: raise BacnetProtocolError("unsupported")
        return vals[prop]

def test_iq3_profile_is_read_only_and_known_device():
    p=TrendIQ3Profile()
    assert p.device_instance == 1001 and p.read_only
    try: TrendIQ3Profile(read_only=False)
    except ValueError: pass
    else: assert False

def test_iq3_catalog_reads_expected_types_and_preserves_ids():
    client=FakeIQ3(); result=TrendIQ3Integration(client).inspect(("10.10.10.2",47808))
    assert result.expected_counts_match
    assert result.counts == {"binary_input":1,"analog_output":2,"schedule":2}
    assert [x.native_identity for x in result.objects] == [
        "bacnet:object:3:2","bacnet:object:1:4","bacnet:object:1:5",
        "bacnet:object:17:1","bacnet:object:17:2"]
    assert len(result.snapshots)==5
    assert all(x.quality=="good" for x in result.snapshots)

def test_iq3_catalog_reports_count_mismatch_without_guessing_ids():
    class Partial(FakeIQ3):
        def read_object_list(self,*args,**kwargs): return [BacnetObjectIdentifier(3,2)]
    result=TrendIQ3Integration(Partial()).inspect(("10.10.10.2",47808))
    assert not result.expected_counts_match
    assert result.warnings
