from __future__ import annotations

from typing import Any, Dict, Optional

from robotics_audit.metadata.auditor import MetadataAuditor
from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT, AuditResult, Violation
from robotics_audit.segment.auditor import SegmentAuditor
from robotics_audit.task_reference.store import TaskReferenceRecord


class AuditRouter:
    def __init__(
        self,
        *,
        segment_config: Optional[str] = None,
        metadata_config: Optional[str] = None,
    ) -> None:
        self.segment_auditor = SegmentAuditor(config_path=segment_config)
        self.metadata_auditor = MetadataAuditor(config_path=metadata_config)

    def audit_row(
        self,
        row: Dict[str, Any],
        *,
        reference: Optional[TaskReferenceRecord] = None,
        enable_reference_check: bool = True,
        frame_count_limit: Optional[float] = None,
    ) -> AuditResult:
        submission_id = str(row.get("submission_id") or "")
        user_id = str(row.get("user_id") or "")
        frontier_id = str(row.get("frontier_id") or "")
        template_id = str(row.get("template_id") or "")
        task_id = str(row.get("task_id") or "")
        data_submission = row.get("data_submission")

        if template_id == TEMPLATE_SEGMENT:
            return self.segment_auditor.audit(
                submission_id,
                data_submission,
                user_id=user_id,
                frontier_id=frontier_id,
                template_id=template_id,
                task_id=task_id,
                reference=reference,
                enable_reference_check=enable_reference_check,
                frame_count_limit=frame_count_limit,
            )
        if template_id == TEMPLATE_METADATA:
            return self.metadata_auditor.audit(
                submission_id,
                data_submission,
                user_id=user_id,
                frontier_id=frontier_id,
                template_id=template_id,
                task_id=task_id,
                reference=reference,
                enable_reference_check=enable_reference_check,
            )

        return AuditResult(
            submission_id=submission_id,
            user_id=user_id,
            frontier_id=frontier_id,
            template_id=template_id,
            task_id=task_id,
            audit_grade="D",
            passed=False,
            error=f"未知 template_id: {template_id}",
            violations=[
                Violation(
                    code="unknown_template",
                    grade="D",
                    message=f"未知 template_id: {template_id}",
                )
            ],
        )
