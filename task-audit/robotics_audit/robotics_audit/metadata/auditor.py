from __future__ import annotations

from typing import Any, Dict, List, Optional

from robotics_audit.common.phase_gate import compute_rule_grades
from robotics_audit.metadata.parser import extract_metadata, parse_json_payload
from robotics_audit.metadata.reference_match import check_metadata_reference
from robotics_audit.metadata.rules import check_metadata_rules, load_metadata_config
from robotics_audit.models import AuditResult, TEMPLATE_METADATA, Violation, worst_grade
from robotics_audit.task_reference.store import TaskReferenceRecord


class MetadataAuditor:
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config = load_metadata_config(config_path)

    def audit(
        self,
        submission_id: str,
        data_submission: Any,
        *,
        user_id: str = "",
        frontier_id: str = "",
        template_id: str = "",
        task_id: str = "",
        reference: Optional[TaskReferenceRecord] = None,
        enable_reference_check: bool = True,
    ) -> AuditResult:
        payload = parse_json_payload(data_submission)
        if not payload and data_submission not in (None, "", {}):
            return AuditResult(
                submission_id=submission_id,
                user_id=user_id,
                frontier_id=frontier_id,
                template_id=template_id,
                task_id=task_id,
                audit_grade="D",
                passed=False,
                error="data_submission 无法解析为 JSON",
                violations=[
                    Violation(code="parse_error", grade="D", message="data_submission 无法解析为 JSON")
                ],
            )

        data = extract_metadata(payload)
        violations: List[Violation] = list(check_metadata_rules(data, self.config))
        hard_grade, all_grade = compute_rule_grades(
            violations,
            config=self.config,
            template_id=template_id or TEMPLATE_METADATA,
        )
        rule_grade = hard_grade
        reference_check = "skipped"

        if all_grade == "S" and enable_reference_check and reference is not None:
            ref_violations = check_metadata_reference(
                data,
                reference,
                min_overlap=float(self.config.get("thresholds", {}).get("reference_min_overlap", 0.12)),
            )
            violations.extend(ref_violations)
            reference_check = "matched" if not ref_violations else "mismatch"

        final_grade = worst_grade([v.grade for v in violations]) if violations else "S"
        return AuditResult(
            submission_id=submission_id,
            user_id=user_id,
            frontier_id=frontier_id,
            template_id=template_id,
            task_id=task_id,
            audit_grade=final_grade,
            passed=final_grade == "S",
            violations=violations,
            segment_count=0,
            reference_check=reference_check,
            reference_path=reference.task_id if reference else None,
            rule_phase_grade=rule_grade,
        )
