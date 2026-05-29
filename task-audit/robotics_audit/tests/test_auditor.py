from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotics_audit.segment.auditor import SegmentAuditor


class TestSegmentAuditor(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.auditor = SegmentAuditor()
        sample_path = ROOT / "sample_data" / "submissions_sample.json"
        with open(sample_path, "r", encoding="utf-8") as f:
            cls.samples = {row["submission_id"]: row for row in json.load(f)}

    def _audit(self, submission_id: str):
        row = self.samples[submission_id]
        return self.auditor.audit(
            submission_id,
            row["data_submission"],
            user_id=row.get("user_id", ""),
            template_id="ROBOTICS_TPL_000001",
            enable_reference_check=False,
        )

    def test_pass_sample(self) -> None:
        result = self._audit("sample_pass_001")
        self.assertEqual(result.audit_grade, "S")
        self.assertTrue(result.passed)

    def test_placeholder_rejected(self) -> None:
        result = self._audit("sample_placeholder_002")
        self.assertIn(result.audit_grade, {"C", "D"})
        self.assertFalse(result.passed)

    def test_overlap_rejected(self) -> None:
        result = self._audit("sample_overlap_003")
        self.assertEqual(result.audit_grade, "D")
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
