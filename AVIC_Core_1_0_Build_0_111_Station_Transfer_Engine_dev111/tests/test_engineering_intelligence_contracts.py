from datetime import datetime, timezone

import pytest

from avic_core.engineering_intelligence import (
    AnalysisStage, CHIEF_ENGINEER_WORKSPACE, DocumentAnalysisJob,
    DocumentArtifact, DocumentEvidence, DocumentKind, EngineeringFinding,
    EngineeringRole, ENGINEER_WORKSPACE, FindingSeverity, ReviewState,
    VIEWER_WORKSPACE, WorkspaceArea, WorkspaceDefinition,
)


def test_role_workspaces_cover_chief_engineer_and_engineer_domains():
    assert WorkspaceArea.FLEET_OVERVIEW in CHIEF_ENGINEER_WORKSPACE.areas
    assert WorkspaceArea.PERFORMANCE_ANALYTICS in CHIEF_ENGINEER_WORKSPACE.areas
    assert WorkspaceArea.ENGINEERING_PROJECTS in ENGINEER_WORKSPACE.areas
    assert WorkspaceArea.LOGIC_AND_FBD in ENGINEER_WORKSPACE.areas
    assert WorkspaceArea.DOCUMENT_INTELLIGENCE in ENGINEER_WORKSPACE.areas
    assert VIEWER_WORKSPACE.read_only is True
    with pytest.raises(ValueError):
        WorkspaceDefinition(EngineeringRole.VIEWER, frozenset({WorkspaceArea.REPORTING}))


def test_document_artifact_requires_digest_and_aware_timestamp():
    doc = DocumentArtifact(
        "HVAC specification", DocumentKind.PDF, "project://docs/hvac.pdf", "a" * 64,
        "engineer-1", datetime.now(timezone.utc), project_ref="project-1", revision="A",
    )
    assert doc.kind is DocumentKind.PDF
    assert doc.project_ref == "project-1"
    with pytest.raises(ValueError):
        DocumentArtifact("bad", DocumentKind.PDF, "uri", "bad", "u", datetime.now(timezone.utc))
    with pytest.raises(ValueError):
        DocumentArtifact("bad", DocumentKind.PDF, "uri", "a" * 64, "u", datetime.now())


def test_document_analysis_pipeline_starts_with_received_and_tracks_stage_order():
    job = DocumentAnalysisJob(("doc-1", "doc-2"), "chief-1", datetime.now(timezone.utc))
    assert job.stages[0] is AnalysisStage.RECEIVED
    assert AnalysisStage.CROSS_CHECKING in job.stages
    with pytest.raises(ValueError):
        DocumentAnalysisJob(("doc-1",), "chief-1", datetime.now(timezone.utc), (AnalysisStage.EXTRACTING,))


def test_findings_require_traceable_evidence_and_human_disposition():
    evidence = DocumentEvidence("doc-1", "page:12", "Pump P-101, 5.5 kW", "pdf_text", 0.97)
    finding = EngineeringFinding(
        "Power mismatch", "Motor power differs between schedule and drawing",
        FindingSeverity.HIGH, (evidence,), confidence=0.91,
    )
    assert finding.evidence[0].locator == "page:12"
    with pytest.raises(ValueError):
        EngineeringFinding("No evidence", "Unsupported finding", FindingSeverity.LOW, ())
    with pytest.raises(ValueError):
        EngineeringFinding("Bad confidence", "Invalid", FindingSeverity.LOW, (evidence,), confidence=1.2)
    with pytest.raises(ValueError):
        EngineeringFinding("Accepted", "No disposition", FindingSeverity.INFO, (evidence,), review_state=ReviewState.ACCEPTED)
