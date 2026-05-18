from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.db.client import supabase

router = APIRouter(prefix="/v1/contributions", tags=["contributions"])


class ContributionResponse(BaseModel):
    id: str
    instance_id: str
    contributor_id: str
    campaign_id: str
    task_type: str
    status: str
    quality_grade: str | None
    pay_amount: float | None
    pay_type: str | None
    chain_id: str | None
    submitted_at: str
    created_at: str


@router.get("", response_model=list[ContributionResponse])
async def list_contributions(
    contributor_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
):
    """List contributions with pagination and filters."""
    query = supabase.table("contributions").select("*")

    if contributor_id:
        query = query.eq("contributor_id", contributor_id)
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    if status:
        query = query.eq("status", status)

    result = (
        query.order("submitted_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return result.data


@router.get("/stats")
async def contribution_stats(contributor_id: str):
    """Get contribution stats for a contributor."""
    result = supabase.table("contributions").select("*").eq("contributor_id", contributor_id).execute()
    data = result.data or []

    total = len(data)
    accepted = sum(1 for d in data if d["status"] == "accepted")
    rejected = sum(1 for d in data if d["status"] == "rejected")
    in_review = sum(1 for d in data if d["status"] == "in_review")
    total_earned = sum(float(d.get("pay_amount") or 0) for d in data if d["status"] == "accepted")

    return {
        "total": total,
        "accepted": accepted,
        "rejected": rejected,
        "in_review": in_review,
        "total_earned": round(total_earned, 2),
    }
