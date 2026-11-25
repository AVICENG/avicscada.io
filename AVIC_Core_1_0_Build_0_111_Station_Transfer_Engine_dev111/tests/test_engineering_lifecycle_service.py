import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from avic_core.contracts.engineering import LifecycleStage, WorkStatus
from avic_core.engineering.lifecycle import (
    EngineeringLifecycleService,
    LifecycleConflict,
    LifecycleTransitionError,
)


class EngineeringLifecycleServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.service = EngineeringLifecycleService(Path(self.tmp.name) / "lifecycle.sqlite3")
        self.now = datetime(2026, 11, 16, 12, 0, tzinfo=timezone.utc)

    def tearDown(self):
        self.tmp.cleanup()

    def initialize(self):
        return self.service.initialize_project("project-001", created_by="chief", at=self.now)

    def update(self, stage, status, version, **kwargs):
        return self.service.update_stage(
            "project-001", stage, status, updated_by="engineer",
            expected_version=version, at=self.now, **kwargs,
        )

    def complete(self, stage, version):
        started = self.update(stage, WorkStatus.IN_PROGRESS, version)
        review = self.update(stage, WorkStatus.IN_REVIEW, started.version)
        return self.update(stage, WorkStatus.DONE, review.version)

    def test_initialize_creates_complete_ordered_lifecycle(self):
        records = self.initialize()
        self.assertEqual(len(records), len(LifecycleStage))
        self.assertEqual(records[0].record.stage, LifecycleStage.DESIGN)
        self.assertEqual(records[-1].record.stage, LifecycleStage.ARCHIVED)
        self.assertTrue(all(item.record.status is WorkStatus.NOT_STARTED for item in records))
        self.assertTrue(all(item.version == 1 for item in records))

    def test_duplicate_initialization_is_rejected(self):
        self.initialize()
        with self.assertRaises(LifecycleConflict):
            self.initialize()

    def test_stage_cannot_start_before_prerequisite_is_done(self):
        self.initialize()
        with self.assertRaisesRegex(LifecycleTransitionError, "requires DESIGN=DONE"):
            self.update(LifecycleStage.DOCUMENT_REVIEW, WorkStatus.IN_PROGRESS, 1)

    def test_happy_path_and_next_stage_prerequisite(self):
        self.initialize()
        design = self.complete(LifecycleStage.DESIGN, 1)
        self.assertEqual(design.record.status, WorkStatus.DONE)
        review = self.update(LifecycleStage.DOCUMENT_REVIEW, WorkStatus.IN_PROGRESS, 1)
        self.assertEqual(review.version, 2)

    def test_logic_and_graphics_can_proceed_in_parallel_after_point_model(self):
        self.initialize()
        self.complete(LifecycleStage.DESIGN, 1)
        self.complete(LifecycleStage.DOCUMENT_REVIEW, 1)
        self.complete(LifecycleStage.EQUIPMENT_MODEL, 1)
        self.complete(LifecycleStage.POINT_MODEL, 1)
        logic = self.update(LifecycleStage.LOGIC, WorkStatus.IN_PROGRESS, 1)
        graphics = self.update(LifecycleStage.GRAPHICS, WorkStatus.IN_PROGRESS, 1)
        self.assertEqual(logic.record.status, WorkStatus.IN_PROGRESS)
        self.assertEqual(graphics.record.status, WorkStatus.IN_PROGRESS)

    def test_invalid_status_transition_is_rejected(self):
        self.initialize()
        with self.assertRaisesRegex(LifecycleTransitionError, "not allowed"):
            self.update(LifecycleStage.DESIGN, WorkStatus.DONE, 1)

    def test_optimistic_concurrency_rejects_stale_version(self):
        self.initialize()
        current = self.update(LifecycleStage.DESIGN, WorkStatus.IN_PROGRESS, 1)
        with self.assertRaises(LifecycleConflict):
            self.update(LifecycleStage.DESIGN, WorkStatus.IN_REVIEW, 1)
        self.assertEqual(current.version, 2)

    def test_metadata_and_transactional_history_are_persisted(self):
        self.initialize()
        current = self.update(
            LifecycleStage.DESIGN, WorkStatus.IN_PROGRESS, 1,
            assignee="engineer-1", document_refs=("doc://project/spec.pdf",),
            issue_refs=("issue-17",), notes="Начата проверка проекта",
        )
        reloaded = self.service.get_stage("project-001", LifecycleStage.DESIGN)
        self.assertEqual(reloaded.version, 2)
        self.assertEqual(reloaded.record.assignee, "engineer-1")
        self.assertEqual(reloaded.record.document_refs, ("doc://project/spec.pdf",))
        self.assertEqual(reloaded.record.issue_refs, ("issue-17",))
        self.assertEqual(reloaded.record.notes, "Начата проверка проекта")
        history = self.service.history("project-001")
        self.assertEqual(len(history), len(LifecycleStage) + 1)
        self.assertEqual(history[-1].actor, "engineer")
        self.assertEqual(history[-1].from_status, WorkStatus.NOT_STARTED)
        self.assertEqual(history[-1].to_status, WorkStatus.IN_PROGRESS)
        self.assertEqual(history[-1].details["version"], current.version)

    def test_failed_transition_does_not_write_history(self):
        self.initialize()
        before = len(self.service.history("project-001"))
        with self.assertRaises(LifecycleTransitionError):
            self.update(LifecycleStage.DOCUMENT_REVIEW, WorkStatus.IN_PROGRESS, 1)
        self.assertEqual(len(self.service.history("project-001")), before)


if __name__ == "__main__":
    unittest.main()
