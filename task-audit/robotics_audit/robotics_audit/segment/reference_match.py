from __future__ import annotations

from typing import Any, Dict, List

from robotics_audit.common.text_utils import overlap_score
from robotics_audit.models import Segment, Violation
from robotics_audit.task_reference.store import TaskReferenceRecord


def build_reference_vocabulary(reference: Dict[str, Any]) -> List[str]:
    vocab: List[str] = []
    for key in ("visible_objects", "actions", "objects", "task"):
        values = reference.get(key) or []
        if isinstance(values, list):
            vocab.extend(str(v) for v in values if str(v).strip())
    for seg in reference.get("segments") or []:
        if isinstance(seg, dict):
            desc = str(seg.get("description") or seg.get("des") or "").strip()
            if desc:
                vocab.append(desc)
    return vocab


def check_reference_match(
    segments: List[Segment],
    record: TaskReferenceRecord,
    *,
    min_overlap: float = 0.12,
) -> List[Violation]:
    reference = record.reference or {}
    vocabulary = build_reference_vocabulary(reference)
    if not vocabulary:
        return [
            Violation(
                code="reference_missing",
                grade="A",
                message="task 参考 JSON 缺少可用于比对的内容",
            )
        ]

    violations: List[Violation] = []
    for seg in segments:
        score = overlap_score(seg.description, vocabulary)
        if score < min_overlap:
            violations.append(
                Violation(
                    code="reference_mismatch_description",
                    grade="B",
                    message=f"第 {seg.index + 1} 段描述与 task 参考内容匹配度过低 ({score:.2f})",
                    segment_index=seg.index,
                )
            )
    return violations
