from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import get_current_user, require_org_admin, require_org_member
from app.db import supabase

router = APIRouter()


class UpdateOrgRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    business_url: str | None = None
    industry: str | None = None
    company_size: str | None = None
    billing_email: str | None = None
    country: str | None = None
    backup_email: str | None = None
    logo_url: str | None = None


@router.post("")
async def create_org(body: UpdateOrgRequest, user: dict = Depends(get_current_user)):
    try:
        res = (
            supabase.table("organizations")
            .insert(body.model_dump(exclude_none=True))
            .execute()
        )
        return {"data": res.data[0]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{org_id}")
async def get_org(org_id: str, member: dict = Depends(require_org_member)):
    res = (
        supabase.table("organizations")
        .select("*")
        .eq("id", org_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"data": res.data}


@router.patch("/{org_id}")
async def update_org(
    org_id: str, body: UpdateOrgRequest, admin: dict = Depends(require_org_admin)
):
    res = (
        supabase.table("organizations")
        .update(body.model_dump(exclude_none=True))
        .eq("id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Organization not found")
    return {"data": res.data[0]}


@router.get("/{org_id}/settings")
async def get_org_settings(
    org_id: str, member: dict = Depends(require_org_member)
):
    """Return org settings (auto_adopt_hours, etc.)."""
    res = (
        supabase.table("org_settings")
        .select("*")
        .eq("org_id", org_id)
        .execute()
    )
    if res.data:
        return {"data": res.data[0]}
    # Auto-create with defaults
    new = (
        supabase.table("org_settings")
        .insert({"org_id": org_id})
        .execute()
    )
    return {"data": new.data[0] if new.data else {"auto_adopt_hours": 48}}


@router.delete("/{org_id}")
async def delete_org(org_id: str, member: dict = Depends(require_org_admin)):
    supabase.table("organizations").delete().eq("id", org_id).execute()
    return {"ok": True}
