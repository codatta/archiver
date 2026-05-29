from __future__ import annotations

from typing import Any, Dict, List

from robotics_audit.common.text_utils import normalize_text, overlap_score
from robotics_audit.models import Violation
from robotics_audit.task_reference.store import TaskReferenceRecord


def check_metadata_reference(
    data: Dict[str, Any],
    record: TaskReferenceRecord,
    *,
    min_overlap: float = 0.12,
) -> List[Violation]:
    reference = record.reference or {}
    violations: List[Violation] = []

    ref_objects = _string_list(reference.get("objects")) + _string_list(reference.get("visible_objects"))
    if ref_objects:
        for idx, item in enumerate(_string_list(data.get("objects"))):
            score = max(overlap_score(item, ref_objects), overlap_score(item, _string_list(reference.get("actions"))))
            if score < min_overlap:
                violations.append(
                    Violation(
                        code="reference_mismatch_objects",
                        grade="B",
                        message=f"objects 第 {idx + 1} 项与 task 参考内容匹配度过低 ({score:.2f})",
                        field="objects",
                    )
                )

    ref_tasks = _string_list(reference.get("task")) + _string_list(reference.get("actions"))
    for idx, item in enumerate(_string_list(data.get("task"))):
        score = overlap_score(item, ref_tasks)
        if ref_tasks and score < min_overlap:
            violations.append(
                Violation(
                    code="reference_mismatch_task",
                    grade="B",
                    message=f"task 第 {idx + 1} 项与 task 参考内容匹配度过低 ({score:.2f})",
                    field="task",
                )
            )

    ref_env = normalize_text(str(reference.get("environment") or ""))
    env = normalize_text(str(data.get("environment") or ""))
    if ref_env and env and ref_env != env:
        violations.append(
            Violation(
                code="reference_mismatch_environment",
                grade="B",
                message=f"environment ({data.get('environment')}) 与参考 ({reference.get('environment')}) 不一致",
                field="environment",
            )
        )

    ref_views = {normalize_text(v) for v in _string_list(reference.get("view"))}
    if ref_views:
        submitted = {normalize_text(v) for v in _string_list(data.get("view"))}
        if submitted and not (submitted & ref_views):
            violations.append(
                Violation(
                    code="reference_mismatch_view",
                    grade="A",
                    message="view 与 task 参考视角无交集",
                    field="view",
                )
            )

    if not reference:
        violations.append(
            Violation(code="reference_missing", grade="A", message="task 参考 JSON 为空")
        )

    return violations


def _string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value or "").strip()
    return [text] if text else []
