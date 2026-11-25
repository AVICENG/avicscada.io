import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

from avic_core.audit.service import AuditService
from avic_core.security.auth import SecurityManager, SessionError
from avic_core.security.gateway import Operation, SecurityGateway
from avic_core.security.rbac import Scope, AccessDenied


class SecurityGatewayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.security = SecurityManager(root / 'security.db', session_ttl_seconds=600, idle_timeout_seconds=300)
        self.audit = AuditService(root / 'audit.db')
        self.gateway = SecurityGateway(self.security, self.audit)
        user = self.security.bootstrap_admin('adminroot', 'StrongPassword123')
        self.session = self.security.login('adminroot', 'StrongPassword123')

    def tearDown(self):
        self.tmp.cleanup()

    def test_mutation_requires_csrf_and_is_audited(self):
        op = Operation('station.start', Scope.STATION, 'station', 'st-1', station_id='st-1', mutating=True)
        with self.assertRaises(SessionError):
            self.gateway.execute(session_token=self.session.token, operation=op, action=lambda: 'started')
        result = self.gateway.execute(session_token=self.session.token, csrf_token=self.session.csrf_token,
                                      operation=op, action=lambda: 'started')
        self.assertEqual(result, 'started')
        self.assertEqual(self.audit.verify_chain(), (True, 1))

    def test_mfa_required_operation_rejects_non_mfa_session(self):
        op = Operation('license.manage', Scope.INSTALLATION, 'license', 'lic-1',
                       installation_id='install-1', mutating=False, require_mfa=True)
        with self.assertRaises(SessionError):
            self.gateway.execute(session_token=self.session.token, operation=op, action=lambda: 'changed')
        self.assertEqual(self.audit.verify_chain(), (True, 1))

    def test_denied_operation_is_audited(self):
        user = self.security.create_user('readuser', 'StrongPassword123')
        self.security.grant(user.user_id, 'station.read', station_id='st-A')
        session = self.security.login('readuser', 'StrongPassword123')
        op = Operation('station.stop', Scope.STATION, 'station', 'st-B', station_id='st-B', mutating=False)
        with self.assertRaises(AccessDenied):
            self.gateway.execute(session_token=session.token, operation=op, action=lambda: None)
        self.assertEqual(self.audit.verify_chain(), (True, 1))

    def test_audit_chain_detects_tampering(self):
        self.audit.append(actor_id='u1', action='x', resource_type='station', resource_id='s1')
        self.audit.append(actor_id='u1', action='y', resource_type='station', resource_id='s1')
        self.assertEqual(self.audit.verify_chain(), (True, 2))
        with closing(sqlite3.connect(self.audit.path)) as db:
            db.execute("UPDATE audit_events SET outcome='tampered' WHERE action='x'")
            db.commit()
        self.assertEqual(self.audit.verify_chain(), (False, 0))

    def test_legacy_audit_rows_are_backfilled(self):
        legacy = Path(self.tmp.name) / 'legacy.db'
        with closing(sqlite3.connect(legacy)) as db:
            db.execute("CREATE TABLE audit_events (event_id TEXT PRIMARY KEY, occurred_at TEXT NOT NULL, actor_id TEXT NOT NULL, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT NOT NULL, outcome TEXT NOT NULL, details_json TEXT NOT NULL)")
            db.execute("INSERT INTO audit_events VALUES(?,?,?,?,?,?,?,?)", ('legacy-1','2026-01-01T00:00:00+00:00','u','old','station','s','success','{}'))
            db.commit()
        migrated = AuditService(legacy)
        self.assertEqual(migrated.verify_chain(), (True, 1))

    def test_idle_timeout_expires_session(self):
        with patch('avic_core.security.auth.time.time', return_value=1000):
            session = self.security.login('adminroot', 'StrongPassword123')
        with patch('avic_core.security.auth.time.time', return_value=1301):
            with self.assertRaises(SessionError):
                self.security.authenticate_session(session.token)


if __name__ == '__main__':
    unittest.main()
