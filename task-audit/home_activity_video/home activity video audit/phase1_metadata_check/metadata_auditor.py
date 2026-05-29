"""
Phase 1 — metadata_check
分辨率 >= 1920x1080；横屏（宽>高）；时长 >= 600 秒。失败为 C 级。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class MetadataCheckOutcome:
    metadata_audit: Dict[str, Any]
    stop: bool
    audit_grade: Optional[str] = None
    db_update: Dict[str, Any] = field(default_factory=dict)


def run_metadata_check(
    *,
    width: int,
    height: int,
    duration_sec: float,
    lightweight_hash: str,
    phash_hex: str,
    task_id: str,
) -> MetadataCheckOutcome:
    meta_checks: List[Dict[str, Any]] = []

    res_ok = width >= 1920 and height >= 1080
    meta_checks.append(
        {
            "check_name": "resolution_check",
            "result": "pass" if res_ok else "fail",
            "actual": f"{width}x{height}",
        }
    )
    dur_ok = duration_sec >= 600.0
    meta_checks.append(
        {
            "check_name": "duration_check",
            "result": "pass" if dur_ok else "fail",
            "expected": ">= 600",
            "actual": str(int(duration_sec))
            if duration_sec == int(duration_sec)
            else f"{duration_sec:.3f}".rstrip("0").rstrip("."),
        }
    )
    orient_ok = width > height
    meta_checks.append(
        {
            "check_name": "orientation_check",
            "result": "pass" if orient_ok else "fail",
            "actual": "landscape" if orient_ok else "portrait_or_square",
        }
    )

    meta_pass = res_ok and dur_ok and orient_ok
    if not meta_pass:
        reasons = []
        if not res_ok:
            reasons.append(f"分辨率不足 ({width}x{height})")
        if not dur_ok:
            reasons.append(f"视频时长不足 (仅 {int(duration_sec)} 秒)")
        if not orient_ok:
            reasons.append("非横屏（宽未大于高）")
        return MetadataCheckOutcome(
            metadata_audit={
                "overall_result": "fail",
                "reason": "；".join(reasons),
                "checks": meta_checks,
            },
            stop=True,
            audit_grade="C",
            db_update={
                "lightweight_hash": lightweight_hash,
                "phash_hex": phash_hex,
                "audit_grade": "C",
                "task_id": task_id,
            },
        )

    return MetadataCheckOutcome(
        metadata_audit={"overall_result": "pass", "checks": meta_checks},
        stop=False,
    )
