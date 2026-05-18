"""Live data pull API — reads from AliCloud MySQL (cfp_metacore).

Consumer API (API key auth): /v1/live/pull, /v1/live/items/{id}/adopt|dispute
Dashboard API (JWT auth): /v1/orgs/{org_id}/live/pull, etc.

NOTE: supply_db.py (Supabase supply schema) is a future migration target —
not yet in production. These endpoints query AliCloud MySQL via mysql_db.py.
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from postgrest.exceptions import APIError
from pydantic import BaseModel

from app.access_log import log_access
from app.apikey_auth import check_subscription_scope, verify_api_key
from app.auth import require_org_member
from app.db import supabase
from app.mysql_db import fetch_all, fetch_one
from app.pricing import resolve_price

logger = logging.getLogger(__name__)

router = APIRouter()
dashboard_router = APIRouter()

# Grade mapping: result (1-5) -> quality_score
GRADE_MAP = {5: 0.97, 4: 0.85, 3: 0.70, 2: 0.50, 1: 0.30}
GRADE_LETTER = {5: "S", 4: "A", 3: "B", 2: "C", 1: "D"}
GRADE_RESULT = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


# -- Helpers -------------------------------------------------------------------


def _format_submission(row, feedback_map: dict | None = None):
    """Format a submission row for API response."""
    result = row.get("result") or 3
    payload = row.get("data_submission")
    # aiomysql returns JSON columns as strings — parse if needed
    if payload is None:
        payload = {}
    elif isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except (json.JSONDecodeError, ValueError):
            payload = {}
    sub_id = str(row["submission_id"])
    frontier_id = str(row.get("frontier_id", ""))
    task_id = str(row["task_id"])
    quality_grade = GRADE_LETTER.get(result, "B")

    unit_price = resolve_price(frontier_id, task_id, quality_grade)
    return {
        "submission_id": sub_id,
        "task_id": task_id,
        "frontier_id": frontier_id,
        "data": payload.get("data", payload) if isinstance(payload, dict) else payload,
        "quality_score": GRADE_MAP.get(result, 0.70),
        "quality_grade": quality_grade,
        "unit_price_usd": float(unit_price),
        "source": row.get("source") or "unknown",
        "created_at": row["gmt_create"].isoformat() if row.get("gmt_create") else None,
        "consumer_feedback": (feedback_map or {}).get(sub_id),
    }


async def _resolve_subscription(subscription_id: str, org_id: str) -> dict:
    """Look up subscription and verify ownership. Returns subscription row."""
    try:
        sub_res = (
            supabase.table("subscriptions")
            .select("id, org_id, frontier_id, task_ids, cursor_position, status, filters")
            .eq("id", subscription_id)
            .eq("org_id", org_id)
            .single()
            .execute()
        )
    except APIError as e:
        if "PGRST116" in str(e):
            raise HTTPException(status_code=404, detail="Subscription not found")
        raise
    if not sub_res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub_res.data["status"] != "active":
        raise HTTPException(status_code=400, detail="Subscription is not active")
    if not sub_res.data.get("frontier_id"):
        raise HTTPException(
            status_code=400,
            detail="This subscription is not frontier-based. Use /v1/data/pull instead.",
        )
    return sub_res.data


async def _get_task_ids(sub: dict) -> list[int]:
    """Resolve task IDs from subscription (explicit or all in frontier)."""
    if sub.get("task_ids"):
        return [int(tid) for tid in sub["task_ids"]]
    tasks = await fetch_all(
        "SELECT task_id FROM cfp_frontier_task "
        "WHERE frontier_id = %s AND deleted = 0",
        (int(sub["frontier_id"]),),
    )
    return [t["task_id"] for t in tasks]


async def _get_feedback_map(org_id: str, submission_ids: list[str]) -> dict:
    """Get consumer feedback for a batch of submission IDs."""
    if not submission_ids:
        return {}
    res = (
        supabase.table("consumer_feedback")
        .select("submission_id, feedback_type")
        .eq("org_id", org_id)
        .in_("submission_id", submission_ids)
        .execute()
    )
    return {r["submission_id"]: r["feedback_type"] for r in (res.data or [])}


async def _do_pull(
    subscription_id: str, org_id: str, cursor: str | None, limit: int,
    *, request: Request | None = None, api_key_id: str | None = None,
    user_id: str | None = None,
) -> dict:
    """Core pull logic shared by API-key and JWT endpoints."""
    sub = await _resolve_subscription(subscription_id, org_id)
    task_ids = await _get_task_ids(sub)

    if not task_ids:
        return {"data": [], "next_cursor": cursor, "has_more": False, "count": 0}

    stored_cursor = sub.get("cursor_position")

    effective_cursor = int(cursor) if cursor is not None else int(stored_cursor or 0)

    # Resolve quality grade filter from subscription filters
    sub_filters = sub.get("filters") or {}
    quality_grades = sub_filters.get("quality_grades") if sub_filters else None
    result_values: list[int] = []
    if quality_grades:
        result_values = [GRADE_RESULT[g] for g in quality_grades if g in GRADE_RESULT]

    placeholders = ",".join(["%s"] * len(task_ids))

    if result_values:
        grade_placeholders = ",".join(["%s"] * len(result_values))
        # NULL result maps to grade B (result=3); include nulls when B is selected
        null_clause = " OR s.result IS NULL" if 3 in result_values else ""
        grade_filter = f"AND (s.result IN ({grade_placeholders}){null_clause})"
        params = (*task_ids, effective_cursor, *result_values, limit + 1)
    else:
        grade_filter = ""
        params = (*task_ids, effective_cursor, limit + 1)

    rows = await fetch_all(
        f"""
        SELECT
            s.submission_id,
            s.task_id,
            t.frontier_id,
            s.data_submission,
            s.result,
            s.source,
            s.gmt_create
        FROM cfp_task_submission s
        JOIN cfp_frontier_task t ON t.task_id = s.task_id
        WHERE s.task_id IN ({placeholders})
            AND s.status = 'ADOPT'
            AND s.deleted = 0
            AND s.submission_id > %s
            {grade_filter}
        ORDER BY s.submission_id ASC
        LIMIT %s
        """,
        params,
    )

    has_more = len(rows) > limit
    rows = rows[:limit]

    submission_ids = [str(r["submission_id"]) for r in rows]
    feedback_map = await _get_feedback_map(org_id, submission_ids)

    data = [_format_submission(r, feedback_map) for r in rows]

    next_cursor = submission_ids[-1] if submission_ids else str(effective_cursor)

    supabase.table("subscriptions").update(
        {"cursor_position": next_cursor}
    ).eq("id", subscription_id).execute()

    # Meter usage + access log
    if data:
        item_costs = [
            {
                "submission_id": d["submission_id"],
                "task_id": d["task_id"],
                "unit_price_usd": d["unit_price_usd"],
            }
            for d in data
        ]
        total_cost = sum(d["unit_price_usd"] for d in data)

        supabase.table("usage_meter").insert({
            "org_id": org_id,
            "subscription_id": subscription_id,
            "event_type": "pull",
            "record_count": len(data),
        }).execute()

        if request:
            request.state.access_logged = True
            log_access(
                request=request,
                org_id=org_id,
                api_key_id=api_key_id,
                user_id=user_id,
                subscription_id=subscription_id,
                frontier_id=sub.get("frontier_id"),
                record_count=len(data),
                item_costs=item_costs,
                total_cost_usd=total_cost,
                response_status=200,
            )

    return {
        "data": data,
        "next_cursor": next_cursor,
        "has_more": has_more,
        "count": len(data),
    }


async def _do_feedback(
    submission_id: str,
    org_id: str,
    subscription_id: str,
    feedback_type: str,
    reason: str | None = None,
) -> dict:
    """Core feedback logic shared by API-key and JWT endpoints."""
    sub = await _resolve_subscription(subscription_id, org_id)

    # Verify submission exists in AliCloud MySQL
    row = await fetch_one(
        "SELECT s.submission_id, s.task_id, t.frontier_id "
        "FROM cfp_task_submission s "
        "JOIN cfp_frontier_task t ON t.task_id = s.task_id "
        "WHERE s.submission_id = %s AND s.deleted = 0",
        (int(submission_id),),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Upsert consumer feedback
    supabase.table("consumer_feedback").upsert(
        {
            "org_id": org_id,
            "subscription_id": sub["id"],
            "submission_id": submission_id,
            "task_id": str(row["task_id"]),
            "frontier_id": str(row["frontier_id"]),
            "feedback_type": feedback_type,
            "reason": reason,
        },
        on_conflict="org_id,submission_id",
    ).execute()

    # Meter usage
    supabase.table("usage_meter").insert({
        "org_id": org_id,
        "subscription_id": sub["id"],
        "event_type": feedback_type,
    }).execute()

    return {
        "ok": True,
        "submission_id": submission_id,
        "feedback": feedback_type,
    }


# -- Consumer API (API key auth) ----------------------------------------------


@router.get("/live/pull")
async def pull_live_data(
    request: Request,
    subscription_id: str = Query(...),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    key_info: dict = Depends(verify_api_key),
):
    """Pull adopted submissions from production MySQL, cursor-based."""
    check_subscription_scope(key_info, subscription_id)
    return await _do_pull(
        subscription_id, key_info["org_id"], cursor, limit,
        request=request, api_key_id=key_info["key_id"],
    )


class FeedbackRequest(BaseModel):
    subscription_id: str
    reason: str | None = None


@router.post("/live/items/{submission_id}/adopt")
async def adopt_live_item(
    submission_id: str,
    body: FeedbackRequest,
    key_info: dict = Depends(verify_api_key),
):
    """Record adopt feedback for a submission."""
    check_subscription_scope(key_info, body.subscription_id)
    return await _do_feedback(
        submission_id, key_info["org_id"], body.subscription_id, "adopt"
    )


@router.post("/live/items/{submission_id}/dispute")
async def dispute_live_item(
    submission_id: str,
    body: FeedbackRequest,
    key_info: dict = Depends(verify_api_key),
):
    """Record dispute feedback for a submission."""
    check_subscription_scope(key_info, body.subscription_id)
    return await _do_feedback(
        submission_id, key_info["org_id"], body.subscription_id, "dispute", body.reason
    )


# -- Dashboard API (JWT auth) -------------------------------------------------


@dashboard_router.get("/live/pull")
async def dashboard_pull_live_data(
    request: Request,
    org_id: str,
    subscription_id: str = Query(...),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    member: dict = Depends(require_org_member),
):
    """Pull adopted submissions from dashboard (JWT auth)."""
    return await _do_pull(
        subscription_id, org_id, cursor, limit,
        request=request, user_id=member.get("user_id"),
    )



@dashboard_router.post("/live/reset-cursor")
async def dashboard_reset_cursor(
    org_id: str,
    subscription_id: str = Query(...),
    member: dict = Depends(require_org_member),
):
    """Reset subscription cursor to 0 (pull from beginning)."""
    sub = await _resolve_subscription(subscription_id, org_id)
    supabase.table("subscriptions").update({"cursor_position": "0"}).eq("id", sub["id"]).execute()
    return {"ok": True, "cursor_position": "0"}


@dashboard_router.post("/live/items/{submission_id}/adopt")
async def dashboard_adopt_live_item(
    org_id: str,
    submission_id: str,
    body: FeedbackRequest,
    member: dict = Depends(require_org_member),
):
    """Record adopt feedback from dashboard."""
    return await _do_feedback(
        submission_id, org_id, body.subscription_id, "adopt"
    )


@dashboard_router.post("/live/items/{submission_id}/dispute")
async def dashboard_dispute_live_item(
    org_id: str,
    submission_id: str,
    body: FeedbackRequest,
    member: dict = Depends(require_org_member),
):
    """Record dispute feedback from dashboard."""
    return await _do_feedback(
        submission_id, org_id, body.subscription_id, "dispute", body.reason
    )
