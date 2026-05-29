"""
Phase 0 — duplicate_check
先做批次内 video.hash 去重，再做数据库历史 video.hash 去重。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from db_client import VideoAuditDBClient


@dataclass
class DuplicateCheckOutcome:
    """供 main_audit 编排：是否阻断流水线、duplicate_audit JSON、建议回写字段。"""

    duplicate_audit: Dict[str, Any]
    stop: bool
    audit_grade: Optional[str] = None  # 'D' | 'Error' when stop
    db_update: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    phash_hex: str = ""  # Phase 0 通过后供后续阶段与最终回写使用（不单独触发中间 UPDATE）


def run_duplicate_check(
    db: VideoAuditDBClient,
    *,
    submission_id: str,
    task_id: str,
    video_path: str,
    lightweight_hash: str,
    duration_sec: float,
    video_hash: Optional[str],
    batch_video_hash_index: Dict[str, List[str]],
    batch_first_submission_by_hash: Dict[str, str],
) -> DuplicateCheckOutcome:
    dup_checks: List[Dict[str, Any]] = []
    if not video_hash:
        dup_checks.append(
            {
                "check_name": "video_hash_batch_match",
                "result": "fail",
                "hash_value": "",
            }
        )
        return DuplicateCheckOutcome(
            duplicate_audit={
                "overall_result": "fail",
                "reason": "data_submission 缺少 video.hash，无法做重复比对",
                "checks": dup_checks,
            },
            stop=True,
            audit_grade="Error",
            errors=["缺少 video.hash"],
        )

    # 1) 先查本批次中相同 hash 的其他 submission。
    #    仅保留该 hash 在批次中最早提交的记录，其余记为 D。
    same = batch_video_hash_index.get(video_hash) or []
    first_sid = str(batch_first_submission_by_hash.get(video_hash) or "").strip()
    if first_sid and submission_id != first_sid:
        dup_checks.append(
            {
                "check_name": "video_hash_batch_match",
                "result": "fail",
                "hash_value": video_hash,
            }
        )
        return DuplicateCheckOutcome(
            duplicate_audit={
                "overall_result": "fail",
                "reason": (
                    f"video.hash 在本批次中重复（{video_hash}），"
                    f"最早提交为 submission_id={first_sid}，当前记录打回 D"
                ),
                "checks": dup_checks,
            },
            stop=True,
            audit_grade="D",
            db_update={
                # 复用 lightweight_hash 字段承载 video.hash，便于后续落库/排查
                "lightweight_hash": video_hash,
                "audit_grade": "D",
                "task_id": task_id,
            },
        )

    dup_checks.append(
        {
            "check_name": "video_hash_batch_match",
            "result": "pass",
            "hash_value": video_hash,
        }
    )

    # 2) 再查数据库历史重复（默认启用）
    try:
        in_history = db.video_hash_exists_in_history(
            video_hash=video_hash,
            exclude_submission_id=submission_id,
            task_id=task_id,
        )
    except Exception as e:
        return DuplicateCheckOutcome(
            duplicate_audit={
                "overall_result": "fail",
                "reason": f"历史去重查询失败: {e}",
                "checks": dup_checks,
            },
            stop=True,
            audit_grade="Error",
            errors=[f"历史去重查询失败: {e}"],
        )

    if in_history:
        dup_checks.append(
            {
                "check_name": "video_hash_history_match",
                "result": "fail",
                "hash_value": video_hash,
            }
        )
        return DuplicateCheckOutcome(
            duplicate_audit={
                "overall_result": "fail",
                "history_hash_duplicate": True,
                "reason": f"video.hash 在历史数据中重复（{video_hash}）",
                "checks": dup_checks,
            },
            stop=True,
            audit_grade="D",
            db_update={
                "lightweight_hash": video_hash,
                "audit_grade": "D",
                "task_id": task_id,
            },
        )

    dup_checks.append(
        {
            "check_name": "video_hash_history_match",
            "result": "pass",
            "hash_value": video_hash,
        }
    )
    return DuplicateCheckOutcome(
        duplicate_audit={"overall_result": "pass", "history_hash_duplicate": False, "checks": dup_checks},
        stop=False,
        phash_hex="",
    )
