from __future__ import annotations

import json
from typing import Any, Dict, Optional


def parse_json_field(raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, (dict, list)):
        return raw
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None
    return None


def resolve_reference_data(row: Dict[str, Any]) -> Optional[Any]:
    """已废弃：参考内容应来自视频视觉分析缓存，不再使用 data_requirements。"""
    direct = parse_json_field(row.get("task_reference_data"))
    if direct is not None:
        return direct

    full = parse_json_field(row.get("task_data_requirements"))
    if isinstance(full, dict) and full.get("data") is not None:
        return full.get("data")

    return None


def resolve_submission_data(row: Dict[str, Any]) -> Any:
    return parse_json_field(row.get("data_submission"))
