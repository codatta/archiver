from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.client import supabase

router = APIRouter(prefix="/v1/tasks", tags=["tasks"])


class TaskInstanceResponse(BaseModel):
    id: str
    task_id: str
    campaign_id: str
    contributor_id: str | None
    status: str
    priority: str | None
    data_url: str | None
    thumbnail_url: str | None
    quality_grade: str | None
    pay_amount: float | None
    created_at: str


@router.get("/instances", response_model=list[TaskInstanceResponse])
async def list_task_instances(
    contributor_id: str | None = None,
    campaign_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
):
    """List task instances with optional filters."""
    query = supabase.table("task_instances").select("*")

    if contributor_id:
        query = query.eq("contributor_id", contributor_id)
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    if status:
        query = query.eq("status", status)

    result = query.limit(limit).order("created_at", desc=True).execute()
    return result.data


@router.get("/instances/available", response_model=list[TaskInstanceResponse])
async def list_available_instances(campaign_id: str | None = None, limit: int = 50):
    """List available (unclaimed) task instances."""
    query = supabase.table("task_instances").select("*").eq("status", "available")
    if campaign_id:
        query = query.eq("campaign_id", campaign_id)
    result = query.limit(limit).order("created_at", desc=True).execute()
    return result.data


@router.post("/instances/{instance_id}/claim")
async def claim_instance(instance_id: str, contributor_id: str | None = None):
    """Claim a task instance to work on."""
    if not contributor_id:
        raise HTTPException(401, "Not authenticated")

    result = (
        supabase.table("task_instances")
        .update({
            "contributor_id": contributor_id,
            "status": "claimed",
            "claimed_at": "now()",
        })
        .eq("id", instance_id)
        .eq("status", "available")
        .execute()
    )
    if not result.data:
        raise HTTPException(409, "Instance already claimed or not available")
    return result.data[0]


@router.post("/instances/{instance_id}/submit")
async def submit_instance(instance_id: str, annotation_data: dict | None = None):
    """Submit completed work for a task instance."""
    update = {
        "status": "submitted",
        "submitted_at": "now()",
    }
    if annotation_data:
        update["annotation_data"] = annotation_data

    result = (
        supabase.table("task_instances")
        .update(update)
        .eq("id", instance_id)
        .in_("status", ["claimed", "in_progress"])
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Instance not found or not in claimable state")
    return result.data[0]
