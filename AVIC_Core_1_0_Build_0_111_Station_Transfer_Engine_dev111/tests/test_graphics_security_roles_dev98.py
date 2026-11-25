import pytest
from avic_core.security.auth import SecurityManager
from avic_core.security.rbac import AccessDenied, AuthorizationService, Scope
from avic_core.security.graphics_policy import GraphicsSecurityPolicy


def test_avic_operator_can_start_stop_but_cannot_configure_graphics_or_setpoints(tmp_path):
    security = SecurityManager(tmp_path / "security.db")
    user = security.create_user("operator_new", "StrongPassword123", roles=["avic_operator"])
    security.grant(user.user_id, "station.read", station_id="station-1")
    security.grant(user.user_id, "equipment.command.start", station_id="station-1")
    security.grant(user.user_id, "equipment.command.stop", station_id="station-1")
    principal = security.authenticate_session(security.login("operator_new", "StrongPassword123").token)
    policy = GraphicsSecurityPolicy()
    policy.require_equipment_command(principal, "station-1", action="start")
    policy.require_equipment_command(principal, "station-1", action="stop")
    with pytest.raises(AccessDenied):
        policy.require_graphics_configure(principal, "station-1")
    with pytest.raises(AccessDenied):
        policy.require_setpoint_write(principal, "station-1")


def test_avic_engineer_can_configure_graphics_but_not_assign_security_roles(tmp_path):
    security = SecurityManager(tmp_path / "security.db")
    user = security.create_user("engineer_new", "StrongPassword123", roles=["avic_engineer"])
    security.grant(user.user_id, "graphics.configure", station_id="station-1")
    security.grant(user.user_id, "graphics.binding.configure", station_id="station-1")
    principal = security.authenticate_session(security.login("engineer_new", "StrongPassword123").token)
    policy = GraphicsSecurityPolicy()
    policy.require_graphics_configure(principal, "station-1")
    policy.require_binding_configure(principal, "station-1")
    with pytest.raises(AccessDenied):
        AuthorizationService().require(principal, "role.assign", scope=Scope.STATION, station_id="station-1")


def test_station_scope_is_required_even_when_role_has_permission(tmp_path):
    security = SecurityManager(tmp_path / "security.db")
    user = security.create_user("viewer_new", "StrongPassword123", roles=["avic_viewer"])
    security.grant(user.user_id, "graphics.read", station_id="station-A")
    principal = security.authenticate_session(security.login("viewer_new", "StrongPassword123").token)
    policy = GraphicsSecurityPolicy()
    policy.require_graphics_read(principal, "station-A")
    with pytest.raises(AccessDenied):
        policy.require_graphics_read(principal, "station-B")
