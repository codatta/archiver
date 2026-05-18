import logging

import resend
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.auth import get_current_user
from app.config import settings
from app.db import supabase
from app.services.email_renderer import FROM_ADDRESS, body_text, render_email

logger = logging.getLogger(__name__)
router = APIRouter()


def _send_welcome_email(email: str, role: str, org_id: str) -> None:
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping welcome to %s", email)
        return
    try:
        org_res = (
            supabase.table("organizations")
            .select("name")
            .eq("id", org_id)
            .single()
            .execute()
        )
        org_name = (
            org_res.data["name"]
            if org_res.data
            else "your organization"
        )
        resend.api_key = settings.resend_api_key
        html = render_email(
            heading=f"Welcome to {org_name}",
            body_html=body_text(
                f"You've successfully joined <strong>"
                f"{org_name}</strong> as a "
                f"<strong>{role}</strong>.",
                "Head to the dashboard to manage API keys, "
                "browse data sources, and start pulling data.",
            ),
            cta_label="Go to dashboard",
            cta_url=f"{settings.webapp_url}/dashboard",
        )
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [email],
            "subject": f"Welcome to {org_name} on Codatta",
            "html": html,
        })
    except Exception:
        logger.exception("Failed to send welcome email to %s", email)


def _auto_join_pending_invitations(user_id: str, email: str) -> dict | None:
    """Check for pending invitations or domain allowlist match and auto-join.

    Returns {"org_id": str, "org_name": str, "join_method": "invite" | "domain"}
    or None if no match.
    """
    # 1. Check email-specific pending invitation first
    inv_res = (
        supabase.table("org_invitations")
        .select("*")
        .eq("email", email)
        .is_("accepted_at", "null")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if inv_res.data:
        invitation = inv_res.data[0]
        supabase.table("org_memberships").insert({
            "org_id": invitation["org_id"],
            "user_id": user_id,
            "role": invitation["role"],
            "permissions": invitation.get("permissions"),
            "invited_by": invitation.get("invited_by"),
        }).execute()
        supabase.table("org_invitations").update({
            "accepted_at": "now()",
        }).eq("id", invitation["id"]).execute()
        _send_welcome_email(email, invitation["role"], invitation["org_id"])
        # Fetch org name for response
        org_res = (
            supabase.table("organizations")
            .select("name")
            .eq("id", invitation["org_id"])
            .single()
            .execute()
        )
        org_name = org_res.data["name"] if org_res.data else "your organization"
        return {"org_id": invitation["org_id"], "org_name": org_name, "join_method": "invite"}

    return None


def _get_org_id(user_id: str) -> str | None:
    """Look up the first org_id for a user."""
    membership = (
        supabase.table("org_memberships")
        .select("org_id")
        .eq("user_id", user_id)
        .order("joined_at")
        .limit(1)
        .execute()
    )
    if membership.data:
        return membership.data[0]["org_id"]
    return None


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    name: str | None = None
    backup_email: EmailStr | None = None



@router.post("/sync-profile")
async def sync_profile(user: dict = Depends(get_current_user)):
    """Create public.users row and auto-join pending invitations.

    Called by the frontend after Supabase auth signup. Idempotent — safe
    to call multiple times.
    """
    auth_id = user["id"]
    email = user["email"]
    full_name = (user.get("user_metadata") or {}).get("full_name", "")

    # Check if users row already exists
    existing = (
        supabase.table("users")
        .select("id")
        .eq("auth_id", auth_id)
        .execute()
    )
    if existing.data:
        user_id = existing.data[0]["id"]
        org_id = _get_org_id(user_id)

        if org_id:
            return {
                "user": {
                    "id": user_id, "email": email,
                    "org_id": org_id, "auto_joined": False,
                    "org_name": None,
                }
            }

        # User exists but has no membership — try auto-join
        join_result = _auto_join_pending_invitations(user_id, email)
        if join_result:
            return {
                "user": {
                    "id": user_id, "email": email,
                    "org_id": join_result["org_id"],
                    "org_name": join_result["org_name"],
                    "auto_joined": True,
                }
            }
        return {
            "user": {
                "id": user_id, "email": email,
                "org_id": None, "auto_joined": False, "org_name": None,
            }
        }

    # Create users row
    user_insert = supabase.table("users").insert({
        "auth_id": auth_id,
        "email": email,
        "name": full_name,
    }).execute()
    user_id = user_insert.data[0]["id"] if user_insert.data else None

    join_result = None
    if user_id:
        join_result = _auto_join_pending_invitations(user_id, email)

    org_id = join_result["org_id"] if join_result else None
    org_name = join_result["org_name"] if join_result else None
    auto_joined = join_result is not None

    return {
        "user": {
            "id": user_id, "email": email,
            "org_id": org_id, "org_name": org_name, "auto_joined": auto_joined,
        }
    }


@router.post("/signin")
async def signin(body: SignInRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password,
        })
        return {
            "user": {"id": res.user.id, "email": res.user.email},
            "session": {
                "access_token": res.session.access_token,
                "refresh_token": res.session.refresh_token,
                "expires_at": res.session.expires_at,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    # Look up the public.users record by auth_id
    res = (
        supabase.table("users")
        .select("id, email, name, avatar_url, backup_email")
        .eq("auth_id", user["id"])
        .single()
        .execute()
    )

    org_id = None
    if res.data:
        membership = (
            supabase.table("org_memberships")
            .select("org_id, role")
            .eq("user_id", res.data["id"])
            .order("joined_at")
            .limit(1)
            .execute()
        )
        if membership.data:
            org_id = membership.data[0]["org_id"]

    return {"user": {**user, "profile": res.data, "org_id": org_id}}


@router.patch("/profile")
async def update_profile(body: UpdateProfileRequest, user: dict = Depends(get_current_user)):
    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name
    if "backup_email" in body.model_fields_set:
        updates["backup_email"] = str(body.backup_email) if body.backup_email else None

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    res = (
        supabase.table("users")
        .update(updates)
        .eq("auth_id", user["id"])
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="User not found")
    return {"data": res.data[0]}


@router.delete("/account")
async def delete_account(
    confirm_email: str,
    user: dict = Depends(get_current_user),
):
    """Permanently delete the current user's account and associated data.

    Requires the user to confirm by providing their email address.

    Deletion order (designed so auth deletion gates destructive ops):
      1. Remove org memberships (reversible — user could be re-invited)
      2. Revoke pending invitations sent/received (reversible)
      3. Revoke user's API keys (reversible — new keys can be created)
      4. Delete auth user (irreversible gate — if this fails, abort)
      5. Delete user profile
      6. Clean up orgs where user was the last member (irreversible)

    Org-scoped data (delivery items, subscriptions, accounts, transactions,
    API keys, org invitations, org settings) is deleted only for organizations
    where this user was the last remaining member, and only after auth
    deletion succeeds.
    """
    auth_id = user["id"]
    email = user["email"]

    if confirm_email.strip().lower() != email.lower():
        raise HTTPException(
            status_code=400,
            detail="Email does not match your account",
        )

    # Look up public.users row
    user_res = (
        supabase.table("users")
        .select("id")
        .eq("auth_id", auth_id)
        .single()
        .execute()
    )
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User profile not found")

    user_db_id = user_res.data["id"]
    steps: list[dict] = []

    # Step 1: Find and remove org memberships
    mem_res = (
        supabase.table("org_memberships")
        .select("org_id, role")
        .eq("user_id", user_db_id)
        .execute()
    )
    memberships = mem_res.data or []
    if memberships:
        supabase.table("org_memberships").delete().eq(
            "user_id", user_db_id
        ).execute()
    steps.append(
        {"step": "memberships", "deleted": len(memberships)}
    )

    # Step 2: Remove pending invitations sent and received by this user
    inv_sent_res = (
        supabase.table("org_invitations")
        .delete()
        .eq("invited_by", user_db_id)
        .is_("accepted_at", None)
        .execute()
    )
    inv_recv_res = (
        supabase.table("org_invitations")
        .delete()
        .eq("email", email)
        .is_("accepted_at", None)
        .execute()
    )
    steps.append(
        {
            "step": "invitations",
            "deleted": len(inv_sent_res.data or [])
            + len(inv_recv_res.data or []),
        }
    )

    # Step 3: Revoke API keys created by this user
    keys_res = (
        supabase.table("api_keys")
        .delete()
        .eq("created_by", auth_id)
        .execute()
    )
    steps.append(
        {"step": "api_keys", "deleted": len(keys_res.data or [])}
    )

    # Step 4: Delete auth user — this is the irreversible gate.
    # If this fails, profile is intact and the user can retry.
    try:
        supabase.auth.admin.delete_user(auth_id)
        steps.append({"step": "auth", "deleted": 1})
    except Exception as e:
        logger.error("Failed to delete auth user %s: %s", auth_id, e)
        steps.append({"step": "auth", "deleted": 0, "error": str(e)})
        raise HTTPException(
            status_code=502,
            detail="Failed to delete auth user. Profile preserved for retry.",
        )

    # Step 5: Delete user profile (only after auth is confirmed deleted)
    supabase.table("users").delete().eq(
        "auth_id", auth_id
    ).execute()
    steps.append({"step": "profile", "deleted": 1})

    # Step 6: Clean up orgs where user was the last member
    # This runs AFTER auth deletion succeeds, so no partial-delete risk.
    for mem in memberships:
        org_id = mem["org_id"]
        remaining = (
            supabase.table("org_memberships")
            .select("id")
            .eq("org_id", org_id)
            .execute()
        )
        if not remaining.data:
            _delete_org_data(org_id)
            supabase.table("organizations").delete().eq(
                "id", org_id
            ).execute()
            steps.append(
                {"step": "org_cleanup", "org_id": org_id}
            )

    return {"deleted": True, "steps": steps}


def _delete_org_data(org_id: str) -> None:
    """Remove all data belonging to an org when the last member is deleted."""
    # Order matters: child records first
    supabase.table("delivery_items").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("subscriptions").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("transactions").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("accounts").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("api_keys").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("org_invitations").delete().eq(
        "org_id", org_id
    ).execute()
    supabase.table("org_settings").delete().eq(
        "org_id", org_id
    ).execute()
