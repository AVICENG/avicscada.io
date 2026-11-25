import os
import pytest
from avic_core.security.secret_store import SecretStore, SecretKeyError, SecretDecryptionError


def test_encrypt_decrypt_roundtrip_and_random_nonce():
    store = SecretStore(b"k" * 32)
    a = store.encrypt("TOTP-SECRET-123", context="totp:user-1")
    b = store.encrypt("TOTP-SECRET-123", context="totp:user-1")
    assert a != b
    assert store.decrypt(a, context="totp:user-1") == "TOTP-SECRET-123"


def test_context_and_wrong_key_are_rejected():
    a = SecretStore(b"a" * 32)
    b = SecretStore(b"b" * 32)
    envelope = a.encrypt("secret", context="user:1")
    with pytest.raises(SecretDecryptionError):
        a.decrypt(envelope, context="user:2")
    with pytest.raises(SecretDecryptionError):
        b.decrypt(envelope, context="user:1")


def test_tampering_is_rejected():
    store = SecretStore(b"z" * 32)
    envelope = store.encrypt("secret", context="mfa")
    altered = envelope[:-3] + ("AAA" if envelope[-3:] != "AAA" else "BBB")
    with pytest.raises(SecretDecryptionError):
        store.decrypt(altered, context="mfa")


def test_key_file_is_created_once_and_private(tmp_path):
    path = tmp_path / "keys" / "avic.secretkey"
    SecretStore.generate_key_file(path)
    assert len(path.read_bytes()) == 32
    if os.name == "posix":
        assert path.stat().st_mode & 0o777 == 0o600
    with pytest.raises(SecretKeyError):
        SecretStore.generate_key_file(path)
    assert SecretStore.from_key_file(path).encrypt("x", context="x")


def test_insecure_key_file_permissions_rejected(tmp_path):
    if os.name != "posix":
        pytest.skip("POSIX permission test")
    path = tmp_path / "key"
    path.write_bytes(b"x" * 32)
    path.chmod(0o644)
    with pytest.raises(SecretKeyError):
        SecretStore.from_key_file(path)


def test_rotation_preserves_plaintext_but_changes_envelope():
    old = SecretStore(b"o" * 32)
    new = SecretStore(b"n" * 32)
    original = old.encrypt("totp-seed", context="totp:user-7")
    rotated = SecretStore.rotate_envelope(original, context="totp:user-7", old_store=old, new_store=new)
    assert rotated != original
    assert new.decrypt(rotated, context="totp:user-7") == "totp-seed"
    with pytest.raises(SecretDecryptionError):
        old.decrypt(rotated, context="totp:user-7")


def test_bytes_payload_roundtrip():
    store = SecretStore(b"q" * 32)
    payload = b"\x00\xffbinary-secret"
    encrypted = store.encrypt(payload, context="opaque")
    assert store.decrypt(encrypted, context="opaque", as_bytes=True) == payload
