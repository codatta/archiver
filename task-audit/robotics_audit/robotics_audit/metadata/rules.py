from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from robotics_audit.common.text_utils import is_garbage_text
from robotics_audit.models import Violation


def load_metadata_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(config_path or Path(__file__).resolve().parent.parent.parent / "audit_config.metadata.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _violation(code: str, grade_map: Dict[str, str], message: str, field: Optional[str] = None) -> Violation:
    return Violation(code=code, grade=grade_map.get(code, "B"), message=message, field=field)


def check_metadata_rules(data: Dict[str, Any], config: Dict[str, Any]) -> List[Violation]:
    thresholds = config["thresholds"]
    grade_map = config["violation_grades"]
    violations: List[Violation] = []

    objects = _as_list(data.get("objects"))
    if len(objects) < thresholds["min_objects_count"]:
        violations.append(_violation("missing_objects", grade_map, "objects 不能为空", "objects"))
    if len(objects) > thresholds["max_objects_count"]:
        violations.append(_violation("missing_objects", grade_map, f"objects 数量过多 (> {thresholds['max_objects_count']})", "objects"))
    for idx, item in enumerate(objects):
        if not item:
            violations.append(_violation("empty_object_item", grade_map, f"objects 第 {idx + 1} 项为空", "objects"))
        elif is_garbage_text(item):
            violations.append(_violation("garbage_object_item", grade_map, f"objects 第 {idx + 1} 项疑似乱填: {item}", "objects"))

    environment = str(data.get("environment") or "").strip()
    if not environment:
        violations.append(_violation("missing_environment", grade_map, "environment 未选择", "environment"))
    elif environment not in config.get("allowed_environments", []):
        violations.append(_violation("invalid_environment", grade_map, f"environment 不在允许范围: {environment}", "environment"))

    agent_type = data.get("agent_type")
    if not isinstance(agent_type, list) or not agent_type:
        violations.append(_violation("missing_agent_type", grade_map, "agent_type 缺失", "agent_type"))
    else:
        if len(agent_type) != 1:
            violations.append(_violation("invalid_agent_type", grade_map, "agent_type 应只提交 1 条", "agent_type"))
        first = agent_type[0] if agent_type else {}
        if isinstance(first, dict):
            status = str(first.get("status") or "").strip().lower()
            arm_count = str(first.get("armCount") or "").strip()
            if status and status not in config.get("allowed_agent_status", []):
                violations.append(_violation("invalid_agent_type", grade_map, f"agent_type.status 无效: {status}", "agent_type"))
            if arm_count and arm_count not in config.get("allowed_arm_counts", []):
                violations.append(_violation("invalid_agent_type", grade_map, f"agent_type.armCount 无效: {arm_count}", "agent_type"))

    views = _as_list(data.get("view"))
    if len(views) < thresholds["min_view_items"]:
        violations.append(_violation("missing_view", grade_map, "view 至少选择 1 项", "view"))
    allowed_views = set(config.get("allowed_views", []))
    for item in views:
        if item not in allowed_views:
            violations.append(_violation("invalid_view_item", grade_map, f"view 包含无效选项: {item}", "view"))

    tasks = _as_list(data.get("task"))
    if len(tasks) < thresholds["min_task_items"]:
        violations.append(_violation("missing_task", grade_map, "task 描述不能为空", "task"))
    for idx, item in enumerate(tasks):
        if is_garbage_text(item):
            violations.append(_violation("garbage_task_item", grade_map, f"task 第 {idx + 1} 项疑似乱填: {item}", "task"))

    relations = _as_list(data.get("relations"))
    if len(relations) < thresholds["min_relations_items"]:
        violations.append(_violation("missing_relations", grade_map, "relations 不能为空", "relations"))
    for idx, item in enumerate(relations):
        if is_garbage_text(item, min_len=3):
            violations.append(_violation("garbage_relation_item", grade_map, f"relations 第 {idx + 1} 项疑似乱填: {item}", "relations"))

    return violations


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    text = str(value).strip()
    return [text] if text else []
