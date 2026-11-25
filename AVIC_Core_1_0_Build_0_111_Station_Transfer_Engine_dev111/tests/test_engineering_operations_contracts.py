from datetime import datetime, timezone
import pytest
from avic_core.contracts import (
    AssetPassport, ChangeRequest, ChangeStatus, CommissioningTest, FindingKind,
    HighAvailabilityPolicy, IntegrationClient, LifecycleRecord, LifecycleStage,
    LogicVerificationFinding, MaintenanceKind, MaintenanceWorkOrder, PointQuality,
    PointQualityState, ReportRequest, SecurityRecoveryEvent, SystemHealthCheck,
    TenantScope, TestMode, TestResult, WorkStatus,
)
NOW = datetime.now(timezone.utc)

def test_lifecycle_record_requires_project_and_actor():
    item = LifecycleRecord("project-1", LifecycleStage.DESIGN, WorkStatus.IN_PROGRESS, "engineer", NOW)
    assert item.stage is LifecycleStage.DESIGN
    with pytest.raises(ValueError): LifecycleRecord(" ", LifecycleStage.DESIGN, WorkStatus.DONE, "x", NOW)

def test_live_commissioning_requires_explicit_authorization():
    with pytest.raises(ValueError):
        CommissioningTest("p", "s", "point-1", "actuator stroke", TestMode.LIVE, live_command=True)
    item = CommissioningTest("p", "s", "point-1", "actuator stroke", TestMode.LIVE,
                             TestResult.PASS, "engineer", NOW, live_command=True, authorization_ref="permit-42")
    assert item.live_command

def test_offline_test_cannot_claim_live_command():
    with pytest.raises(ValueError):
        CommissioningTest("p", "s", "x", "test", TestMode.OFFLINE, live_command=True)

def test_change_approval_requires_identity_and_evidence():
    with pytest.raises(ValueError):
        ChangeRequest("p", "setpoint update", "approved by supervisor", "eng", NOW,
                      "a"*64, "b"*64, ChangeStatus.APPROVED)
    approved = ChangeRequest("p", "setpoint update", "energy optimization", "eng", NOW,
                             "a"*64, "b"*64, ChangeStatus.APPROVED, "chief", "approval-7")
    assert approved.approved_by == "chief"

def test_asset_passport_supports_hierarchical_parent_and_separate_refs():
    asset = AssetPassport("asset-ahu-1", "asset-floor-1", "AHU-1", "AIR_HANDLING_UNIT",
                          "project", "station", point_refs=("point-supply-temp",), controller_refs=("ctrl-1",))
    assert asset.parent_asset_ref == "asset-floor-1"
    assert asset.point_refs != asset.controller_refs

def test_maintenance_order_has_timezone_aware_dates():
    order = MaintenanceWorkOrder("asset-1", MaintenanceKind.PREVENTIVE, "Filter inspection", NOW, "planner")
    assert order.status is WorkStatus.NOT_STARTED
    with pytest.raises(ValueError):
        MaintenanceWorkOrder("asset-1", MaintenanceKind.CORRECTIVE, "Repair", datetime.now(), "planner")

def test_non_good_quality_cannot_be_control_eligible():
    with pytest.raises(ValueError):
        PointQualityState("point-1", PointQuality.STALE, NOW, "driver-1", is_control_eligible=True)
    good = PointQualityState("point-1", PointQuality.GOOD, NOW, "driver-1", is_control_eligible=True)
    assert good.is_control_eligible

def test_logic_verification_finding_is_traceable_to_project_and_graph():
    finding = LogicVerificationFinding("p", "fbd-1", FindingKind.MISSING_INTERLOCK,
                                       "Pump start path has no low-level interlock", ("node-1", "node-2"))
    assert finding.node_refs == ("node-1", "node-2")

def test_report_request_validates_period_and_format():
    ReportRequest("p", "commissioning", "chief", NOW, format="PDF")
    with pytest.raises(ValueError): ReportRequest("p", "x", "chief", NOW, format="EXE")
    with pytest.raises(ValueError): ReportRequest("p", "x", "chief", NOW, NOW, datetime(2020,1,1,tzinfo=timezone.utc))

def test_security_recovery_and_health_are_auditable():
    event = SecurityRecoveryEvent("station-1", "BACKUP_VERIFIED", NOW, "admin", "SUCCESS", "backup-9")
    health = SystemHealthCheck("runtime-1", NOW, "HEALTHY", {"queue_depth": 0.0})
    assert event.evidence_ref == "backup-9" and health.metric_values["queue_depth"] == 0.0

def test_tenant_scope_and_integration_client_require_tenant_boundary():
    scope = TenantScope("tenant-a", "project-a", "station-a")
    client = IntegrationClient("erp-sync", "1.0", scope, frozenset({"assets:read"}))
    assert client.tenant_scope.tenant_id == "tenant-a"
    with pytest.raises(ValueError): TenantScope(" ")

def test_ha_policy_requires_explicit_supported_mode_and_safe_fencing_default():
    policy = HighAvailabilityPolicy("cluster-1", "ACTIVE_PASSIVE")
    assert policy.failover_requires_fencing is True
    with pytest.raises(ValueError): HighAvailabilityPolicy("cluster-1", "AUTO_MAGIC")
    with pytest.raises(ValueError): HighAvailabilityPolicy("cluster-1", "ACTIVE_PASSIVE", max_data_loss_seconds=-1)
