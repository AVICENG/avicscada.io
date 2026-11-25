from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, VerificationError
except ImportError as exc:  # fail closed: never silently downgrade password hashing
    raise RuntimeError("AVIC Security requires argon2-cffi; install the declared dependency") from exc

from avic_core.security.rbac import Principal
from avic_core.security.secret_store import SecretStore, SecretStoreError


class AuthenticationError(Exception):
    """Generic authentication failure; callers must not reveal whether a user exists."""


class AccountLocked(AuthenticationError):
    pass


class SessionError(AuthenticationError):
    pass


class MFAStorageMigrationRequired(AuthenticationError):
    """Legacy plaintext MFA material requires an explicit one-time migration."""


@dataclass(frozen=True)
class AuthenticatedSession:
    user_id: str
    username: str
    token: str
    csrf_token: str
    expires_at: int
    mfa_verified: bool


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    username: str
    enabled: bool
    mfa_enabled: bool


ROLE_PERMISSIONS = {
    # Customer-side roles are intentionally operational; they do not receive
    # engineering, driver, logic, deployment, or platform permissions.
    "customer_administrator": frozenset({
        "project.read", "station.read", "point.read", "point.write",
        "alarm.read", "alarm.acknowledge", "trend.read", "report.read",
        "report.export", "schedule.configure", "user.manage", "backup.create",
    }),
    "system_administrator": frozenset({"*"}),
    "project_administrator": frozenset({"project.read", "project.configure", "station.read", "station.start", "station.stop", "point.read", "point.create", "point.delete", "point.write", "logic.read", "logic.edit", "logic.deploy", "driver.install", "driver.configure", "alarm.read", "alarm.acknowledge", "audit.read"}),
    "engineer": frozenset({"project.read", "station.read", "station.start", "station.stop", "point.read", "point.create", "point.write", "logic.read", "logic.edit", "logic.deploy", "driver.configure", "alarm.read", "alarm.acknowledge"}),
    "operator": frozenset({"project.read", "station.read", "point.read", "point.write", "alarm.read", "alarm.acknowledge"}),
    "dispatcher": frozenset({"project.read", "station.read", "point.read", "alarm.read", "alarm.acknowledge"}),
    "viewer": frozenset({"project.read", "station.read", "point.read", "alarm.read"}),
    # AVIC granular role templates. Scope is still granted separately per station/project.
    "avic_viewer": frozenset({"project.read", "station.read", "point.read", "graphics.read", "alarm.read", "trend.read", "event.read"}),
    "avic_operator": frozenset({"project.read", "station.read", "point.read", "graphics.read", "alarm.read", "alarm.acknowledge", "event.read", "trend.read", "equipment.command.start", "equipment.command.stop"}),
    "avic_senior_operator": frozenset({"project.read", "station.read", "point.read", "graphics.read", "alarm.read", "alarm.acknowledge", "event.read", "trend.read", "equipment.command.start", "equipment.command.stop", "setpoint.write", "schedule.configure", "equipment.manual_mode"}),
    "avic_engineer": frozenset({"project.read", "project.configure", "station.read", "station.start", "station.stop", "point.read", "point.create", "point.write", "graphics.read", "graphics.configure", "graphics.binding.configure", "graphics.publish", "alarm.read", "alarm.acknowledge", "event.read", "trend.read", "schedule.configure", "logic.read", "logic.edit", "logic.deploy", "driver.configure", "network.discovery"}),
    "avic_security_admin": frozenset({"project.read", "station.read", "point.read", "graphics.read", "alarm.read", "event.read", "audit.read", "user.manage", "role.assign", "security.configure"}),
}


class SecurityManager:
    """Local identity/session service. Network cookies/TLS/CSRF middleware belong to the API host."""

    def __init__(self, database_path: str | Path, *, session_ttl_seconds: int = 8 * 3600,
                 idle_timeout_seconds: int = 30 * 60,
                 max_failed_attempts: int = 5, lockout_seconds: int = 15 * 60,
                 password_hasher: PasswordHasher | None = None,
                 secret_store: SecretStore | None = None,
                 audit_service=None,
                 break_glass_ttl_seconds: int = 900):
        self.path = str(database_path)
        if session_ttl_seconds < 60 or idle_timeout_seconds < 60:
            raise ValueError("Тайм-ауты сессии должны быть не менее 60 секунд")
        self.session_ttl = session_ttl_seconds
        self.idle_timeout = min(idle_timeout_seconds, session_ttl_seconds)
        self.max_failed = max_failed_attempts
        self.lockout_seconds = lockout_seconds
        self.hasher = password_hasher or PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
        self.secret_store = secret_store
        self.audit_service = audit_service
        if not 60 <= break_glass_ttl_seconds <= 900:
            raise ValueError("Break-glass TTL должен быть от 60 до 900 секунд")
        self.break_glass_ttl = break_glass_ttl_seconds
        self._init_db()

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @contextmanager
    def _db(self):
        db = self._connect()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _init_db(self):
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS security_users (
              user_id TEXT PRIMARY KEY, username TEXT NOT NULL UNIQUE COLLATE NOCASE,
              password_hash TEXT NOT NULL, enabled INTEGER NOT NULL DEFAULT 1,
              mfa_secret TEXT, failed_attempts INTEGER NOT NULL DEFAULT 0,
              locked_until INTEGER NOT NULL DEFAULT 0, created_at INTEGER NOT NULL,
              password_changed_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS security_roles (
              user_id TEXT NOT NULL REFERENCES security_users(user_id) ON DELETE CASCADE,
              role_id TEXT NOT NULL, PRIMARY KEY(user_id, role_id)
            );
            CREATE TABLE IF NOT EXISTS security_grants (
              user_id TEXT NOT NULL REFERENCES security_users(user_id) ON DELETE CASCADE,
              permission_id TEXT NOT NULL, installation_id TEXT, project_id TEXT, station_id TEXT,
              PRIMARY KEY(user_id, permission_id, installation_id, project_id, station_id)
            );
            CREATE TABLE IF NOT EXISTS security_sessions (
              token_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES security_users(user_id) ON DELETE CASCADE,
              csrf_hash TEXT NOT NULL, created_at INTEGER NOT NULL, expires_at INTEGER NOT NULL,
              last_seen INTEGER NOT NULL, revoked INTEGER NOT NULL DEFAULT 0, mfa_verified INTEGER NOT NULL DEFAULT 0,
              break_glass INTEGER NOT NULL DEFAULT 0, break_glass_reason TEXT,
              break_glass_expires_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS security_meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS security_recovery (
              recovery_hash TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES security_users(user_id) ON DELETE CASCADE,
              created_at INTEGER NOT NULL, used_at INTEGER
            );
            """)
            columns = {row[1] for row in db.execute("PRAGMA table_info(security_sessions)")}
            for name, declaration in (
                ("break_glass", "INTEGER NOT NULL DEFAULT 0"),
                ("break_glass_reason", "TEXT"),
                ("break_glass_expires_at", "INTEGER"),
            ):
                if name not in columns:
                    db.execute(f"ALTER TABLE security_sessions ADD COLUMN {name} {declaration}")

    @staticmethod
    def _validate_password(password: str):
        if not isinstance(password, str) or len(password) < 12 or len(password) > 1024:
            raise ValueError("Пароль должен содержать от 12 до 1024 символов")
        if not any(c.islower() for c in password) or not any(c.isupper() for c in password) or not any(c.isdigit() for c in password):
            raise ValueError("Пароль должен включать строчные, прописные буквы и цифры")

    def create_user(self, username: str, password: str, *, roles: Iterable[str] = (), enabled: bool = True) -> UserRecord:
        username = username.strip()
        if not 3 <= len(username) <= 128 or any(ord(c) < 33 for c in username):
            raise ValueError("Недопустимое имя пользователя")
        self._validate_password(password)
        user_id = secrets.token_hex(16)
        now = int(time.time())
        with self._db() as db:
            db.execute("INSERT INTO security_users(user_id,username,password_hash,enabled,created_at,password_changed_at) VALUES(?,?,?,?,?,?)",
                       (user_id, username, self.hasher.hash(password), int(enabled), now, now))
            db.executemany("INSERT INTO security_roles(user_id,role_id) VALUES(?,?)", [(user_id, r) for r in set(roles)])
        return UserRecord(user_id, username, enabled, False)

    def bootstrap_admin(self, username: str, password: str) -> UserRecord:
        """Create the first administrator once; bootstrap permanently closes after success."""
        with self._db() as db:
            if db.execute("SELECT 1 FROM security_meta WHERE key='bootstrap_closed'").fetchone():
                raise PermissionError("Первичная настройка администратора уже закрыта")
            if db.execute("SELECT 1 FROM security_users LIMIT 1").fetchone():
                raise PermissionError("В базе уже есть пользователи; bootstrap запрещён")
            username = username.strip()
            if not 3 <= len(username) <= 128:
                raise ValueError("Недопустимое имя пользователя")
            self._validate_password(password)
            user_id = secrets.token_hex(16)
            now = int(time.time())
            db.execute("INSERT INTO security_users(user_id,username,password_hash,enabled,created_at,password_changed_at) VALUES(?,?,?,?,?,?)",
                       (user_id, username, self.hasher.hash(password), 1, now, now))
            db.execute("INSERT INTO security_roles(user_id,role_id) VALUES(?,?)", (user_id, "system_administrator"))
            db.execute("INSERT INTO security_meta(key,value) VALUES('bootstrap_closed','1')")
        return UserRecord(user_id, username, True, False)

    @staticmethod
    def _totp(secret: str, at_time: int | None = None, *, step: int = 30, digits: int = 6) -> str:
        key = base64.b32decode(secret.upper() + "=" * ((8 - len(secret) % 8) % 8), casefold=True)
        counter = int((time.time() if at_time is None else at_time) // step)
        digest = hmac.new(key, counter.to_bytes(8, "big"), hashlib.sha1).digest()
        offset = digest[-1] & 0x0F
        number = (int.from_bytes(digest[offset:offset + 4], "big") & 0x7fffffff) % (10 ** digits)
        return str(number).zfill(digits)

    def _require_secret_store(self) -> SecretStore:
        if self.secret_store is None:
            raise SecretStoreError("Для MFA необходимо настроить внешний AVIC Secret Store")
        return self.secret_store

    @staticmethod
    def _totp_context(user_id: str) -> str:
        return "totp:" + user_id

    def _decode_mfa_secret(self, user_id: str, stored: str | None) -> tuple[str | None, bool]:
        """Return (secret, enrollment_pending); legacy plaintext is never silently accepted."""
        if not stored:
            return None, False
        if stored.startswith("avic:v1:"):
            envelope, pending = stored[len("avic:v1:"):], False
        elif stored.startswith("avic-pending:v1:"):
            envelope, pending = stored[len("avic-pending:v1:"):], True
        else:
            raise MFAStorageMigrationRequired(
                "Обнаружен старый MFA-секрет; требуется явная миграция в AVIC Secret Store"
            )
        try:
            value = self._require_secret_store().decrypt(envelope, context=self._totp_context(user_id))
        except SecretStoreError as exc:
            raise AuthenticationError("Не удалось безопасно прочитать MFA-секрет") from exc
        return value, pending

    def begin_totp_enrollment(self, user_id: str) -> str:
        store = self._require_secret_store()
        secret = base64.b32encode(secrets.token_bytes(20)).decode("ascii").rstrip("=")
        encrypted = "avic-pending:v1:" + store.encrypt(secret, context=self._totp_context(user_id))
        with self._db() as db:
            cur = db.execute("UPDATE security_users SET mfa_secret=? WHERE user_id=?", (encrypted, user_id))
            if cur.rowcount != 1:
                raise KeyError(user_id)
        return secret

    def confirm_totp_enrollment(self, user_id: str, code: str) -> None:
        with self._db() as db:
            row = db.execute("SELECT mfa_secret FROM security_users WHERE user_id=?", (user_id,)).fetchone()
            if not row:
                raise AuthenticationError("Нет незавершённой настройки MFA")
            secret, pending = self._decode_mfa_secret(user_id, row["mfa_secret"])
            if not pending or not secret:
                raise AuthenticationError("Нет незавершённой настройки MFA")
            if not self._verify_totp(secret, code):
                raise AuthenticationError("Неверный код MFA")
            envelope = row["mfa_secret"][len("avic-pending:v1:"):]
            db.execute("UPDATE security_users SET mfa_secret=? WHERE user_id=?",
                       ("avic:v1:" + envelope, user_id))

    def disable_totp(self, user_id: str) -> None:
        with self._db() as db:
            db.execute("UPDATE security_users SET mfa_secret=NULL WHERE user_id=?", (user_id,))
            db.execute("UPDATE security_sessions SET revoked=1 WHERE user_id=?", (user_id,))

    def migrate_legacy_totp_secrets(self) -> int:
        """Explicit, transactional conversion of legacy plaintext/pending MFA values."""
        store = self._require_secret_store()
        migrated = 0
        with self._db() as db:
            rows = db.execute("SELECT user_id,mfa_secret FROM security_users WHERE mfa_secret IS NOT NULL").fetchall()
            for row in rows:
                stored = row["mfa_secret"]
                if stored.startswith(("avic:v1:", "avic-pending:v1:")):
                    self._decode_mfa_secret(row["user_id"], stored)
                    continue
                pending = stored.startswith("pending:")
                plaintext = stored[8:] if pending else stored
                encrypted = store.encrypt(plaintext, context=self._totp_context(row["user_id"]))
                prefix = "avic-pending:v1:" if pending else "avic:v1:"
                db.execute("UPDATE security_users SET mfa_secret=? WHERE user_id=?",
                           (prefix + encrypted, row["user_id"]))
                migrated += 1
        return migrated

    def rotate_totp_encryption_key(self, new_store: SecretStore) -> int:
        """Re-encrypt every MFA secret in one SQLite transaction; switch provider only after commit."""
        old_store = self._require_secret_store()
        replacements = []
        with self._db() as db:
            rows = db.execute("SELECT user_id,mfa_secret FROM security_users WHERE mfa_secret IS NOT NULL").fetchall()
            for row in rows:
                stored = row["mfa_secret"]
                if stored.startswith("avic-pending:v1:"):
                    prefix, envelope = "avic-pending:v1:", stored[len("avic-pending:v1:"):]
                elif stored.startswith("avic:v1:"):
                    prefix, envelope = "avic:v1:", stored[len("avic:v1:"):]
                else:
                    raise MFAStorageMigrationRequired("Перед ротацией необходимо выполнить миграцию старых MFA-секретов")
                rotated = SecretStore.rotate_envelope(envelope, context=self._totp_context(row["user_id"]),
                                                       old_store=old_store, new_store=new_store)
                replacements.append((prefix + rotated, row["user_id"]))
            db.executemany("UPDATE security_users SET mfa_secret=? WHERE user_id=?", replacements)
        self.secret_store = new_store
        return len(replacements)

    @classmethod
    def _verify_totp(cls, secret: str, code: str, now: int | None = None) -> bool:
        if not isinstance(code, str) or not code.isdigit() or len(code) != 6:
            return False
        moment = int(time.time()) if now is None else now
        return any(hmac.compare_digest(cls._totp(secret, moment + delta), code) for delta in (-30, 0, 30))

    def login(self, username: str, password: str, *, totp_code: str | None = None) -> AuthenticatedSession:
        now = int(time.time())
        with self._db() as db:
            row = db.execute("SELECT * FROM security_users WHERE username=? COLLATE NOCASE", (username.strip(),)).fetchone()
            # Verify a fixed dummy hash for unknown users to reduce username enumeration timing.
            if row is None:
                try: self.hasher.hash("dummy-password-value")
                except Exception: pass
                raise AuthenticationError("Неверные учётные данные")
            if not row["enabled"]:
                raise AuthenticationError("Неверные учётные данные")
            if row["locked_until"] > now:
                raise AccountLocked("Учётная запись временно заблокирована")
            try:
                valid = self.hasher.verify(row["password_hash"], password)
            except (VerifyMismatchError, VerificationError, TypeError):
                valid = False
            if not valid:
                failures = row["failed_attempts"] + 1
                locked_until = now + self.lockout_seconds if failures >= self.max_failed else 0
                db.execute("UPDATE security_users SET failed_attempts=?,locked_until=? WHERE user_id=?",
                           (0 if locked_until else failures, locked_until, row["user_id"]))
                db.commit()  # failed-attempt state must survive the authentication exception
                if locked_until:
                    raise AccountLocked("Учётная запись временно заблокирована")
                raise AuthenticationError("Неверные учётные данные")
            secret, enrollment_pending = self._decode_mfa_secret(row["user_id"], row["mfa_secret"])
            if enrollment_pending:
                raise AuthenticationError("Сначала завершите настройку MFA")
            if secret and not self._verify_totp(secret, totp_code or ""):
                raise AuthenticationError("Требуется корректный код MFA")
            db.execute("UPDATE security_users SET failed_attempts=0,locked_until=0 WHERE user_id=?", (row["user_id"],))
            token = secrets.token_urlsafe(32)
            csrf = secrets.token_urlsafe(32)
            expires = now + self.session_ttl
            db.execute("INSERT INTO security_sessions(token_hash,user_id,csrf_hash,created_at,expires_at,last_seen,mfa_verified) VALUES(?,?,?,?,?,?,?)",
                       (self._hash_token(token), row["user_id"], self._hash_token(csrf), now, expires, now, int(bool(secret))))
            return AuthenticatedSession(row["user_id"], row["username"], token, csrf, expires, bool(secret))

    @staticmethod
    def _hash_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def authenticate_session(self, token: str, *, csrf_token: str | None = None, require_csrf: bool = False) -> Principal:
        now = int(time.time())
        with self._db() as db:
            row = db.execute("SELECT s.*,u.enabled FROM security_sessions s JOIN security_users u USING(user_id) WHERE token_hash=?",
                             (self._hash_token(token),)).fetchone()
            if (not row or row["revoked"] or not row["enabled"] or row["expires_at"] <= now
                    or row["last_seen"] + self.idle_timeout <= now
                    or (row["break_glass"] and (not row["break_glass_expires_at"]
                                                or row["break_glass_expires_at"] <= now))):
                raise SessionError("Сессия недействительна или истекла")
            if require_csrf and (not csrf_token or not hmac.compare_digest(row["csrf_hash"], self._hash_token(csrf_token))):
                raise SessionError("CSRF-проверка не пройдена")
            db.execute("UPDATE security_sessions SET last_seen=? WHERE token_hash=?", (now, self._hash_token(token)))
            grants = db.execute("SELECT permission_id,installation_id,project_id,station_id FROM security_grants WHERE user_id=?", (row["user_id"],)).fetchall()
            roles = db.execute("SELECT role_id FROM security_roles WHERE user_id=?", (row["user_id"],)).fetchall()
            permissions = {g["permission_id"] for g in grants}
            for role in roles:
                permissions.update(ROLE_PERMISSIONS.get(role["role_id"], ()))
            installation_ids = {g["installation_id"] for g in grants if g["installation_id"]}
            project_ids = {g["project_id"] for g in grants if g["project_id"]}
            station_ids = {g["station_id"] for g in grants if g["station_id"]}
            if "system_administrator" in {r["role_id"] for r in roles}:
                installation_ids = project_ids = station_ids = {"*"}
            return Principal(row["user_id"], frozenset(permissions), frozenset(installation_ids),
                             frozenset(project_ids), frozenset(station_ids))

    def grant(self, user_id: str, permission_id: str, *, installation_id: str | None = None,
              project_id: str | None = None, station_id: str | None = None) -> None:
        if not permission_id or any(ch.isspace() for ch in permission_id):
            raise ValueError("Некорректный permission ID")
        with self._db() as db:
            db.execute("INSERT OR IGNORE INTO security_grants VALUES(?,?,?,?,?)",
                       (user_id, permission_id, installation_id, project_id, station_id))

    def revoke_session(self, token: str) -> None:
        with self._db() as db:
            db.execute("UPDATE security_sessions SET revoked=1 WHERE token_hash=?", (self._hash_token(token),))

    def revoke_all_sessions(self, user_id: str) -> int:
        with self._db() as db:
            cur = db.execute("UPDATE security_sessions SET revoked=1 WHERE user_id=? AND revoked=0", (user_id,))
            return cur.rowcount

    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        self._validate_password(new_password)
        with self._db() as db:
            row = db.execute("SELECT password_hash FROM security_users WHERE user_id=?", (user_id,)).fetchone()
            if not row:
                raise AuthenticationError("Неверные учётные данные")
            try: valid = self.hasher.verify(row["password_hash"], old_password)
            except (VerifyMismatchError, VerificationError, TypeError): valid = False
            if not valid:
                raise AuthenticationError("Неверные учётные данные")
            db.execute("UPDATE security_users SET password_hash=?,password_changed_at=? WHERE user_id=?",
                       (self.hasher.hash(new_password), int(time.time()), user_id))
            db.execute("UPDATE security_sessions SET revoked=1 WHERE user_id=?", (user_id,))

    def _append_security_audit(self, *, actor_id: str, action: str, outcome: str,
                               details: dict | None = None) -> None:
        if self.audit_service is not None:
            self.audit_service.append(actor_id=actor_id, action=action,
                resource_type="security_account", resource_id=actor_id,
                outcome=outcome, details=details or {})

    def create_recovery_codes(self, user_id: str, *, count: int = 8) -> list[str]:
        """Low-level provisioning API; production callers should use issue_recovery_codes()."""
        if not 4 <= count <= 16:
            raise ValueError("Количество recovery-кодов должно быть от 4 до 16")
        codes = [secrets.token_urlsafe(12) for _ in range(count)]
        now = int(time.time())
        with self._db() as db:
            if not db.execute("SELECT 1 FROM security_users WHERE user_id=? AND enabled=1", (user_id,)).fetchone():
                raise KeyError(user_id)
            db.execute("DELETE FROM security_recovery WHERE user_id=?", (user_id,))
            db.executemany("INSERT INTO security_recovery(recovery_hash,user_id,created_at) VALUES(?,?,?)",
                           [(self._hash_token(code), user_id, now) for code in codes])
        self._append_security_audit(actor_id=user_id, action="mfa.recovery_codes.provision",
                                    outcome="success", details={"count": count})
        return codes

    def issue_recovery_codes(self, *, session_token: str, password: str,
                             totp_code: str, count: int = 8) -> list[str]:
        """Issue new codes only from an active MFA-verified session after password+TOTP re-auth."""
        principal = self.authenticate_session(session_token)
        user_id = principal.user_id
        if not self.session_has_mfa(session_token):
            raise AuthenticationError("Для выпуска recovery-кодов требуется MFA-сессия")
        with self._db() as db:
            row = db.execute("SELECT password_hash,mfa_secret FROM security_users WHERE user_id=? AND enabled=1",
                             (user_id,)).fetchone()
            if not row:
                raise AuthenticationError("Неверные учётные данные")
            try:
                valid_password = self.hasher.verify(row["password_hash"], password)
            except (VerifyMismatchError, VerificationError, TypeError):
                valid_password = False
            secret, pending = self._decode_mfa_secret(user_id, row["mfa_secret"])
            if not valid_password or pending or not secret or not self._verify_totp(secret, totp_code):
                self._append_security_audit(actor_id=user_id, action="mfa.recovery_codes.provision",
                                            outcome="denied", details={"reason": "reauth_failed"})
                raise AuthenticationError("Повторная проверка учётных данных не пройдена")
        return self.create_recovery_codes(user_id, count=count)

    def use_recovery_code(self, user_id: str, code: str) -> bool:
        if not isinstance(code, str) or not 12 <= len(code) <= 128:
            return False
        with self._db() as db:
            cur = db.execute("UPDATE security_recovery SET used_at=? WHERE recovery_hash=? AND user_id=? AND used_at IS NULL",
                             (int(time.time()), self._hash_token(code), user_id))
            used = cur.rowcount == 1
        self._append_security_audit(actor_id=user_id, action="mfa.recovery_code.use",
                                    outcome="success" if used else "denied",
                                    details={"reason": "one_time_code"})
        return used

    def break_glass_login(self, username: str, password: str, recovery_code: str, *,
                          reason: str) -> AuthenticatedSession:
        """Time-limited emergency admin session using one recovery code; grants no new RBAC rights."""
        reason = reason.strip() if isinstance(reason, str) else ""
        if not 12 <= len(reason) <= 500:
            raise ValueError("Причина аварийного доступа должна содержать 12–500 символов")
        now = int(time.time())
        with self._db() as db:
            row = db.execute(
                "SELECT u.*, EXISTS(SELECT 1 FROM security_roles r WHERE r.user_id=u.user_id "
                "AND r.role_id='system_administrator') AS is_admin "
                "FROM security_users u WHERE username=? COLLATE NOCASE", (username.strip(),)
            ).fetchone()
            if not row or not row["enabled"] or not row["is_admin"] or row["locked_until"] > now:
                raise AuthenticationError("Аварийный доступ не разрешён")
            try:
                valid_password = self.hasher.verify(row["password_hash"], password)
            except (VerifyMismatchError, VerificationError, TypeError):
                valid_password = False
            if not valid_password:
                raise AuthenticationError("Аварийный доступ не разрешён")
            code_hash = self._hash_token(recovery_code) if isinstance(recovery_code, str) else ""
            cur = db.execute("UPDATE security_recovery SET used_at=? WHERE recovery_hash=? AND user_id=? AND used_at IS NULL",
                             (now, code_hash, row["user_id"]))
            if cur.rowcount != 1:
                raise AuthenticationError("Аварийный доступ не разрешён")
            token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
            expires = now + self.break_glass_ttl
            token_hash = self._hash_token(token)
            db.execute("INSERT INTO security_sessions(token_hash,user_id,csrf_hash,created_at,expires_at,last_seen,"
                       "mfa_verified,break_glass,break_glass_reason,break_glass_expires_at) "
                       "VALUES(?,?,?,?,?,?,1,1,?,?)",
                       (token_hash, row["user_id"], self._hash_token(csrf), now, expires, now, reason, expires))
            db.execute("UPDATE security_sessions SET revoked=1 WHERE user_id=? AND token_hash<>?",
                       (row["user_id"], token_hash))
            user_id, actual_username = row["user_id"], row["username"]
        self._append_security_audit(actor_id=user_id, action="security.break_glass.start",
            outcome="success", details={"reason": reason, "expires_at": expires,
                                         "recovery_code_consumed": True})
        return AuthenticatedSession(user_id, actual_username, token, csrf, expires, True)

    def get_break_glass_status(self, token: str) -> dict:
        now = int(time.time())
        with self._db() as db:
            row = db.execute("SELECT break_glass,break_glass_reason,break_glass_expires_at,revoked "
                             "FROM security_sessions WHERE token_hash=?", (self._hash_token(token),)).fetchone()
        if not row or not row["break_glass"] or row["revoked"]:
            return {"active": False}
        active = bool(row["break_glass_expires_at"] and row["break_glass_expires_at"] > now)
        return {"active": active, "expires_at": row["break_glass_expires_at"],
                "reason": row["break_glass_reason"] if active else None}

    def session_has_mfa(self, token: str) -> bool:
        """Return MFA assurance for a currently valid session without exposing its token hash."""
        now = int(time.time())
        with self._db() as db:
            row = db.execute(
                "SELECT s.mfa_verified,s.expires_at,s.last_seen,s.revoked,u.enabled "
                "FROM security_sessions s JOIN security_users u USING(user_id) WHERE s.token_hash=?",
                (self._hash_token(token),),
            ).fetchone()
            return bool(row and row["mfa_verified"] and not row["revoked"] and row["enabled"]
                        and row["expires_at"] > now and row["last_seen"] + self.idle_timeout > now)
