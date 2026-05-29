from __future__ import annotations

from typing import Any, Dict, List, Tuple

from robotics_audit.models import TEMPLATE_METADATA, TEMPLATE_SEGMENT, Violation, worst_grade

DEFAULT_HARD_REJECT_CODES = {
    "parse_error",
    "no_segments",
    "missing_time",
    "negative_time",
    "end_lte_start",
    "time_exceeds_duration",
    "time_overlap",
    "placeholder_time",
    "empty_description",
    "garbage_description",
    "nonsense_description",
    "duplicate_segment",
    "identical_descriptions",
    "too_many_segments",
    "garbage_object_item",
    "garbage_task_item",
    "missing_objects",
    "missing_environment",
    "missing_agent_type",
}

DEFAULT_LLM_DEFER_CODES = {
    "insufficient_elements_0",
    "insufficient_elements_1",
    "description_too_short",
    "segment_too_short",
    "segment_too_long",
    "segment_unsorted",
    "garbage_relation_item",
    "invalid_environment",
    "invalid_view_item",
    "invalid_agent_type",
    "missing_view",
    "missing_task",
    "missing_relations",
}


def _gate_config(config: Dict[str, Any], template_id: str) -> Dict[str, Any]:
    gate = dict(config.get("phase_gate") or {})
    if template_id == TEMPLATE_SEGMENT:
        gate.setdefault("hard_reject_codes", list(DEFAULT_HARD_REJECT_CODES))
        gate.setdefault("llm_defer_codes", list(DEFAULT_LLM_DEFER_CODES))
    elif template_id == TEMPLATE_METADATA:
        gate.setdefault(
            "hard_reject_codes",
            [
                "parse_error",
                "garbage_object_item",
                "garbage_task_item",
                "garbage_relation_item",
                "missing_objects",
                "missing_environment",
                "missing_agent_type",
                "empty_object_item",
            ],
        )
        gate.setdefault(
            "llm_defer_codes",
            [
                "invalid_environment",
                "invalid_view_item",
                "invalid_agent_type",
                "missing_view",
                "missing_task",
                "missing_relations",
            ],
        )
    return gate


def split_violations(
    violations: List[Violation],
    *,
    config: Dict[str, Any],
    template_id: str,
) -> Tuple[List[Violation], List[Violation]]:
    gate = _gate_config(config, template_id)
    hard_codes = set(gate.get("hard_reject_codes") or [])
    defer_codes = set(gate.get("llm_defer_codes") or [])

    hard: List[Violation] = []
    soft: List[Violation] = []
    for item in violations:
        if item.code in defer_codes:
            soft.append(item)
        elif item.code in hard_codes:
            hard.append(item)
        elif item.grade in {"D", "C"}:
            hard.append(item)
        elif item.grade == "B" and item.code not in defer_codes:
            soft.append(item)
        else:
            hard.append(item)
    return hard, soft


def compute_rule_grades(
    violations: List[Violation],
    *,
    config: Dict[str, Any],
    template_id: str,
) -> Tuple[str, str]:
    hard, soft = split_violations(violations, config=config, template_id=template_id)
    hard_grade = worst_grade([v.grade for v in hard]) if hard else "S"
    all_grade = worst_grade([v.grade for v in violations]) if violations else "S"
    return hard_grade, all_grade


def is_llm_eligible(
    violations: List[Violation],
    *,
    config: Dict[str, Any],
    template_id: str,
) -> bool:
    hard_grade, _ = compute_rule_grades(violations, config=config, template_id=template_id)
    return hard_grade == "S"
