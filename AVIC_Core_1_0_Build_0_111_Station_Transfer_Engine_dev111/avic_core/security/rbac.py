from dataclasses import dataclass, field
from enum import Enum

class Scope(str, Enum):
    INSTALLATION = "installation"
    PROJECT = "project"
    STATION = "station"

@dataclass(frozen=True)
class Permission:
    permission_id: str
    scope: Scope

@dataclass(frozen=True)
class Principal:
    user_id: str
    permissions: frozenset[str] = frozenset()
    installation_ids: frozenset[str] = frozenset()
    project_ids: frozenset[str] = frozenset()
    station_ids: frozenset[str] = frozenset()

class AccessDenied(PermissionError): pass

class AuthorizationService:
    """Policy primitive. Authentication/session management is a separate service."""
    def require(self, principal: Principal, permission_id: str, *, scope: Scope,
                installation_id: str | None = None, project_id: str | None = None,
                station_id: str | None = None) -> None:
        if permission_id not in principal.permissions and "*" not in principal.permissions:
            raise AccessDenied(f"Missing permission: {permission_id}")
        if scope == Scope.INSTALLATION and "*" not in principal.installation_ids and installation_id not in principal.installation_ids:
            raise AccessDenied("Installation scope denied")
        if scope == Scope.PROJECT and "*" not in principal.project_ids and project_id not in principal.project_ids:
            raise AccessDenied("Project scope denied")
        if scope == Scope.STATION and "*" not in principal.station_ids and station_id not in principal.station_ids:
            raise AccessDenied("Station scope denied")
