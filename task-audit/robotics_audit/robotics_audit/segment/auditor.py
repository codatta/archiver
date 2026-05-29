from __future__ import annotations

from typing import Any, Dict, List, Optional

from robotics_audit.common.phase_gate import compute_rule_grades
from robotics_audit.models import AuditResult, SegmentAuditDetail, TEMPLATE_SEGMENT, Violation, worst_grade
from robotics_audit.segment.parser import extract_video_duration, parse_json_payload, parse_segments
from robotics_audit.segment.reference_match import check_reference_match
from robotics_audit.segment.rules import (
    analyze_elements,
    check_segment_rules,
    check_submission_rules,
    load_audit_config,
)
from robotics_audit.task_reference.store import TaskReferenceRecord


class SegmentAuditor:
    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config = load_audit_config(config_path)

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
        frame_count_limit: Optional[float] = None,
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

        list_keys = self.config.get("segment_list_keys", [])
        segments = parse_segments(payload, list_keys)
        video_duration = extract_video_duration(payload)
        if frame_count_limit is not None and frame_count_limit > 0:
            video_duration = frame_count_limit
        elif video_duration is None and segments:
            max_end = max((s.end for s in segments if s.end == s.end), default=None)
            if max_end is not None and max_end <= 1000:
                video_duration = max_end

        all_violations: List[Violation] = []
        segment_details: List[SegmentAuditDetail] = []

        all_violations.extend(
            check_submission_rules(segments, config=self.config, video_duration=video_duration)
        )

        word_lists = self.config["word_lists"]
        for seg in segments:
            seg_violations = check_segment_rules(
                seg, config=self.config, video_duration=video_duration
            )
            all_violations.extend(seg_violations)
            elements = analyze_elements(seg.description, word_lists)
            segment_details.append(
                SegmentAuditDetail(
                    segment_index=seg.index,
                    start=seg.start,
                    end=seg.end,
                    description=seg.description,
                    elements=elements,
                    violations=seg_violations,
                )
            )

        hard_grade, all_grade = compute_rule_grades(
            all_violations,
            config=self.config,
            template_id=template_id or TEMPLATE_SEGMENT,
        )
        rule_grade = hard_grade
        reference_check = "skipped"
        reference_path = None

        if all_grade == "S" and enable_reference_check and reference is not None:
            ref_violations = check_reference_match(
                segments,
                reference,
                min_overlap=float(self.config.get("thresholds", {}).get("reference_min_overlap", 0.12)),
            )
            all_violations.extend(ref_violations)
            reference_check = "matched" if not ref_violations else "mismatch"
            reference_path = str(reference.task_id)

        final_grade = worst_grade([v.grade for v in all_violations]) if all_violations else "S"

        return AuditResult(
            submission_id=submission_id,
            user_id=user_id,
            frontier_id=frontier_id,
            template_id=template_id,
            task_id=task_id,
            audit_grade=final_grade,
            passed=final_grade == "S",
            violations=all_violations,
            segment_details=segment_details,
            video_duration=video_duration,
            segment_count=len(segments),
            reference_check=reference_check,
            reference_path=reference_path,
            rule_phase_grade=rule_grade,
        )
