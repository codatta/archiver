from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import require_org_member
from app.db import supabase

router = APIRouter()


class CreateSubscriptionRequest(BaseModel):
    vertical_id: str | None = None
    topic_ids: list[str] | None = None
    domain_id: str | None = None
    frontier_id: str | None = None  # deprecated alias for domain_id
    task_ids: list[str] | None = None
    delivery_mode: str = "pull"
    webhook_url: str | None = None
    filters: dict | None = None
    auto_accept: bool = False


class UpdateFiltersRequest(BaseModel):
    filters: dict | None = None
    auto_accept: bool | None = None


@router.get("")
async def list_subscriptions(org_id: str, member: dict = Depends(require_org_member)):
    res = (
        supabase.table("subscriptions")
        .select("*, verticals(id, slug, name)")
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"data": res.data}


@router.post("")
async def create_subscription(
    org_id: str, body: CreateSubscriptionRequest, member: dict = Depends(require_org_member)
):
    # Accept domain_id or legacy frontier_id
    effective_domain_id = body.domain_id or body.frontier_id
    if not body.vertical_id and not effective_domain_id:
        raise HTTPException(
            status_code=400,
            detail="Either vertical_id or domain_id is required",
        )

    # Prevent duplicate active subscriptions for same org + frontier/vertical
    if effective_domain_id:
        existing = (
            supabase.table("subscriptions")
            .select("id")
            .eq("org_id", org_id)
            .eq("frontier_id", effective_domain_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "An active subscription for this frontier already exists",
                    "existing_id": existing.data[0]["id"],
                },
            )
    elif body.vertical_id:
        existing = (
            supabase.table("subscriptions")
            .select("id")
            .eq("org_id", org_id)
            .eq("vertical_id", body.vertical_id)
            .eq("status", "active")
            .limit(1)
            .execute()
        )
        if existing.data:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "An active subscription for this vertical already exists",
                    "existing_id": existing.data[0]["id"],
                },
            )

    row = {
        "org_id": org_id,
        "delivery_mode": body.delivery_mode,
        "filters": body.filters,
        "auto_accept": body.auto_accept,
        "status": "active",
    }
    if effective_domain_id:
        # DB column is still frontier_id until migration
        row["frontier_id"] = effective_domain_id
        row["task_ids"] = body.task_ids
        row["webhook_url"] = body.webhook_url
    if body.vertical_id:
        row["vertical_id"] = body.vertical_id
        row["topic_ids"] = body.topic_ids

    res = supabase.table("subscriptions").insert(row).execute()
    return {"data": res.data[0]}


@router.patch("/{sub_id}")
async def update_subscription(
    org_id: str, sub_id: str, body: UpdateFiltersRequest, member: dict = Depends(require_org_member)
):
    update = body.model_dump(exclude_none=True)
    res = (
        supabase.table("subscriptions")
        .update(update)
        .eq("id", sub_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"data": res.data[0]}


@router.post("/{sub_id}/cancel")
async def cancel_subscription(org_id: str, sub_id: str, member: dict = Depends(require_org_member)):
    res = (
        supabase.table("subscriptions")
        .update({"status": "cancelled"})
        .eq("id", sub_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    return {"data": res.data[0]}
