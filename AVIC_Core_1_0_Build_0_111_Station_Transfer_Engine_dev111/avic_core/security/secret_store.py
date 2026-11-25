from __future__ import annotations

import base64
import os
import secrets
import stat
import tempfile
from pathlib import Path
from typing import Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class SecretStoreError(RuntimeError):
    """Base error for secret-store failures."""


class SecretKeyError(SecretStoreError):
    """Missing, malformed, or insufficiently protected key material."""


class SecretDecryptionError(SecretStoreError):
    """Ciphertext authentication failed or the wrong key/context was used."""


class SecretStore:
    """Authenticated encryption for small secrets using AES-256-GCM.

    Key material is supplied out-of-band in a dedicated 32-byte file. This class
    deliberately does not create keys during normal startup: losing or silently
    replacing a key must never make encrypted MFA material appear recoverable.
    """

    VERSION = 1
    KEY_BYTES = 32
    NONCE_BYTES = 12
    _MAGIC = b"AVICSEC"

    def __init__(self, key: bytes):
        if not isinstance(key, bytes) or len(key) != self.KEY_BYTES:
            raise SecretKeyError("Ключ Secret Store должен содержать ровно 32 байта")
        self._key = bytes(key)

    @classmethod
    def generate_key_file(cls, path: Union[str, Path]) -> Path:
        """Provision a new key file once; never overwrite an existing path."""
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            fd = os.open(str(target), flags, 0o600)
        except FileExistsError as exc:
            raise SecretKeyError("Файл ключа уже существует; перезапись запрещена") from exc
        key = secrets.token_bytes(cls.KEY_BYTES)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(key)
                stream.flush()
                os.fsync(stream.fileno())
            if os.name == "posix":
                os.chmod(target, 0o600)
        except Exception:
            try:
                target.unlink(missing_ok=True)
            finally:
                raise
        return target

    @classmethod
    def from_key_file(cls, path: Union[str, Path], *, enforce_permissions: bool = True) -> "SecretStore":
        target = Path(path)
        if target.is_symlink() or not target.is_file():
            raise SecretKeyError("Файл ключа отсутствует или не является обычным файлом")
        if os.name == "posix" and enforce_permissions:
            mode = stat.S_IMODE(target.stat().st_mode)
            if mode & 0o077:
                raise SecretKeyError("Небезопасные права файла ключа: требуется доступ только владельцу (0600)")
        try:
            key = target.read_bytes()
        except OSError as exc:
            raise SecretKeyError("Не удалось прочитать файл ключа") from exc
        return cls(key)

    @staticmethod
    def _aad(context: str) -> bytes:
        if not isinstance(context, str) or not context or len(context) > 512:
            raise ValueError("Контекст секрета должен содержать от 1 до 512 символов")
        return ("AVIC-SecretStore-v1:" + context).encode("utf-8")

    def encrypt(self, plaintext: Union[str, bytes], *, context: str) -> str:
        if isinstance(plaintext, str):
            raw = plaintext.encode("utf-8")
        elif isinstance(plaintext, bytes):
            raw = plaintext
        else:
            raise TypeError("Секрет должен быть строкой или bytes")
        nonce = secrets.token_bytes(self.NONCE_BYTES)
        ciphertext = AESGCM(self._key).encrypt(nonce, raw, self._aad(context))
        packed = self._MAGIC + bytes([self.VERSION]) + nonce + ciphertext
        return base64.urlsafe_b64encode(packed).decode("ascii")

    def decrypt(self, envelope: str, *, context: str, as_bytes: bool = False) -> Union[str, bytes]:
        try:
            packed = base64.urlsafe_b64decode(envelope.encode("ascii"))
            header_len = len(self._MAGIC) + 1 + self.NONCE_BYTES
            if len(packed) < header_len + 16 or not packed.startswith(self._MAGIC):
                raise ValueError("invalid envelope")
            version = packed[len(self._MAGIC)]
            if version != self.VERSION:
                raise ValueError("unsupported version")
            nonce = packed[len(self._MAGIC) + 1:header_len]
            ciphertext = packed[header_len:]
            plaintext = AESGCM(self._key).decrypt(nonce, ciphertext, self._aad(context))
            return plaintext if as_bytes else plaintext.decode("utf-8")
        except (InvalidTag, ValueError, UnicodeDecodeError, UnicodeEncodeError, TypeError) as exc:
            raise SecretDecryptionError("Не удалось проверить или расшифровать секрет") from exc

    @classmethod
    def rotate_envelope(cls, envelope: str, *, context: str, old_store: "SecretStore", new_store: "SecretStore") -> str:
        """Re-encrypt one value; caller must atomically persist the returned value."""
        plaintext = old_store.decrypt(envelope, context=context, as_bytes=True)
        return new_store.encrypt(plaintext, context=context)
