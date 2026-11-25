"""Server-side commercial-edition and capability enforcement for AVIC.

UI visibility is deliberately irrelevant here: every protected application
operation must ask this policy (or a facade built on it) before execution.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

from avic_core.licensing.manager import LicenseStatus
from avic_core.security.rbac import Principal


class CommercialEdition(StrEnum):
    CUSTOMER = "customer_runtime"
    INTEGRATOR = "integrator_workbench"
    DEVELOPER = "avic_developer"


class Capability(StrEnum):
    WEB_OPERATE = "web.operate"
    WEB_ADMINISTER = "web.administer"
    ENGINEERING_DISCOVERY = "engineering.discovery"
    ENGINEERING_DEVICE_IMPORT = "engineering.device_import"
    ENGINEERING_GRAPHICS_EDIT = "engineering.graphics_edit"
    ENGINEERING_LOGIC_EDIT = "engineering.logic_edit"
    ENGINEERING_DEPLOY = "engineering.deploy"
    PLATFORM_NETWORK_CONFIGURE = "platform.network.configure"
    DEVELOPER_SDK = "developer.sdk"
    DEVELOPER_DRIVER_BUILD = "developer.driver_build"
    DEVELOPER_CORE_DEBUG = "developer.core_debug"


CAPABILITY_PERMISSION: dict[Capability, str] = {
    Capability.WEB_OPERATE: "point.read",
    Capability.WEB_ADMINISTER: "user.manage",
    Capability.ENGINEERING_DISCOVERY: "driver.configure",
    Capability.ENGINEERING_DEVICE_IMPORT: "point.create",
    Capability.ENGINEERING_GRAPHICS_EDIT: "graphics.edit",
    Capability.ENGINEERING_LOGIC_EDIT: "logic.edit",
    Capability.ENGINEERING_DEPLOY: "logic.deploy",
    Capability.PLATFORM_NETWORK_CONFIGURE: "platform.network.configure",
    Capability.DEVELOPER_SDK: "developer.sdk",
    Capability.DEVELOPER_DRIVER_BUILD: "developer.driver_build",
    Capability.DEVELOPER_CORE_DEBUG: "developer.core_debug",
}

# A capability must be present in the signed license feature list as well as
# permitted by the principal. No client-supplied edition string is trusted.
EDITION_CAPABILITIES: dict[CommercialEdition, frozenset[Capability]] = {
    CommercialEdition.CUSTOMER: frozenset({Capability.WEB_OPERATE, Capability.WEB_ADMINISTER}),
    CommercialEdition.INTEGRATOR: frozenset({
        Capability.WEB_OPERATE, Capability.WEB_ADMINISTER,
        Capability.ENGINEERING_DISCOVERY, Capability.ENGINEERING_DEVICE_IMPORT,
        Capability.ENGINEERING_GRAPHICS_EDIT, Capability.ENGINEERING_LOGIC_EDIT,
        Capability.ENGINEERING_DEPLOY, Capability.PLATFORM_NETWORK_CONFIGURE,
    }),
    CommercialEdition.DEVELOPER: frozenset(Capability),
}


@dataclass(frozen=True)
class AccessDecision:
    allowed: bool
    reason: str
    capability: str
    edition: str


class EditionAccessDenied(PermissionError):
    def __init__(self, decision: AccessDecision):
        self.decision = decision
        super().__init__(f"Доступ запрещён: {decision.reason} ({decision.capability})")


class EditionAccessPolicy:
    """Combines signed edition features with user RBAC permissions."""

    def evaluate(self, principal: Principal, license_status: LicenseStatus,
                 capability: Capability | str, edition: CommercialEdition | str) -> AccessDecision:
        cap = Capability(capability)
        selected_edition = CommercialEdition(edition)
        if not license_status.valid:
            return AccessDecision(False, "LICENSE_INVALID", cap.value, selected_edition.value)
        if cap not in EDITION_CAPABILITIES[selected_edition]:
            return AccessDecision(False, "CAPABILITY_NOT_INCLUDED_IN_EDITION", cap.value, selected_edition.value)
        # License features are signed by AVIC. Wildcards are intentionally not
        # accepted: a license must explicitly name every enabled capability.
        if cap.value not in set(license_status.features):
            return AccessDecision(False, "FEATURE_NOT_LICENSED", cap.value, selected_edition.value)
        permission = CAPABILITY_PERMISSION[cap]
        if permission not in principal.permissions and "*" not in principal.permissions:
            return AccessDecision(False, "RBAC_PERMISSION_DENIED", cap.value, selected_edition.value)
        return AccessDecision(True, "OK", cap.value, selected_edition.value)

    def require(self, principal: Principal, license_status: LicenseStatus,
                capability: Capability | str, edition: CommercialEdition | str) -> None:
        decision = self.evaluate(principal, license_status, capability, edition)
        if not decision.allowed:
            raise EditionAccessDenied(decision)
