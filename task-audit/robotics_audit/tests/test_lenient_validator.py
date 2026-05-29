from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotics_audit.llm_text_validator import LLMTextValidator, _timeline_hint
from robotics_audit.models import Violation


class TestLenientValidator(unittest.TestCase):
    def setUp(self) -> None:
        os.environ["LLM_LENIENT_MODE"] = "1"
        self.validator = LLMTextValidator()

    def test_lenient_upgrades_minor_grade(self) -> None:
        grade, violations = self.validator._normalize_result(
            {
                "audit_grade": "D",
                "passed": False,
                "violations": [
                    {
                        "code": "llm_semantic_mismatch",
                        "grade": "D",
                        "message": "cup vs bottle wording difference",
                    }
                ],
            }
        )
        self.assertEqual(grade, "S")
        self.assertEqual(violations, [])

    def test_lenient_keeps_severe_garbage(self) -> None:
        grade, _ = self.validator._normalize_result(
            {
                "audit_grade": "D",
                "violations": [
                    {
                        "code": "llm_garbage",
                        "grade": "D",
                        "message": "明显乱填 fsfs",
                    }
                ],
            }
        )
        self.assertEqual(grade, "D")

    def test_timeline_hint_when_submission_longer(self) -> None:
        hint = _timeline_hint(
            {"segments": [{"start": 0, "end": 15, "description": "a"}]},
            [{"start": 1, "end": 45, "des": "b"}],
            {"frame_count": 83, "time_unit": "frame"},
        )
        self.assertIn("83", hint)
        self.assertIn("帧", hint)


if __name__ == "__main__":
    unittest.main()
