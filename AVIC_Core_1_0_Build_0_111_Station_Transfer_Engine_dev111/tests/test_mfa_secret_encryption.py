import sqlite3
from contextlib import closing

import pytest

from avic_core.security.auth import (
    AuthenticationError,
    MFAStorageMigrationRequired,
    SecurityManager,
)
from avic_core.security.secret_store import SecretStore


PASSWORD = "StrongPassword123"


def make_security(tmp_path, key=b"a" * 32):
    return SecurityManager(
        tmp_path / "security.db",
        secret_store=SecretStore(key) if key is not None else None,
    )


def stored_secret(db_path, user_id):
    with closing(sqlite3.connect(db_path)) as db:
        return db.execute(
            "SELECT mfa_secret FROM security_users WHERE user_id=?", (user_id,)
        ).fetchone()[0]


def test_totp_secret_is_encrypted_at_rest_and_survives_restart(tmp_path):
    db_path = tmp_path / "security.db"
    store = SecretStore(b"a" * 32)
    manager = SecurityManager(db_path, secret_store=store)
    user = manager.create_user("mfa-user", PASSWORD)
    seed = manager.begin_totp_enrollment(user.user_id)
    pending = stored_secret(db_path, user.user_id)
    assert pending.startswith("avic-pending:v1:")
    assert seed not in pending
    manager.confirm_totp_enrollment(user.user_id, manager._totp(seed))
    encrypted = stored_secret(db_path, user.user_id)
    assert encrypted.startswith("avic:v1:")
    assert seed not in encrypted

    restarted = SecurityManager(db_path, secret_store=SecretStore(b"a" * 32))
    session = restarted.login("mfa-user", PASSWORD, totp_code=restarted._totp(seed))
    assert session.mfa_verified


def test_legacy_plaintext_migration_is_explicit_and_transactional(tmp_path):
    manager = make_security(tmp_path)
    user = manager.create_user("legacy-user", PASSWORD)
    legacy_seed = "JBSWY3DPEHPK3PXP"
    with manager._db() as db:
        db.execute("UPDATE security_users SET mfa_secret=? WHERE user_id=?",
                   ("pending:" + legacy_seed, user.user_id))

    with pytest.raises(MFAStorageMigrationRequired):
        manager.login("legacy-user", PASSWORD)

    manager.secret_store = SecretStore(b"b" * 32)
    assert manager.migrate_legacy_totp_secrets() == 1
    stored = stored_secret(manager.path, user.user_id)
    assert stored.startswith("avic-pending:v1:")
    assert legacy_seed not in stored
    assert manager.migrate_legacy_totp_secrets() == 0
    assert manager._decode_mfa_secret(user.user_id, stored) == (legacy_seed, True)


def test_missing_key_fails_closed_for_existing_encrypted_mfa(tmp_path):
    db_path = tmp_path / "security.db"
    manager = SecurityManager(db_path, secret_store=SecretStore(b"c" * 32))
    user = manager.create_user("key-user", PASSWORD)
    seed = manager.begin_totp_enrollment(user.user_id)
    manager.confirm_totp_enrollment(user.user_id, manager._totp(seed))

    no_key_manager = SecurityManager(db_path)
    with pytest.raises(AuthenticationError):
        no_key_manager.login("key-user", PASSWORD, totp_code=no_key_manager._totp(seed))


def test_key_rotation_reencrypts_all_totp_secrets(tmp_path):
    db_path = tmp_path / "security.db"
    old_store = SecretStore(b"d" * 32)
    manager = SecurityManager(db_path, secret_store=old_store)
    user = manager.create_user("rotate-user", PASSWORD)
    seed = manager.begin_totp_enrollment(user.user_id)
    manager.confirm_totp_enrollment(user.user_id, manager._totp(seed))
    before = stored_secret(db_path, user.user_id)

    new_store = SecretStore(b"e" * 32)
    assert manager.rotate_totp_encryption_key(new_store) == 1
    after = stored_secret(db_path, user.user_id)
    assert after != before
    assert manager.secret_store is new_store
    with pytest.raises(AuthenticationError):
        SecurityManager(db_path, secret_store=old_store).login(
            "rotate-user", PASSWORD, totp_code=manager._totp(seed)
        )
    restarted = SecurityManager(db_path, secret_store=SecretStore(b"e" * 32))
    assert restarted.login("rotate-user", PASSWORD, totp_code=restarted._totp(seed)).mfa_verified


def test_rotation_refuses_legacy_rows_without_switching_store(tmp_path):
    manager = make_security(tmp_path, key=b"f" * 32)
    user = manager.create_user("legacy-rotate", PASSWORD)
    with manager._db() as db:
        db.execute("UPDATE security_users SET mfa_secret=? WHERE user_id=?",
                   ("JBSWY3DPEHPK3PXP", user.user_id))
    old_provider = manager.secret_store
    with pytest.raises(MFAStorageMigrationRequired):
        manager.rotate_totp_encryption_key(SecretStore(b"g" * 32))
    assert manager.secret_store is old_provider
    assert stored_secret(manager.path, user.user_id) == "JBSWY3DPEHPK3PXP"


def test_wrong_key_and_unconfigured_store_never_disable_mfa_checks(tmp_path):
    db_path = tmp_path / "security.db"
    manager = SecurityManager(db_path, secret_store=SecretStore(b"h" * 32))
    user = manager.create_user("wrong-key", PASSWORD)
    seed = manager.begin_totp_enrollment(user.user_id)
    manager.confirm_totp_enrollment(user.user_id, manager._totp(seed))

    wrong_key = SecurityManager(db_path, secret_store=SecretStore(b"i" * 32))
    with pytest.raises(AuthenticationError):
        wrong_key.login("wrong-key", PASSWORD, totp_code=wrong_key._totp(seed))

    unconfigured = SecurityManager(tmp_path / "empty.db")
    no_mfa_user = unconfigured.create_user("no-secret-store", PASSWORD)
    with pytest.raises(Exception):
        unconfigured.begin_totp_enrollment(no_mfa_user.user_id)
