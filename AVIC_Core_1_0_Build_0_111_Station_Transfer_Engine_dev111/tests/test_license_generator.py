import json, tempfile, unittest
from pathlib import Path
from tools.avic_license_generator import generate_keys, issue
from avic_core.licensing.manager import LicenseManager

class LicenseGeneratorTests(unittest.TestCase):
 def test_issue_verify_host_and_point_limit(self):
  with tempfile.TemporaryDirectory() as d:
   priv=Path(d)/'issuer.pem'; pub=Path(d)/'public.pem'; lic=Path(d)/'customer.aviclic'
   generate_keys(priv,pub); issue('HOST-ABC','Test Customer',250,priv,lic,['bacnet_ip'])
   manager=LicenseManager(pub); status=manager.verify(lic,'HOST-ABC')
   self.assertTrue(status.valid); self.assertEqual(status.point_limit,250)
   self.assertTrue(manager.can_create_point(status,{'p1','p2'}))
   self.assertFalse(manager.can_create_point(status,set(str(i) for i in range(250))))
   self.assertEqual(manager.verify(lic,'OTHER').reason,'HOST_ID_MISMATCH')
   self.assertTrue(manager.validate_existing_runtime(status, set(str(i) for i in range(300))).allowed)
 def test_tamper_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   priv=Path(d)/'i.pem'; pub=Path(d)/'p.pem'; lic=Path(d)/'x.aviclic'
   generate_keys(priv,pub); issue('H','C',10,priv,lic)
   data=json.loads(lic.read_text()); data['point_limit']=999; lic.write_text(json.dumps(data))
   self.assertEqual(LicenseManager(pub).verify(lic,'H').reason,'INVALID_SIGNATURE')
if __name__=='__main__': unittest.main()
