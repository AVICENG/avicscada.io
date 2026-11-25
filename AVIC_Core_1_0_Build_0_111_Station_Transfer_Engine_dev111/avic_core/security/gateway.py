"""Framework-neutral mandatory security gateway for AVIC Core service operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from avic_core.audit.service import AuditService
from avic_core.security.auth import SecurityManager, SessionError
from avic_core.security.rbac import AuthorizationService, Scope


@dataclass(frozen=True)
class Operation:
    permission_id: str
    scope: Scope
    resource_type: str
    resource_id: str
    installation_id: str | None = None
    project_id: str | None = None
    station_id: str | None = None
    mutating: bool = False
    require_mfa: bool = False


class SecurityGateway:
    """Single service entry point: authentication -> scope RBAC -> CSRF -> action -> audit.

    API handlers should call execute() rather than invoking domain services directly.
    This class is deliberately framework-neutral; an HTTP adapter must extract the
    session cookie, CSRF header and request origin, and must enforce HTTPS at its edge.
    """
    def __init__(self, security: SecurityManager, audit: AuditService,
                 authorization: AuthorizationService | None = None):
        self.security = security
        self.audit = audit
        self.authorization = authorization or AuthorizationService()

    def execute(self, *, session_token: str, operation: Operation,
                action: Callable[[], Any], csrf_token: str | None = None) -> Any:
        principal = self.security.authenticate_session(
            session_token, csrf_token=csrf_token, require_csrf=operation.mutating
        )
        if operation.require_mfa:
            if not self.security.session_has_mfa(session_token):
                self.audit.append(actor_id=principal.user_id, action=operation.permission_id,
                                  resource_type=operation.resource_type, resource_id=operation.resource_id,
                                  outcome="denied", details={"reason": "mfa_required"})
                raise SessionError("Для операции требуется MFA")
        try:
            self.authorization.require(
                principal, operation.permission_id, scope=operation.scope,
                installation_id=operation.installation_id,
                project_id=operation.project_id, station_id=operation.station_id,
            )
        except PermissionError:
            self.audit.append(actor_id=principal.user_id, action=operation.permission_id,
                              resource_type=operation.resource_type, resource_id=operation.resource_id,
                              outcome="denied", details={"reason": "authorization_denied"})
            raise
        try:
            result = action()
        except Exception as exc:
            self.audit.append(actor_id=principal.user_id, action=operation.permission_id,
                              resource_type=operation.resource_type, resource_id=operation.resource_id,
                              outcome="error", details={"error_type": type(exc).__name__})
            raise
        self.audit.append(actor_id=principal.user_id, action=operation.permission_id,
                          resource_type=operation.resource_type, resource_id=operation.resource_id,
                          outcome="success", details={"mutating": operation.mutating})
        return result
