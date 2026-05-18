import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.auth import get_current_user
from app.db import supabase
from app.routes.members import send_invite_email
from app.services.invite_batch import queue_invite_notification

router = APIRouter()

KEY_PREFIX = "hb_live_sk_"


class CreateOrgRequest(BaseModel):
    name: str
    slug: str
    logo_url: str | None = None
    business_url: str | None = None
    industry: str | None = None
    company_size: str | None = None
    billing_email: str | None = None
    country: str | None = None


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = "member"


class InviteBatchRequest(BaseModel):
    org_id: str
    invites: list[InviteRequest]


def _get_user_id(auth_id: str) -> str:
    """Look up public.users.id from auth_id."""
    res = (
        supabase.table("users")
        .select("id")
        .eq("auth_id", auth_id)
        .single()
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=400, detail="User profile not found")
    return res.data["id"]


@router.get("/org/check")
async def check_org_availability(
    name: str = "",
    slug: str = "",
    user: dict = Depends(get_current_user),
):
    """Check whether an org name and slug are available.

    Returns {"name_available": bool, "slug_available": bool}.
    Name check is case-insensitive (ILIKE). Slug check is exact.
    """
    name = name.strip()
    slug = slug.strip()

    name_available = True
    slug_available = True

    if name:
        res = (
            supabase.table("organizations")
            .select("id")
            .ilike("name", name)
            .limit(1)
            .execute()
        )
        name_available = len(res.data) == 0

    if slug:
        res = (
            supabase.table("organizations")
            .select("id")
            .eq("slug", slug)
            .limit(1)
            .execute()
        )
        slug_available = len(res.data) == 0

    return {"name_available": name_available, "slug_available": slug_available}


@router.post("/skip")
async def skip_onboarding(user: dict = Depends(get_current_user)):
    """Record that the user chose to skip org creation.

    Sets users.onboarding_skipped_at to the current timestamp.
    The user lands on the dashboard in no-org mode.
    """
    user_id = _get_user_id(user["id"])
    supabase.table("users").update(
        {"onboarding_skipped_at": datetime.now(timezone.utc).isoformat()}
    ).eq("id", user_id).execute()

    return {"ok": True}


@router.post("/org")
async def create_org(body: CreateOrgRequest, user: dict = Depends(get_current_user)):
    """Step 1: Create org, owner membership, and account."""
    if not body.name.strip():
        raise HTTPException(status_code=400, detail="Organization name is required")
    if not body.slug.strip():
        raise HTTPException(status_code=400, detail="Organization slug is required")

    # Check slug uniqueness
    existing = (
        supabase.table("organizations")
        .select("id")
        .eq("slug", body.slug)
        .execute()
    )
    if existing.data:
        raise HTTPException(status_code=409, detail="Slug already taken")

    user_id = _get_user_id(user["id"])

    # Create org
    org_data = body.model_dump(exclude_none=True)
    org_res = supabase.table("organizations").insert(org_data).execute()
    org = org_res.data[0]

    # Create owner membership
    supabase.table("org_memberships").insert({
        "org_id": org["id"],
        "user_id": user_id,
        "role": "owner",
    }).execute()

    # Create account (balance)
    supabase.table("accounts").insert({
        "org_id": org["id"],
    }).execute()

    return {"data": org}


@router.post("/invite")
async def invite_members(
    body: InviteBatchRequest,
    user: dict = Depends(get_current_user),
):
    """Step 2: Invite team members to the org."""
    user_id = _get_user_id(user["id"])

    # Look up org name for the invite email
    org_res = (
        supabase.table("organizations")
        .select("name")
        .eq("id", body.org_id)
        .single()
        .execute()
    )
    org_name = org_res.data["name"] if org_res.data else "your organization"

    results = []
    for invite in body.invites:
        if invite.role not in ("admin", "member"):
            continue

        # Look up invitee by email in users table
        invitee = (
            supabase.table("users")
            .select("id")
            .eq("email", invite.email)
            .execute()
        )

        inviter_email = user.get("email", "")

        if invitee.data:
            # User exists — create membership directly
            res = (
                supabase.table("org_memberships")
                .insert({
                    "org_id": body.org_id,
                    "user_id": invitee.data[0]["id"],
                    "role": invite.role,
                    "invited_by": user_id,
                    "invited_at": datetime.now(timezone.utc).isoformat(),
                })
                .execute()
            )
            email_sent = send_invite_email(invite.email, invite.role, org_name)
            if inviter_email:
                queue_invite_notification(inviter_email, invite.email, org_name, "added")
            result = res.data[0]
            result["email_sent"] = email_sent
            results.append(result)
        else:
            # User doesn't exist yet — store as pending invite
            (
                supabase.table("org_invitations")
                .insert({
                    "org_id": body.org_id,
                    "email": invite.email,
                    "role": invite.role,
                    "invited_by": user_id,
                })
                .execute()
            )
            email_sent = send_invite_email(invite.email, invite.role, org_name)
            if inviter_email:
                queue_invite_notification(inviter_email, invite.email, org_name, "pending_signup")
            results.append({
                "email": invite.email,
                "role": invite.role,
                "status": "pending_signup",
                "email_sent": email_sent,
            })

    return {"data": results}


@router.post("/complete")
async def complete_onboarding(
    org_id: str,
    user: dict = Depends(get_current_user),
):
    """Step 3: Mark onboarding as completed (no API key created)."""
    supabase.table("organizations").update({
        "onboarding_completed": True,
    }).eq("id", org_id).execute()

    return {"data": {"completed": True}}


@router.post("/api-key")
async def create_first_key(
    org_id: str,
    user: dict = Depends(get_current_user),
):
    """Legacy: Generate the first API key for the org.

    Kept for backward compatibility — no longer called from onboarding UI.
    """
    raw_key = KEY_PREFIX + secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    expires_at = (
        datetime.now(timezone.utc) + timedelta(days=90)
    ).isoformat()

    res = (
        supabase.table("api_keys")
        .insert({
            "org_id": org_id,
            "name": "Default",
            "key_hash": key_hash,
            "key_prefix": raw_key[:20],
            "status": "active",
            "expires_at": expires_at,
        })
        .execute()
    )

    # Mark onboarding as completed
    supabase.table("organizations").update({
        "onboarding_completed": True,
    }).eq("id", org_id).execute()

    return {"data": {**res.data[0], "raw_key": raw_key}}
