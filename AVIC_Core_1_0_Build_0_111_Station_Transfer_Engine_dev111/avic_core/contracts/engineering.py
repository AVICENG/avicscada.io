"""Versioned engineering/operations contracts for AVIC Core.

These are immutable domain contracts, not implementations of UI, schedulers,
protocol I/O, HA replication, tenant storage isolation, or backup orchestration.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Mapping
from uuid import uuid4


def _required(**values: str) -> None:
    for name, value in values.items():
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} is required")


def _aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")


class LifecycleStage(str, Enum):
    DESIGN="DESIGN"; DOCUMENT_REVIEW="DOCUMENT_REVIEW"; EQUIPMENT_MODEL="EQUIPMENT_MODEL"
    POINT_MODEL="POINT_MODEL"; LOGIC="LOGIC"; GRAPHICS="GRAPHICS"; CONTROLLER_INTEGRATION="CONTROLLER_INTEGRATION"
    COMMISSIONING="COMMISSIONING"; TESTING="TESTING"; HANDOVER="HANDOVER"; OPERATIONS="OPERATIONS"
    MAINTENANCE="MAINTENANCE"; MODERNIZATION="MODERNIZATION"; ARCHIVED="ARCHIVED"

class WorkStatus(str, Enum):
    NOT_STARTED="NOT_STARTED"; IN_PROGRESS="IN_PROGRESS"; BLOCKED="BLOCKED"; IN_REVIEW="IN_REVIEW"; DONE="DONE"; CANCELLED="CANCELLED"

class TestMode(str, Enum):
    __test__ = False
    SIMULATION="SIMULATION"; OFFLINE="OFFLINE"; LIVE="LIVE"

class TestResult(str, Enum):
    __test__ = False
    NOT_RUN="NOT_RUN"; PASS="PASS"; FAIL="FAIL"; BLOCKED="BLOCKED"; NEEDS_REVIEW="NEEDS_REVIEW"

class PointQuality(str, Enum):
    GOOD="GOOD"; STALE="STALE"; NO_COMMUNICATION="NO_COMMUNICATION"; SENSOR_FAULT="SENSOR_FAULT"
    OUT_OF_RANGE="OUT_OF_RANGE"; UNCERTAIN="UNCERTAIN"; BAD="BAD"; MANUAL="MANUAL"; FORCED="FORCED"; UNKNOWN="UNKNOWN"

class ChangeStatus(str, Enum):
    DRAFT="DRAFT"; SUBMITTED="SUBMITTED"; APPROVED="APPROVED"; REJECTED="REJECTED"; APPLIED="APPLIED"; ROLLED_BACK="ROLLED_BACK"

class MaintenanceKind(str, Enum):
    PREVENTIVE="PREVENTIVE"; CORRECTIVE="CORRECTIVE"; PREDICTIVE="PREDICTIVE"; INSPECTION="INSPECTION"

class FindingKind(str, Enum):
    UNUSED_IO="UNUSED_IO"; CYCLE="CYCLE"; CONFLICTING_COMMAND="CONFLICTING_COMMAND"; MISSING_INTERLOCK="MISSING_INTERLOCK"
    ALARM_SCENARIO="ALARM_SCENARIO"; SENSOR_FAILURE="SENSOR_FAILURE"; COMMUNICATION_LOSS="COMMUNICATION_LOSS"

@dataclass(frozen=True, slots=True)
class LifecycleRecord:
    project_ref: str; stage: LifecycleStage; status: WorkStatus; updated_by: str
    updated_at: datetime; assignee: str | None = None; document_refs: tuple[str,...] = ()
    issue_refs: tuple[str,...] = (); notes: str = ""; record_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self):
        _required(project_ref=self.project_ref, updated_by=self.updated_by); _aware("updated_at",self.updated_at)

@dataclass(frozen=True, slots=True)
class CommissioningTest:
    project_ref: str; station_ref: str; target_ref: str; test_name: str; mode: TestMode
    result: TestResult = TestResult.NOT_RUN; performed_by: str = ""; performed_at: datetime | None = None
    evidence_refs: tuple[str,...] = (); live_command: bool = False; authorization_ref: str | None = None
    test_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self):
        _required(project_ref=self.project_ref,station_ref=self.station_ref,target_ref=self.target_ref,test_name=self.test_name)
        if self.performed_at is not None: _aware("performed_at",self.performed_at)
        if self.mode is not TestMode.LIVE and self.live_command: raise ValueError("live_command requires LIVE mode")
        if self.live_command and not (self.performed_by.strip() and self.authorization_ref and self.authorization_ref.strip()):
            raise ValueError("live command requires performer and explicit authorization reference")

@dataclass(frozen=True, slots=True)
class ChangeRequest:
    project_ref: str; title: str; reason: str; requested_by: str; created_at: datetime
    before_digest: str; after_digest: str; status: ChangeStatus = ChangeStatus.DRAFT
    approved_by: str | None = None; approval_ref: str | None = None; change_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self):
        _required(project_ref=self.project_ref,title=self.title,reason=self.reason,requested_by=self.requested_by,before_digest=self.before_digest,after_digest=self.after_digest)
        _aware("created_at",self.created_at)
        if self.status in {ChangeStatus.APPROVED,ChangeStatus.APPLIED} and not (self.approved_by and self.approved_by.strip() and self.approval_ref and self.approval_ref.strip()):
            raise ValueError("approved/applied change requires approver and approval reference")

@dataclass(frozen=True, slots=True)
class AssetPassport:
    asset_ref: str; parent_asset_ref: str | None; name: str; asset_type: str
    project_ref: str; station_ref: str; manufacturer: str = ""; model: str = ""; serial_number: str = ""
    document_refs: tuple[str,...] = (); point_refs: tuple[str,...] = (); controller_refs: tuple[str,...] = ()
    def __post_init__(self): _required(asset_ref=self.asset_ref,name=self.name,asset_type=self.asset_type,project_ref=self.project_ref,station_ref=self.station_ref)

@dataclass(frozen=True, slots=True)
class MaintenanceWorkOrder:
    asset_ref: str; kind: MaintenanceKind; title: str; created_at: datetime; created_by: str
    due_at: datetime | None = None; assignee: str | None = None; procedure_ref: str | None = None
    status: WorkStatus = WorkStatus.NOT_STARTED; work_order_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self):
        _required(asset_ref=self.asset_ref,title=self.title,created_by=self.created_by); _aware("created_at",self.created_at)
        if self.due_at is not None: _aware("due_at",self.due_at)

@dataclass(frozen=True, slots=True)
class LogicVerificationFinding:
    project_ref: str; graph_ref: str; kind: FindingKind; description: str
    node_refs: tuple[str,...] = (); severity: str = "WARNING"; finding_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self): _required(project_ref=self.project_ref,graph_ref=self.graph_ref,description=self.description)

@dataclass(frozen=True, slots=True)
class PointQualityState:
    point_ref: str; quality: PointQuality; observed_at: datetime; source_ref: str
    diagnostic: str = ""; is_control_eligible: bool = False
    def __post_init__(self):
        _required(point_ref=self.point_ref,source_ref=self.source_ref); _aware("observed_at",self.observed_at)
        if self.quality is not PointQuality.GOOD and self.is_control_eligible:
            raise ValueError("non-GOOD point quality cannot be control eligible")

@dataclass(frozen=True, slots=True)
class SecurityRecoveryEvent:
    station_ref: str; event_type: str; occurred_at: datetime; actor: str
    result: str; evidence_ref: str | None = None; event_id: str = field(default_factory=lambda: str(uuid4()))
    def __post_init__(self): _required(station_ref=self.station_ref,event_type=self.event_type,actor=self.actor,result=self.result); _aware("occurred_at",self.occurred_at)

@dataclass(frozen=True, slots=True)
class ReportRequest:
    project_ref: str; report_type: str; requested_by: str; requested_at: datetime
    period_start: datetime | None = None; period_end: datetime | None = None
    format: str = "PDF"; filters: Mapping[str,str] = field(default_factory=dict)
    def __post_init__(self):
        _required(project_ref=self.project_ref,report_type=self.report_type,requested_by=self.requested_by)
        _aware("requested_at",self.requested_at)
        if self.format.upper() not in {"PDF","DOCX","XLSX","CSV"}: raise ValueError("unsupported report format")
        if self.period_start is not None: _aware("period_start",self.period_start)
        if self.period_end is not None: _aware("period_end",self.period_end)
        if self.period_start and self.period_end and self.period_start > self.period_end: raise ValueError("period_start must not exceed period_end")

@dataclass(frozen=True, slots=True)
class SystemHealthCheck:
    component_ref: str; checked_at: datetime; status: str; metric_values: Mapping[str,float] = field(default_factory=dict)
    diagnostics: tuple[str,...] = ()
    def __post_init__(self): _required(component_ref=self.component_ref,status=self.status); _aware("checked_at",self.checked_at)

@dataclass(frozen=True, slots=True)
class TenantScope:
    tenant_id: str; project_id: str | None = None; station_id: str | None = None
    def __post_init__(self): _required(tenant_id=self.tenant_id)

@dataclass(frozen=True, slots=True)
class HighAvailabilityPolicy:
    group_id: str; mode: str; failover_requires_fencing: bool = True; max_data_loss_seconds: int = 0
    def __post_init__(self):
        _required(group_id=self.group_id,mode=self.mode)
        if self.mode not in {"ACTIVE_PASSIVE","ACTIVE_ACTIVE"}: raise ValueError("unsupported HA mode")
        if self.max_data_loss_seconds < 0: raise ValueError("max_data_loss_seconds cannot be negative")

@dataclass(frozen=True, slots=True)
class IntegrationClient:
    client_id: str; api_version: str; tenant_scope: TenantScope; permissions: frozenset[str]
    def __post_init__(self): _required(client_id=self.client_id,api_version=self.api_version)
