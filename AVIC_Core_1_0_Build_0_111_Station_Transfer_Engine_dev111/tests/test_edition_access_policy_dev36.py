from avic_core.licensing.manager import LicenseStatus
from avic_core.security.edition_policy import (
    Capability, CommercialEdition, EditionAccessDenied, EditionAccessPolicy,
)
from avic_core.security.rbac import Principal


def license(*features, valid=True):
    return LicenseStatus(valid, "OK" if valid else "INVALID_SIGNATURE", "host", "customer", 100,
                         tuple(features), "license-id")


def principal(*permissions):
    return Principal("user-1", frozenset(permissions), frozenset({"*"}),
                     frozenset({"*"}), frozenset({"*"}))


def test_customer_edition_allows_web_operation_with_license_and_permission():
    policy = EditionAccessPolicy()
    result = policy.evaluate(principal("point.read"), license("web.operate"),
                             Capability.WEB_OPERATE, CommercialEdition.CUSTOMER)
    assert result.allowed and result.reason == "OK"


def test_customer_edition_cannot_use_engineering_even_if_user_permission_exists():
    policy = EditionAccessPolicy()
    result = policy.evaluate(principal("driver.configure"),
                             license("engineering.discovery"),
                             Capability.ENGINEERING_DISCOVERY, CommercialEdition.CUSTOMER)
    assert not result.allowed
    assert result.reason == "CAPABILITY_NOT_INCLUDED_IN_EDITION"


def test_integrator_requires_both_license_feature_and_rbac():
    policy = EditionAccessPolicy()
    lic = license("engineering.graphics_edit")
    assert not policy.evaluate(principal("point.read"), lic,
                               Capability.ENGINEERING_GRAPHICS_EDIT,
                               CommercialEdition.INTEGRATOR).allowed
    assert policy.evaluate(principal("graphics.edit"), lic,
                            Capability.ENGINEERING_GRAPHICS_EDIT,
                            CommercialEdition.INTEGRATOR).allowed


def test_developer_capability_not_available_in_integrator_edition():
    decision = EditionAccessPolicy().evaluate(
        principal("developer.core_debug"), license("developer.core_debug"),
        Capability.DEVELOPER_CORE_DEBUG, CommercialEdition.INTEGRATOR)
    assert not decision.allowed
    assert decision.reason == "CAPABILITY_NOT_INCLUDED_IN_EDITION"


def test_invalid_license_fails_closed():
    decision = EditionAccessPolicy().evaluate(
        principal("point.read"), license("web.operate", valid=False),
        Capability.WEB_OPERATE, CommercialEdition.CUSTOMER)
    assert not decision.allowed and decision.reason == "LICENSE_INVALID"


def test_require_raises_with_machine_readable_reason():
    policy = EditionAccessPolicy()
    try:
        policy.require(principal("point.read"), license("web.operate"),
                       Capability.ENGINEERING_DEPLOY, CommercialEdition.CUSTOMER)
    except EditionAccessDenied as exc:
        assert exc.decision.reason == "CAPABILITY_NOT_INCLUDED_IN_EDITION"
    else:
        raise AssertionError("Expected EditionAccessDenied")
