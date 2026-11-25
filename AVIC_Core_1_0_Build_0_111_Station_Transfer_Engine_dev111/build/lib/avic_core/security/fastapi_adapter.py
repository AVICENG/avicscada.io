"""Optional FastAPI/Starlette transport adapter for AVIC SecurityGateway.

The adapter hardens the HTTP boundary; route handlers must still use the
AuthorizedOperation dependency to ensure the domain action is executed through
SecurityGateway (and therefore RBAC/scope/CSRF/audit).
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlsplit

from avic_core.security.gateway import Operation, SecurityGateway
from avic_core.security.auth import SessionError

try:
    from fastapi import Depends, HTTPException, Request, Response
except ImportError as exc:  # pragma: no cover - exercised in minimal installations
    raise RuntimeError("FastAPI adapter requires fastapi; install avic-core[http]") from exc


@dataclass(frozen=True)
class HttpSecurityConfig:
    allowed_origins: frozenset[str]
    https_required: bool = True
    allow_loopback_http: bool = False
    session_cookie_name: str = "avic_session"
    cookie_secure: bool = True
    cookie_samesite: str = "strict"
    rate_limit_requests: int = 30
    rate_limit_window_seconds: int = 60
    rate_limit_paths: tuple[str, ...] = ("/auth/login",)

    def __post_init__(self) -> None:
        if not self.allowed_origins:
            raise ValueError("Необходимо явно задать allowlist Origin")
        if self.cookie_samesite.lower() not in {"strict", "lax", "none"}:
            raise ValueError("Недопустимое значение SameSite")
        if self.cookie_samesite.lower() == "none" and not self.cookie_secure:
            raise ValueError("SameSite=None требует Secure cookie")
        if self.https_required and not self.cookie_secure:
            raise ValueError("HTTPS-режим требует Secure cookie")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if parsed.scheme not in {"https", "http"} or not parsed.netloc or parsed.path or parsed.query or parsed.fragment:
                raise ValueError(f"Некорректный Origin в allowlist: {origin}")
            if parsed.scheme != "https" and not self.allow_loopback_http:
                raise ValueError("HTTP Origin разрешён только в явном loopback development режиме")


class _WindowLimiter:
    """Per-process limiter. Use a shared gateway limiter at multi-worker deployment."""
    def __init__(self, limit: int, window: int):
        if limit < 1 or window < 1:
            raise ValueError("Параметры rate limit должны быть положительными")
        self.limit, self.window = limit, window
        self._hits: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: tuple[str, str], now: float | None = None) -> bool:
        moment = time.monotonic() if now is None else now
        with self._lock:
            hits = self._hits[key]
            while hits and hits[0] <= moment - self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                return False
            hits.append(moment)
            return True


class AVICSecurityMiddleware:
    """Pure ASGI middleware: transport, Origin, basic rate-limit and headers."""
    def __init__(self, app: Any, config: HttpSecurityConfig):
        self.app, self.config = app, config
        self.limiter = _WindowLimiter(config.rate_limit_requests, config.rate_limit_window_seconds)
        self._allowed = {origin.rstrip("/") for origin in config.allowed_origins}

    @staticmethod
    def _headers(scope: dict) -> dict[bytes, bytes]:
        return {k.lower(): v for k, v in scope.get("headers", [])}

    @staticmethod
    def _loopback(host: str | None) -> bool:
        return host in {"127.0.0.1", "::1", "localhost", "testclient"}

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        headers = self._headers(scope)
        method = scope.get("method", "GET").upper()
        client = scope.get("client") or ("unknown", 0)
        client_ip = str(client[0])
        scheme = scope.get("scheme", "http")
        host = client_ip
        if self.config.https_required and scheme != "https":
            if not (self.config.allow_loopback_http and self._loopback(host)):
                await self._reject(send, 400, b"HTTPS required")
                return
        origin = headers.get(b"origin")
        if origin:
            origin_text = origin.decode("latin1").rstrip("/")
            if origin_text not in self._allowed:
                await self._reject(send, 403, b"Origin denied")
                return
        if method not in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            if not origin:
                await self._reject(send, 403, b"Origin required")
                return
            if origin.decode("latin1").rstrip("/") not in self._allowed:
                await self._reject(send, 403, b"Origin denied")
                return
        path = scope.get("path", "")
        if path in self.config.rate_limit_paths and not self.limiter.allow((client_ip, path)):
            await self._reject(send, 429, b"Rate limit exceeded")
            return

        async def send_with_headers(message: dict) -> None:
            if message["type"] == "http.response.start":
                extra = [
                    (b"x-content-type-options", b"nosniff"),
                    (b"x-frame-options", b"DENY"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"cache-control", b"no-store"),
                    (b"content-security-policy", b"default-src 'self'; frame-ancestors 'none'"),
                ]
                existing = {k.lower() for k, _ in message.get("headers", [])}
                message["headers"] = list(message.get("headers", [])) + [(k, v) for k, v in extra if k not in existing]
            await send(message)
        await self.app(scope, receive, send_with_headers)

    @staticmethod
    async def _reject(send: Callable, status: int, body: bytes) -> None:
        await send({"type": "http.response.start", "status": status,
                    "headers": [(b"content-type", b"text/plain; charset=utf-8"), (b"cache-control", b"no-store")]})
        await send({"type": "http.response.body", "body": body})


@dataclass
class AuthorizedOperation:
    gateway: SecurityGateway
    session_token: str
    csrf_token: str | None
    operation: Operation

    def execute(self, action: Callable[[], Any]) -> Any:
        try:
            return self.gateway.execute(session_token=self.session_token, csrf_token=self.csrf_token,
                                        operation=self.operation, action=action)
        except SessionError as exc:
            raise HTTPException(status_code=401, detail="Authentication or CSRF validation failed") from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail="Permission denied") from exc


def authorized_operation(gateway: SecurityGateway, operation: Operation | Callable[[Request], Operation],
                         *, cookie_name: str = "avic_session") -> Callable:
    """Build a FastAPI dependency. Route must call dependency.execute(action).

    Pass an Operation for fixed resources, or a Request -> Operation factory when
    the resource identifier comes from a path/query parameter.
    """
    def dependency(request: Request) -> AuthorizedOperation:
        token = request.cookies.get(cookie_name)
        if not token:
            raise HTTPException(status_code=401, detail="Authentication required")
        csrf = request.headers.get("x-avic-csrf")
        resolved = operation(request) if callable(operation) else operation
        return AuthorizedOperation(gateway, token, csrf, resolved)
    return Depends(dependency)


def set_session_cookie(response: Response, session: Any, config: HttpSecurityConfig) -> dict[str, Any]:
    """Set opaque session cookie and return CSRF token for the client memory store."""
    response.set_cookie(
        key=config.session_cookie_name, value=session.token, max_age=max(0, session.expires_at - int(time.time())),
        httponly=True, secure=config.cookie_secure, samesite=config.cookie_samesite.lower(),
        path="/",)
    return {"csrf_token": session.csrf_token, "expires_at": session.expires_at}


def clear_session_cookie(response: Response, config: HttpSecurityConfig) -> None:
    response.delete_cookie(key=config.session_cookie_name, path="/", secure=config.cookie_secure,
                           httponly=True, samesite=config.cookie_samesite.lower())


class UnprotectedRouteError(RuntimeError):
    """Raised when a mutating FastAPI route lacks an explicit security marker."""


def security_gateway_protected(endpoint: Callable) -> Callable:
    """Mark an endpoint whose domain action is enforced through AuthorizedOperation.

    This marker is a startup coverage assertion, not a substitute for calling
    AuthorizedOperation.execute() in the endpoint implementation.
    """
    setattr(endpoint, "__avic_security_gateway_protected__", True)
    return endpoint


def validate_security_routes(app: Any, *, public_mutation_routes: dict[str, str] | None = None) -> None:
    """Fail closed if any unsafe API route is neither protected nor explicitly public.

    `public_mutation_routes` maps exact route paths to a non-empty rationale.
    Keep this list small (e.g. login endpoints); never use broad wildcards.
    Call after all routers have been included and before serving requests.
    """
    public = public_mutation_routes or {}
    invalid_public = [path for path, reason in public.items() if not path or not isinstance(reason, str) or not reason.strip()]
    if invalid_public:
        raise ValueError(f"Для публичных изменяющих маршрутов нужна причина: {invalid_public}")

    unsafe = {"POST", "PUT", "PATCH", "DELETE"}
    missing: list[str] = []
    for route in getattr(app, "routes", []):
        methods = set(getattr(route, "methods", None) or ()) & unsafe
        if not methods:
            continue
        path = getattr(route, "path", "<unknown>")
        endpoint = getattr(route, "endpoint", None)
        if path in public:
            continue
        if not getattr(endpoint, "__avic_security_gateway_protected__", False):
            missing.append(f"{','.join(sorted(methods))} {path}")
    if missing:
        details = "; ".join(sorted(missing))
        raise UnprotectedRouteError("Обнаружены изменяющие маршруты без AVIC Security Gateway: " + details)
