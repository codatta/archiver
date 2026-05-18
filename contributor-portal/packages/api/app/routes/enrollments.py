from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db.client import supabase

router = APIRouter(prefix="/v1/enrollments", tags=["enrollments"])


class EnrollRequest(BaseModel):
    campaign_id: str


class EnrollmentResponse(BaseModel):
    id: str
    contributor_id: str
    campaign_id: str
    status: str
    enrolled_at: str
    total_submitted: int
    total_accepted: int
    total_earned: float


@router.get("", response_model=list[EnrollmentResponse])
async def list_enrollments(contributor_id: str):
    """List enrollments for a contributor."""
    result = (
        supabase.table("enrollments")
        .select("*")
        .eq("contributor_id", contributor_id)
        .order("enrolled_at", desc=True)
        .execute()
    )
    return result.data


@router.post("", response_model=EnrollmentResponse)
async def enroll(body: EnrollRequest, contributor_id: str | None = None):
    """Enroll in a campaign."""
    if not contributor_id:
        raise HTTPException(401, "Not authenticated")

    result = (
        supabase.table("enrollments")
        .insert({"contributor_id": contributor_id, "campaign_id": body.campaign_id})
        .execute()
    )
    if not result.data:
        raise HTTPException(400, "Failed to enroll")
    return result.data[0]


@router.patch("/{enrollment_id}/unenroll")
async def unenroll(enrollment_id: str):
    """Unenroll from a campaign."""
    result = (
        supabase.table("enrollments")
        .update({"status": "unenrolling", "unenrolled_at": "now()"})
        .eq("id", enrollment_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, "Enrollment not found")
    return {"status": "unenrolling", "message": "In-progress tasks remain until completed."}
