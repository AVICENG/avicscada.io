import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from avic_core.security.auth import SecurityManager, AuthenticationError, AccountLocked, SessionError
from avic_core.security.rbac import AuthorizationService, Scope, AccessDenied


class SecurityManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "security.db"
        self.security = SecurityManager(self.db, session_ttl_seconds=120, max_failed_attempts=3, lockout_seconds=60)

    def tearDown(self):
        self.tmp.cleanup()

    def test_bootstrap_is_one_time_and_admin_has_global_scope(self):
        user = self.security.bootstrap_admin("rootadmin", "StrongPassword123")
        session = self.security.login("rootadmin", "StrongPassword123")
        principal = self.security.authenticate_session(session.token)
        AuthorizationService().require(principal, "license.manage", scope=Scope.INSTALLATION, installation_id="install-1")
        with self.assertRaises(PermissionError):
            self.security.bootstrap_admin("secondadmin", "StrongPassword123")

    def test_password_hash_and_session_revoke(self):
        user = self.security.create_user("engineer1", "StrongPassword123")
        session = self.security.login("engineer1", "StrongPassword123")
        self.assertNotIn("StrongPassword123", session.token)
        self.security.revoke_session(session.token)
        with self.assertRaises(SessionError):
            self.security.authenticate_session(session.token)

    def test_bad_password_lockout(self):
        self.security.create_user("operator1", "StrongPassword123")
        for _ in range(2):
            with self.assertRaises(AuthenticationError):
                self.security.login("operator1", "WrongPassword123")
        with self.assertRaises(AccountLocked):
            self.security.login("operator1", "WrongPassword123")
        with self.assertRaises(AccountLocked):
            self.security.login("operator1", "StrongPassword123")

    def test_station_grant_is_scoped(self):
        user = self.security.create_user("operator2", "StrongPassword123")
        self.security.grant(user.user_id, "station.read", station_id="station-A")
        session = self.security.login("operator2", "StrongPassword123")
        principal = self.security.authenticate_session(session.token)
        auth = AuthorizationService()
        auth.require(principal, "station.read", scope=Scope.STATION, station_id="station-A")
        with self.assertRaises(AccessDenied):
            auth.require(principal, "station.read", scope=Scope.STATION, station_id="station-B")

    def test_csrf_and_password_change_revoke_sessions(self):
        user = self.security.create_user("engineer2", "StrongPassword123")
        session = self.security.login("engineer2", "StrongPassword123")
        self.security.authenticate_session(session.token, csrf_token=session.csrf_token, require_csrf=True)
        with self.assertRaises(SessionError):
            self.security.authenticate_session(session.token, csrf_token="wrong", require_csrf=True)
        self.security.change_password(user.user_id, "StrongPassword123", "AnotherStrong456")
        with self.assertRaises(SessionError):
            self.security.authenticate_session(session.token)
        self.security.login("engineer2", "AnotherStrong456")

    def test_totp_enrollment_and_login(self):
        user = self.security.create_user("mfauser", "StrongPassword123")
        from avic_core.security.secret_store import SecretStore
        secured = SecurityManager(self.db, session_ttl_seconds=120,
                                  max_failed_attempts=3, lockout_seconds=60,
                                  secret_store=SecretStore(b"t" * 32))
        secret = secured.begin_totp_enrollment(user.user_id)
        code = secured._totp(secret)
        secured.confirm_totp_enrollment(user.user_id, code)
        with self.assertRaises(AuthenticationError):
            secured.login("mfauser", "StrongPassword123")
        session = secured.login("mfauser", "StrongPassword123", totp_code=secured._totp(secret))
        self.assertTrue(session.mfa_verified)

    def test_recovery_codes_are_single_use(self):
        user = self.security.create_user("recoveruser", "StrongPassword123")
        codes = self.security.create_recovery_codes(user.user_id, count=4)
        self.assertTrue(self.security.use_recovery_code(user.user_id, codes[0]))
        self.assertFalse(self.security.use_recovery_code(user.user_id, codes[0]))


if __name__ == "__main__":
    unittest.main()
