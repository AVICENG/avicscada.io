import sqlite3
from contextlib import closing
from unittest.mock import patch
import pytest

from avic_core.audit.service import AuditService
from avic_core.security.auth import AuthenticationError, SecurityManager, SessionError
from avic_core.security.secret_store import SecretStore

PASSWORD = "StrongPassword123"


def test_recovery_code_issuance_requires_recent_mfa_and_reauth(tmp_path):
    db = tmp_path / "security.db"
    audit = AuditService(tmp_path / "audit.db")
    manager = SecurityManager(db, secret_store=SecretStore(b"r" * 32), audit_service=audit)
    user = manager.create_user("mfa-recovery", PASSWORD)
    seed = manager.begin_totp_enrollment(user.user_id)
    manager.confirm_totp_enrollment(user.user_id, manager._totp(seed))
    session = manager.login("mfa-recovery", PASSWORD, totp_code=manager._totp(seed))

    with pytest.raises(AuthenticationError):
        manager.issue_recovery_codes(session_token=session.token, password="WrongPassword123",
                                     totp_code=manager._totp(seed))
    codes = manager.issue_recovery_codes(session_token=session.token, password=PASSWORD,
                                         totp_code=manager._totp(seed), count=4)
    assert len(codes) == 4
    assert manager.use_recovery_code(user.user_id, codes[0])
    assert not manager.use_recovery_code(user.user_id, codes[0])
    assert audit.verify_chain()[0]


def test_break_glass_requires_admin_password_recovery_code_and_reason(tmp_path):
    audit = AuditService(tmp_path / "audit.db")
    manager = SecurityManager(tmp_path / "security.db", audit_service=audit,
                              break_glass_ttl_seconds=120)
    admin = manager.bootstrap_admin("rootadmin", PASSWORD)
    codes = manager.create_recovery_codes(admin.user_id, count=4)

    with pytest.raises(AuthenticationError):
        manager.break_glass_login("rootadmin", PASSWORD, "not-a-code",
                                  reason="Emergency maintenance required")
    with pytest.raises(ValueError):
        manager.break_glass_login("rootadmin", PASSWORD, codes[0], reason="urgent")

    session = manager.break_glass_login("rootadmin", PASSWORD, codes[0],
                                        reason="Production control service recovery")
    assert session.mfa_verified
    assert manager.get_break_glass_status(session.token)["active"]
    manager.authenticate_session(session.token)
    assert not manager.use_recovery_code(admin.user_id, codes[0])
    events_ok, count = audit.verify_chain()
    assert events_ok and count >= 2
    with closing(sqlite3.connect(manager.path)) as db:
        row = db.execute("SELECT break_glass,break_glass_reason FROM security_sessions WHERE token_hash=?",
                         (manager._hash_token(session.token),)).fetchone()
    assert row == (1, "Production control service recovery")


def test_break_glass_expires_and_revokes_old_admin_sessions(tmp_path):
    manager = SecurityManager(tmp_path / "security.db", break_glass_ttl_seconds=60)
    admin = manager.bootstrap_admin("adminexpire", PASSWORD)
    old = manager.login("adminexpire", PASSWORD)
    code = manager.create_recovery_codes(admin.user_id, count=4)[0]
    emergency = manager.break_glass_login("adminexpire", PASSWORD, code,
                                          reason="Emergency site recovery operation")
    with pytest.raises(SessionError):
        manager.authenticate_session(old.token)
    assert manager.get_break_glass_status(emergency.token)["active"]
    with patch("avic_core.security.auth.time.time", return_value=emergency.expires_at + 1):
        assert not manager.get_break_glass_status(emergency.token)["active"]
        with pytest.raises(SessionError):
            manager.authenticate_session(emergency.token)
