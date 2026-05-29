"""
Phase 2 — scene_cut_check
使用 scenedetect ContentDetector(threshold=27.0)；切点数 > 3 为 B 级（大量剪辑点）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from scenedetect import detect as scenedetect_detect
    from scenedetect import ContentDetector
except ImportError:
    scenedetect_detect = None  # type: ignore
    ContentDetector = None  # type: ignore


def count_scene_cuts(video_path: str, *, threshold: float = 27.0) -> int:
    if scenedetect_detect is None or ContentDetector is None:
        raise RuntimeError("请安装依赖: pip install scenedetect 与 opencv-python-headless")
    scene_list = scenedetect_detect(video_path, ContentDetector(threshold=threshold))
    if not scene_list:
        return 0
    return max(0, len(scene_list) - 1)


@dataclass
class SceneCutCheckOutcome:
    scene_cut_audit: Dict[str, Any]
    stop: bool
    audit_grade: Optional[str] = None
    db_update: Dict[str, Any] = field(default_factory=dict)
    cut_count: int = 0
    errors: List[str] = field(default_factory=list)


def run_scene_cut_check(
    video_path: str,
    *,
    lightweight_hash: str,
    phash_hex: str,
    task_id: str,
    max_cuts: int = 3,
    detector_threshold: float = 27.0,
) -> SceneCutCheckOutcome:
    try:
        cut_count = count_scene_cuts(video_path, threshold=detector_threshold)
    except Exception as e:
        return SceneCutCheckOutcome(
            scene_cut_audit={
                "overall_result": "fail",
                "reason": str(e),
                "cut_count": 0,
            },
            stop=True,
            audit_grade="Error",
            cut_count=0,
            errors=[f"scenedetect 失败: {e}"],
        )

    if cut_count > max_cuts:
        return SceneCutCheckOutcome(
            scene_cut_audit={
                "overall_result": "fail",
                "reason": f"剪辑点过多 (cut_count={cut_count} > {max_cuts})",
                "cut_count": cut_count,
            },
            stop=True,
            audit_grade="B",
            db_update={
                "lightweight_hash": lightweight_hash,
                "phash_hex": phash_hex,
                "audit_grade": "B",
                "cut_count": cut_count,
                "task_id": task_id,
            },
            cut_count=cut_count,
        )

    return SceneCutCheckOutcome(
        scene_cut_audit={
            "overall_result": "pass",
            "cut_count": cut_count,
        },
        stop=False,
        cut_count=cut_count,
        db_update={
            "lightweight_hash": lightweight_hash,
            "phash_hex": phash_hex,
            "audit_grade": "Pending_AI",
            "cut_count": cut_count,
            "task_id": task_id,
        },
    )
