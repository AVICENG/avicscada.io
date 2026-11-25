"""Architecture contracts for AVIC Engineering Intelligence.

These immutable contracts describe role workspaces and document-analysis
artifacts. They do not implement parsers, AI inference, UI, or project writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Mapping
from uuid import uuid4


class EngineeringRole(str, Enum):
    CHIEF_ENGINEER = "CHIEF_ENGINEER"
    ENGINEER = "ENGINEER"
    OPERATOR = "OPERATOR"
    ADMINISTRATOR = "ADMINISTRATOR"
    VIEWER = "VIEWER"


class WorkspaceArea(str, Enum):
    FLEET_OVERVIEW = "FLEET_OVERVIEW"
    TECHNICAL_HEALTH = "TECHNICAL_HEALTH"
    ALARMS_AND_EVENTS = "ALARMS_AND_EVENTS"
    PERFORMANCE_ANALYTICS = "PERFORMANCE_ANALYTICS"
    MAINTENANCE_AND_COMPLIANCE = "MAINTENANCE_AND_COMPLIANCE"
    ENGINEERING_PROJECTS = "ENGINEERING_PROJECTS"
    DEVICE_INTEGRATION = "DEVICE_INTEGRATION"
    LOGIC_AND_FBD = "LOGIC_AND_FBD"
    GRAPHICS_AND_MIMICS = "GRAPHICS_AND_MIMICS"
    TRENDS_AND_DIAGNOSTICS = "TRENDS_AND_DIAGNOSTICS"
    DOCUMENT_INTELLIGENCE = "DOCUMENT_INTELLIGENCE"
    REPORTING = "REPORTING"
    AUDIT_AND_CHANGE_CONTROL = "AUDIT_AND_CHANGE_CONTROL"


class DocumentKind(str, Enum):
    PDF = "PDF"
    DOCX = "DOCX"
    XLSX = "XLSX"
    DWG = "DWG"
    DXF = "DXF"
    IFC = "IFC"
    IMAGE = "IMAGE"
    CSV = "CSV"
    TEXT = "TEXT"
    OTHER = "OTHER"


class AnalysisStage(str, Enum):
    RECEIVED = "RECEIVED"
    INDEXING = "INDEXING"
    EXTRACTING = "EXTRACTING"
    CLASSIFYING = "CLASSIFYING"
    CROSS_CHECKING = "CROSS_CHECKING"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class FindingSeverity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReviewState(str, Enum):
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


@dataclass(frozen=True, slots=True)
class WorkspaceDefinition:
    role: EngineeringRole
    areas: frozenset[WorkspaceArea]
    read_only: bool = False

    def __post_init__(self) -> None:
        if not self.areas:
            raise ValueError("workspace must expose at least one area")
        if self.role is EngineeringRole.VIEWER and not self.read_only:
            raise ValueError("viewer workspace must be read-only")


@dataclass(frozen=True, slots=True)
class DocumentArtifact:
    name: str
    kind: DocumentKind
    source_uri: str
    content_sha256: str
    uploaded_by: str
    uploaded_at: datetime
    project_ref: str | None = None
    station_ref: str | None = None
    revision: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
    document_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.name.strip() or not self.source_uri.strip() or not self.uploaded_by.strip():
            raise ValueError("document name, source_uri and uploaded_by are required")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdefABCDEF" for c in self.content_sha256):
            raise ValueError("content_sha256 must be a 64-character hexadecimal digest")
        if self.uploaded_at.tzinfo is None or self.uploaded_at.utcoffset() is None:
            raise ValueError("uploaded_at must be timezone-aware")


@dataclass(frozen=True, slots=True)
class DocumentEvidence:
    document_id: str
    locator: str
    excerpt: str
    extraction_method: str
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not self.document_id.strip() or not self.locator.strip() or not self.extraction_method.strip():
            raise ValueError("document_id, locator and extraction_method are required")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class EngineeringFinding:
    title: str
    description: str
    severity: FindingSeverity
    evidence: tuple[DocumentEvidence, ...]
    recommendation: str = ""
    confidence: float | None = None
    review_state: ReviewState = ReviewState.DRAFT
    finding_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.title.strip() or not self.description.strip():
            raise ValueError("finding title and description are required")
        if not self.evidence:
            raise ValueError("engineering finding must cite at least one evidence item")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if self.review_state is ReviewState.ACCEPTED and not self.recommendation.strip():
            # Acceptance is a human review decision; require a recorded disposition.
            raise ValueError("accepted finding requires a recorded recommendation/disposition")


@dataclass(frozen=True, slots=True)
class DocumentAnalysisJob:
    document_ids: tuple[str, ...]
    requested_by: str
    requested_at: datetime
    stages: tuple[AnalysisStage, ...] = (
        AnalysisStage.RECEIVED,
        AnalysisStage.INDEXING,
        AnalysisStage.EXTRACTING,
        AnalysisStage.CLASSIFYING,
        AnalysisStage.CROSS_CHECKING,
        AnalysisStage.REVIEW_REQUIRED,
    )
    job_id: str = field(default_factory=lambda: str(uuid4()))

    def __post_init__(self) -> None:
        if not self.document_ids or any(not item.strip() for item in self.document_ids):
            raise ValueError("at least one non-empty document_id is required")
        if not self.requested_by.strip():
            raise ValueError("requested_by is required")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("requested_at must be timezone-aware")
        if not self.stages or self.stages[0] is not AnalysisStage.RECEIVED:
            raise ValueError("analysis pipeline must begin with RECEIVED")


# Default navigation profiles are descriptive only. Server-side RBAC/scope
# remains authoritative and must authorize every operation independently.
CHIEF_ENGINEER_WORKSPACE = WorkspaceDefinition(
    EngineeringRole.CHIEF_ENGINEER,
    frozenset({
        WorkspaceArea.FLEET_OVERVIEW, WorkspaceArea.TECHNICAL_HEALTH,
        WorkspaceArea.ALARMS_AND_EVENTS, WorkspaceArea.PERFORMANCE_ANALYTICS,
        WorkspaceArea.MAINTENANCE_AND_COMPLIANCE, WorkspaceArea.DOCUMENT_INTELLIGENCE,
        WorkspaceArea.REPORTING, WorkspaceArea.AUDIT_AND_CHANGE_CONTROL,
        WorkspaceArea.TRENDS_AND_DIAGNOSTICS,
    }),
)
ENGINEER_WORKSPACE = WorkspaceDefinition(
    EngineeringRole.ENGINEER,
    frozenset({
        WorkspaceArea.ENGINEERING_PROJECTS, WorkspaceArea.DEVICE_INTEGRATION,
        WorkspaceArea.LOGIC_AND_FBD, WorkspaceArea.GRAPHICS_AND_MIMICS,
        WorkspaceArea.TRENDS_AND_DIAGNOSTICS, WorkspaceArea.ALARMS_AND_EVENTS,
        WorkspaceArea.DOCUMENT_INTELLIGENCE, WorkspaceArea.REPORTING,
    }),
)
VIEWER_WORKSPACE = WorkspaceDefinition(
    EngineeringRole.VIEWER,
    frozenset({WorkspaceArea.FLEET_OVERVIEW, WorkspaceArea.TECHNICAL_HEALTH,
               WorkspaceArea.ALARMS_AND_EVENTS, WorkspaceArea.REPORTING}),
    read_only=True,
)
