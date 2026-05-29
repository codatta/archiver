from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotics_audit.models import TEMPLATE_SEGMENT
from robotics_audit.pipeline import AuditPipeline
from robotics_audit.task_reference.store import TaskReferenceRecord


class TestPipelineJsonReference(unittest.TestCase):
    def setUp(self) -> None:
        self.pipeline = AuditPipeline(
            reference_dir=ROOT / "output" / "task_reference",
            enable_llm_text_check=True,
            enable_json_reference_check=True,
        )

    def test_json_reference_match_ok(self) -> None:
        row = {
            "data_submission": [
                {"start": 1, "end": 20, "des": "The robot arm picks up the cup from the table"},
            ],
        }
        reference = TaskReferenceRecord(
            frontier_id="ROBSTIC001",
            template_id=TEMPLATE_SEGMENT,
            task_id="t1",
            reference={
                "segments": [
                    {"start": 1, "end": 20, "description": "robot picks up cup from table"},
                ],
                "visible_objects": ["cup", "table"],
                "actions": ["pick up cup"],
            },
        )
        violations = self.pipeline._apply_json_reference_check(row, TEMPLATE_SEGMENT, reference)
        self.assertEqual(violations, [])

    def test_json_reference_mismatch(self) -> None:
        row = {
            "data_submission": [
                {"start": 1, "end": 20, "des": "completely unrelated xyz random text"},
            ],
        }
        reference = TaskReferenceRecord(
            frontier_id="ROBSTIC001",
            template_id=TEMPLATE_SEGMENT,
            task_id="t1",
            reference={
                "segments": [
                    {"start": 1, "end": 20, "description": "robot picks up cup from table"},
                ],
                "visible_objects": ["cup", "table"],
                "actions": ["pick up cup"],
            },
        )
        violations = self.pipeline._apply_json_reference_check(row, TEMPLATE_SEGMENT, reference)
        self.assertTrue(violations)
        self.assertEqual(violations[0].code, "reference_mismatch_description")

    @patch.object(AuditPipeline, "_apply_json_reference_check", return_value=[])
    @patch("robotics_audit.pipeline.LLMTextValidator.validate")
    def test_llm_flow_appends_json_ref_ok_suffix(self, mock_validate, _mock_json) -> None:
        mock_validate.return_value = {"audit_grade": "S", "violations": []}
        pipeline = AuditPipeline(
            reference_dir=ROOT / "output" / "task_reference",
            enable_llm_text_check=True,
            enable_json_reference_check=True,
        )
        pipeline.reference_manager = MagicMock()
        pipeline.reference_manager.get_or_create.return_value = TaskReferenceRecord(
            frontier_id="ROBSTIC001",
            template_id=TEMPLATE_SEGMENT,
            task_id="t1",
            reference={"segments": []},
            media_url="http://example.com/a.gif",
        )
        pipeline.reference_manager.store.path_for.return_value = "/tmp/ref.json"

        from robotics_audit.models import AuditResult

        rule_result = AuditResult(
            submission_id="s1",
            template_id=TEMPLATE_SEGMENT,
            rule_phase_grade="S",
        )
        row = {"data_submission": [{"start": 1, "end": 2, "des": "robot picks cup"}]}
        result = pipeline._apply_llm_text_check(row, rule_result, "ROBSTIC001", TEMPLATE_SEGMENT, "t1")
        self.assertIn("+json_ref_ok", result.reference_check)


if __name__ == "__main__":
    unittest.main()
