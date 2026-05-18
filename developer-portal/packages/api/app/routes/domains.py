"""Browse production domains (data verticals) from AliCloud MySQL (supply-side).

Public endpoints for discovering available data sources.
Internally these map to "frontiers" in cfp_metacore (cfp_frontier /
cfp_frontier_task / cfp_task_submission).

NOTE: The `supply` Postgres schema in Supabase (supply_db.py) is a future
migration target — not yet in production. These endpoints query AliCloud MySQL
directly via mysql_db.py until the migration is validated.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from app.access_log import log_access
from app.auth import get_current_user
from app.mysql_db import fetch_all, fetch_one

router = APIRouter()

_tasks_cache: dict[str, tuple[float, list]] = {}
_TASKS_TTL = 60.0

# Grade mapping: result (1-5) -> quality_score
GRADE_MAP = {5: 0.97, 4: 0.85, 3: 0.70, 2: 0.50, 1: 0.30}
GRADE_LETTER = {5: "S", 4: "A", 3: "B", 2: "C", 1: "D"}


@router.get("")
async def list_domains(status: Literal["online", "all"] = Query(default="online")):
    """List available domains from AliCloud MySQL.

    Query params:
        status: "online" (default) or "all"

    total_submissions is read from cfp_frontier.ext_info.adopted_count
    (adopted/qualified submission count, updated by supply-side worker every ~5 min).
    """
    base_sql = """
        SELECT
            f.frontier_id,
            f.title,
            f.status,
            f.gmt_create AS created_at,
            COUNT(DISTINCT t.task_id) AS task_count,
            f.ext_info
        FROM cfp_frontier f
        LEFT JOIN cfp_frontier_task t
            ON t.frontier_id = f.frontier_id AND t.deleted = 0
        WHERE f.deleted = 0"""
    if status == "online":
        base_sql += " AND f.status = 'ONLINE'"
    base_sql += " GROUP BY f.frontier_id, f.title, f.status, f.gmt_create, f.ext_info"
    rows = await fetch_all(base_sql)

    # Filter out domains older than 3 days with zero submissions
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    data = []
    for r in rows:
        created = r.get("created_at")
        # Read adopted_count from ext_info JSON field (adopted/qualified submissions)
        ext_info = r.get("ext_info")
        if isinstance(ext_info, str):
            try:
                ext_info = json.loads(ext_info)
            except (json.JSONDecodeError, ValueError):
                ext_info = {}
        if not isinstance(ext_info, dict):
            ext_info = {}
        subs = int(ext_info.get("adopted_count") or 0)
        if subs == 0 and created:
            # aiomysql returns naive datetimes — treat as UTC
            created_utc = (
                created.replace(tzinfo=timezone.utc)
                if created.tzinfo is None
                else created
            )
            if created_utc < cutoff:
                continue
        data.append({
            "domain_id": str(r["frontier_id"]),
            "title": r["title"],
            "status": r["status"],
            "task_count": int(r["task_count"]),
            "total_submissions": subs,
        })

    # Sort by popularity (most submissions first) to match pre-optimization behavior
    data.sort(key=lambda d: d["total_submissions"], reverse=True)
    return {"data": data}


@router.get("/{domain_id}/tasks")
async def list_domain_tasks(domain_id: str):
    """List tasks under a domain with submission counts."""
    now = time.time()
    cached = _tasks_cache.get(domain_id)
    if cached and now - cached[0] < _TASKS_TTL:
        return {"data": cached[1]}

    rows = await fetch_all(
        """
        SELECT
            t.task_id,
            t.frontier_id,
            t.name,
            t.task_type,
            t.status,
            COUNT(s.submission_id) AS submission_count
        FROM cfp_frontier_task t
        LEFT JOIN cfp_task_submission s
            ON s.task_id = t.task_id
            AND s.deleted = 0
            AND s.status = 'ADOPT'
        WHERE t.frontier_id = %s AND t.deleted = 0
        GROUP BY t.task_id, t.frontier_id,
                 t.name, t.task_type, t.status
        ORDER BY submission_count DESC
        """,
        (int(domain_id),),
    )

    data = [
        {
            "task_id": str(r["task_id"]),
            "domain_id": str(r["frontier_id"]),
            "name": r["name"],
            "task_type": r["task_type"],
            "status": r["status"],
            "submission_count": int(r["submission_count"]),
        }
        for r in rows
    ]
    _tasks_cache[domain_id] = (now, data)
    return {"data": data}


@router.get("/{domain_id}/tasks/{task_id}/preview")
async def preview_task_submissions(
    request: Request,
    domain_id: str,
    task_id: str,
    limit: int = Query(default=5, le=20),
    _user: dict = Depends(get_current_user),
):
    """Preview sample adopted submissions for a task. JWT required."""
    task = await fetch_one(
        "SELECT task_id FROM cfp_frontier_task "
        "WHERE task_id = %s AND frontier_id = %s AND deleted = 0",
        (int(task_id), int(domain_id)),
    )
    if not task:
        raise HTTPException(
            status_code=404, detail="Task not found in this domain"
        )

    rows = await fetch_all(
        """
        SELECT
            s.submission_id,
            s.data_submission,
            s.result,
            s.source,
            s.gmt_create AS created_at,
            a.rating AS audit_rating,
            a.reason AS audit_reason
        FROM cfp_task_submission s
        LEFT JOIN cfp_task_audit_record a
            ON a.submission_id = s.submission_id AND a.deleted = 0
        WHERE s.task_id = %s
            AND s.status = 'ADOPT'
            AND s.deleted = 0
        ORDER BY s.gmt_create DESC
        LIMIT %s
        """,
        (int(task_id), limit),
    )

    data = []
    for r in rows:
        result = r["result"] or 3
        payload = r["data_submission"]
        # aiomysql returns JSON columns as strings — parse if needed
        if payload is None:
            payload = {}
        elif isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except (json.JSONDecodeError, ValueError):
                payload = {}

        data.append({
            "submission_id": str(r["submission_id"]),
            "data": (
                payload.get("data", payload)
                if isinstance(payload, dict) else payload
            ),
            "quality_score": GRADE_MAP.get(result, 0.70),
            "quality_grade": GRADE_LETTER.get(result, "B"),
            "source": r["source"] or "unknown",
            "created_at": (
                r["created_at"].isoformat()
                if r["created_at"] else None
            ),
            "audit_rating": r["audit_rating"],
            "audit_reason": r["audit_reason"],
        })

    # Log preview access (free, but tracked for auditing)
    request.state.access_logged = True
    log_access(
        request=request,
        user_id=_user.get("id"),
        frontier_id=domain_id,
        record_count=len(data),
        total_cost_usd=0.0,
        response_status=200,
    )

    return {"data": data}
