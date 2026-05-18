from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.db.client import supabase

router = APIRouter(prefix="/v1/contributors", tags=["contributors"])


class ContributorProfile(BaseModel):
    id: str
    username: str
    display_name: str
    email: str
    avatar_url: str | None
    reputation: int
    tier: str
    skills: list
    created_at: str


class ContributorUpdate(BaseModel):
    display_name: str | None = None
    username: str | None = None
    avatar_url: str | None = None
    skills: list | None = None
    preferences: dict | None = None


@router.get("/me", response_model=ContributorProfile)
async def get_my_profile(auth_id: str | None = None):
    """Get current contributor profile. Auth_id passed via header in production."""
    if not auth_id:
        raise HTTPException(401, "Not authenticated")

    result = supabase.table("contributors").select("*").eq("auth_id", auth_id).single().execute()
    if not result.data:
        raise HTTPException(404, "Contributor profile not found")
    return result.data


@router.patch("/me", response_model=ContributorProfile)
async def update_my_profile(body: ContributorUpdate, auth_id: str | None = None):
    """Update current contributor profile."""
    if not auth_id:
        raise HTTPException(401, "Not authenticated")

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(400, "No fields to update")

    result = (
        supabase.table("contributors")
        .update(update_data)
        .eq("auth_id", auth_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Contributor not found")
    return result.data[0]
