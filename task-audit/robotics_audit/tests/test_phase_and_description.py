from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from robotics_audit.common.description_utils import is_plausible_description
from robotics_audit.common.phase_gate import is_llm_eligible, split_violations
from robotics_audit.models import Violation
from robotics_audit.segment.rules import load_audit_config


class TestDescriptionUtils(unittest.TestCase):
    def test_english_sentence_ok(self) -> None:
        config = load_audit_config()
        self.assertTrue(
            is_plausible_description(
                "The robot arm picks up the black object from the table",
                config["word_lists"],
            )
        )

    def test_garbage_english_rejected(self) -> None:
        config = load_audit_config()
        self.assertFalse(is_plausible_description("fsfs sfsffs", config["word_lists"]))


class TestPhaseGate(unittest.TestCase):
    def test_defer_insufficient_elements(self) -> None:
        config = load_audit_config()
        violations = [
            Violation(
                code="insufficient_elements_1",
                grade="B",
                message="only one element",
                segment_index=0,
            )
        ]
        hard, soft = split_violations(
            violations,
            config=config,
            template_id="ROBOTICS_TPL_000001",
        )
        self.assertEqual(len(hard), 0)
        self.assertEqual(len(soft), 1)
        self.assertTrue(
            is_llm_eligible(violations, config=config, template_id="ROBOTICS_TPL_000001")
        )

    def test_hard_reject_overlap(self) -> None:
        config = load_audit_config()
        violations = [
            Violation(code="time_overlap", grade="D", message="overlap", segment_index=0)
        ]
        self.assertFalse(
            is_llm_eligible(violations, config=config, template_id="ROBOTICS_TPL_000001")
        )


if __name__ == "__main__":
    unittest.main()
