"""综合 JSON / 评级汇总结构（与 cex_hot_wallet 输出形态对齐）。"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List


def summarize_comprehensive(audit_results: List[Dict[str, Any]]) -> Dict[str, int]:
    total = len(audit_results)
    success = 0
    with_errors = 0
    for r in audit_results:
        grade = final_grade_from_result(r)
        if grade != "Error":
            success += 1
        else:
            with_errors += 1
    return {"total": total, "success": success, "with_errors": with_errors}


def final_grade_from_result(r: Dict[str, Any]) -> str:
    g = r.get("audit_grade")
    if isinstance(g, str) and g:
        return g
    dup = r.get("duplicate_audit") or {}
    if dup.get("overall_result") == "fail":
        return "D"
    meta = r.get("metadata_audit") or {}
    if meta.get("overall_result") == "fail":
        return "C"
    sc = r.get("scene_cut_audit") or {}
    if sc.get("overall_result") == "fail":
        return "B"
    if (
        dup.get("overall_result") == "pass"
        and meta.get("overall_result") == "pass"
        and sc.get("overall_result") == "pass"
    ):
        yolo = r.get("yolo_audit") or {}
        if yolo.get("overall_result") in {"pass", "manual_review"}:
            g = r.get("audit_grade")
            return str(g) if g else "A"
        return "A"
    return "unknown"


def grade_to_result_score(grade: str) -> int:
    mapping = {"D": 1, "C": 2, "B": 3, "A": 4, "S": 5}
    return mapping.get(str(grade).upper(), 0)


def grade_to_status(grade: str) -> str:
    g = str(grade).upper()
    if g == "S":
        return "ADOPT"
    if g == "A":
        return "PENDING"
    if g in {"B", "C", "D"}:
        return "REFUSED"
    return "PENDING"


def build_rating_results(audit_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    dist: Dict[str, int] = {}
    rated: List[Dict[str, Any]] = []
    for r in audit_results:
        sid = r.get("submission_id")
        grade = final_grade_from_result(r)
        dist[grade] = dist.get(grade, 0) + 1

        dup = r.get("duplicate_audit") or {}
        meta = r.get("metadata_audit") or {}
        sc = r.get("scene_cut_audit") or {}
        yolo = r.get("yolo_audit") or {}

        reason_parts = []
        if dup.get("overall_result") == "fail":
            reason_parts.append(dup.get("reason") or "duplicate_audit 未通过")
        if meta.get("overall_result") == "fail":
            reason_parts.append(meta.get("reason") or "metadata_audit 未通过")
        if sc.get("overall_result") == "fail":
            reason_parts.append(sc.get("reason") or "scene_cut_audit 未通过")
        if yolo.get("overall_result") == "fail":
            reason_parts.append(yolo.get("reason") or "yolo_audit 未通过")
        if yolo.get("overall_result") == "manual_review":
            reason_parts.append(yolo.get("reason") or "yolo_audit 进入人工复审")
        if r.get("errors"):
            reason_parts.append("处理异常: " + "; ".join(r["errors"]))

        stage_summary = (
            f"阶段结果 duplicate={dup.get('overall_result', 'unknown')}, "
            f"metadata={meta.get('overall_result', 'unknown')}, "
            f"scene_cut={sc.get('overall_result', 'unknown')}, "
            f"yolo={yolo.get('overall_result', 'unknown')}"
        )
        full_reason = "；".join(reason_parts) if reason_parts else "全部阶段通过"
        full_reason = f"{stage_summary}；{full_reason}"

        rated.append(
            {
                "submission_id": sid,
                "audit_grade": grade,
                "result": grade_to_result_score(grade),
                "status": grade_to_status(grade),
                "reason": full_reason,
                "checks": {
                    "duplicate_audit": dup.get("overall_result", "unknown"),
                    "metadata_audit": meta.get("overall_result", "unknown"),
                    "scene_cut_audit": sc.get("overall_result", "unknown"),
                    "yolo_audit": yolo.get("overall_result", "unknown"),
                },
                "ai_confidence": {
                    "both_hands_confidence": yolo.get("both_hands_confidence"),
                    "object_interaction_confidence": yolo.get("object_interaction_confidence"),
                    "first_person_confidence": yolo.get("first_person_confidence"),
                    "video_type": yolo.get("video_type"),
                    "video_type_confidence": yolo.get("video_type_confidence"),
                },
            }
        )

    return {
        "result": "success",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total": len(audit_results),
            "audit_grade_distribution": dist,
        },
        "rated_results": rated,
    }


__all__ = ["summarize_comprehensive", "build_rating_results", "final_grade_from_result"]
