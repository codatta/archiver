from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from robotics_audit.models import ElementAnalysis, Segment, Violation, worst_grade


def load_audit_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    path = Path(config_path or Path(__file__).resolve().parent.parent / "audit_config.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", "", text or "").strip()


def _contains_any(text: str, words: List[str]) -> bool:
    return any(w and w in text for w in words)


def analyze_elements(description: str, word_lists: Dict[str, List[str]]) -> ElementAnalysis:
    text = _normalize_text(description)
    if not text:
        return ElementAnalysis()
    return ElementAnalysis(
        subject=_contains_any(text, word_lists.get("subject", [])),
        action=_contains_any(text, word_lists.get("action", [])),
        object=_contains_any(text, word_lists.get("object", [])),
        result=_contains_any(text, word_lists.get("result", [])),
    )


def _violation(code: str, grade_map: Dict[str, str], message: str, segment_index: Optional[int] = None) -> Violation:
    return Violation(
        code=code,
        grade=grade_map.get(code, "B"),
        message=message,
        segment_index=segment_index,
    )


def _segments_overlap(a: Segment, b: Segment) -> bool:
    return a.start < b.end and b.start < a.end


def _is_placeholder_segment(seg: Segment) -> bool:
    if seg.start == seg.end and not seg.description.strip():
        return True
    if seg.start == seg.end and len(_normalize_text(seg.description)) < 4:
        return True
    return False


def _detect_global_placeholder_pattern(segments: List[Segment]) -> bool:
    if len(segments) < 2:
        return False
    if not all(seg.start == seg.end for seg in segments):
        return False
    starts = [seg.start for seg in segments]
    if starts == list(range(int(starts[0]), int(starts[0]) + len(starts))):
        empty_or_short = all(len(_normalize_text(seg.description)) < 4 for seg in segments)
        if empty_or_short:
            return True
    return False


def check_segment_rules(
    seg: Segment,
    *,
    config: Dict[str, Any],
    video_duration: Optional[float],
) -> List[Violation]:
    thresholds = config["thresholds"]
    grade_map = config["violation_grades"]
    word_lists = config["word_lists"]
    violations: List[Violation] = []
    idx = seg.index

    if seg.start != seg.start or seg.end != seg.end:
        violations.append(
            _violation("missing_time", grade_map, f"第 {idx + 1} 段缺少合法的开始或结束时间", idx)
        )
        return violations

    if seg.start < 0 or seg.end < 0:
        violations.append(
            _violation("negative_time", grade_map, f"第 {idx + 1} 段时间为负数", idx)
        )

    if seg.end <= seg.start:
        violations.append(
            _violation("end_lte_start", grade_map, f"第 {idx + 1} 段结束时间必须大于开始时间", idx)
        )

    if video_duration is not None and seg.end > video_duration:
        violations.append(
            _violation(
                "time_exceeds_duration",
                grade_map,
                f"第 {idx + 1} 段结束时间 {seg.end} 超出视频时长 {video_duration}",
                idx,
            )
        )

    desc = seg.description.strip()
    norm = _normalize_text(desc)
    if not norm:
        violations.append(
            _violation("empty_description", grade_map, f"第 {idx + 1} 段描述为空", idx)
        )
    elif len(norm) < thresholds["soft_min_description_length"]:
        violations.append(
            _violation("description_too_short", grade_map, f"第 {idx + 1} 段描述过短", idx)
        )
    elif len(norm) < thresholds["min_description_length"]:
        violations.append(
            _violation(
                "description_too_short",
                grade_map,
                f"第 {idx + 1} 段描述长度不足 {thresholds['min_description_length']} 字",
                idx,
            )
        )

    duration = seg.end - seg.start
    if duration < thresholds["min_segment_duration"]:
        violations.append(
            _violation("segment_too_short", grade_map, f"第 {idx + 1} 段时长过短 ({duration:.2f}s)", idx)
        )
    if duration > thresholds["max_segment_duration"]:
        violations.append(
            _violation("segment_too_long", grade_map, f"第 {idx + 1} 段时长过长 ({duration:.2f}s)", idx)
        )

    if _is_placeholder_segment(seg):
        violations.append(
            _violation("placeholder_time", grade_map, f"第 {idx + 1} 段疑似占位符时间", idx)
        )

    if norm:
        elements = analyze_elements(desc, word_lists)
        min_count = thresholds["min_element_count_for_s"]
        if elements.count == 0:
            violations.append(
                _violation(
                    "insufficient_elements_0",
                    grade_map,
                    f"第 {idx + 1} 段描述未体现四要素中任何一项（主体/动作/对象/结果）",
                    idx,
                )
            )
        elif elements.count < min_count:
            violations.append(
                _violation(
                    "insufficient_elements_1",
                    grade_map,
                    f"第 {idx + 1} 段描述仅体现 {elements.count} 个要素，至少需要 {min_count} 个",
                    idx,
                )
            )

    return violations


def check_submission_rules(
    segments: List[Segment],
    *,
    config: Dict[str, Any],
    video_duration: Optional[float],
) -> List[Violation]:
    thresholds = config["thresholds"]
    grade_map = config["violation_grades"]
    violations: List[Violation] = []

    if not segments:
        violations.append(_violation("no_segments", grade_map, "未提交任何分段"))
        return violations

    if len(segments) > thresholds["max_segment_count"]:
        violations.append(
            _violation(
                "too_many_segments",
                grade_map,
                f"分段数量 {len(segments)} 超过上限 {thresholds['max_segment_count']}",
            )
        )

    if _detect_global_placeholder_pattern(segments):
        violations.append(
            _violation("placeholder_time", grade_map, "全部段时间戳呈连续占位符模式且描述为空")
        )

    seen: Set[Tuple[float, float, str]] = set()
    for seg in segments:
        key = (round(seg.start, 3), round(seg.end, 3), _normalize_text(seg.description))
        if key in seen:
            violations.append(
                _violation("duplicate_segment", grade_map, f"第 {seg.index + 1} 段与其他段完全重复", seg.index)
            )
        seen.add(key)

    sorted_by_start = sorted(segments, key=lambda s: (s.start, s.index))
    for i in range(len(sorted_by_start) - 1):
        if sorted_by_start[i].start > sorted_by_start[i + 1].start:
            violations.append(
                _violation("segment_unsorted", grade_map, "分段时间未按开始时间递增排列")
            )
            break

    for i in range(len(segments)):
        for j in range(i + 1, len(segments)):
            if _segments_overlap(segments[i], segments[j]):
                violations.append(
                    _violation(
                        "time_overlap",
                        grade_map,
                        f"第 {segments[i].index + 1} 段与第 {segments[j].index + 1} 段时间重叠",
                        segments[i].index,
                    )
                )

    descriptions = [_normalize_text(seg.description) for seg in segments if _normalize_text(seg.description)]
    if len(descriptions) >= 3 and len(set(descriptions)) == 1:
        violations.append(
            _violation("identical_descriptions", grade_map, "全部段描述完全相同，疑似复制粘贴")
        )

    return violations
