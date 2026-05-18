import logging
from typing import List, Optional

import resend
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr

from app.auth import require_org_admin, require_org_member
from app.config import settings
from app.db import supabase
from app.services.email_renderer import FROM_ADDRESS, body_text, render_email
from app.services.invite_batch import queue_invite_notification

router = APIRouter()


ALL_PERMISSIONS = [
    "data.read", "subscriptions.manage", "members.invite",
    "keys.manage", "billing.manage",
]
DEFAULT_MEMBER_PERMISSIONS = ["data.read", "subscriptions.manage"]
DEFAULT_ADMIN_PERMISSIONS = ALL_PERMISSIONS


class CheckEmailsRequest(BaseModel):
    emails: List[EmailStr]


class InviteMemberRequest(BaseModel):
    email: EmailStr
    role: str = "member"
    permissions: Optional[List[str]] = None


class UpdateMemberRequest(BaseModel):
    role: Optional[str] = None
    permissions: Optional[List[str]] = None


class UpdateRoleRequest(BaseModel):
    role: str


def _default_permissions(role: str) -> List[str]:
    if role in ("owner", "admin"):
        return ALL_PERMISSIONS
    return DEFAULT_MEMBER_PERMISSIONS


logger = logging.getLogger(__name__)


def send_invite_email(
    email: str, role: str, org_name: str,
) -> bool:
    """Send invitation email to the invitee."""
    if not settings.resend_api_key:
        logger.warning(
            "RESEND_API_KEY not set — skipping invite to %s", email,
        )
        return False
    try:
        resend.api_key = settings.resend_api_key
        html = render_email(
            heading=f"You're invited to {org_name} on Humanbased",
            body_html=body_text(
                f"You've been invited to join <strong>{org_name}"
                f"</strong> on Humanbased as a <strong>{role}</strong>.",
                "Sign in to accept the invitation and start "
                "collaborating with your team.",
            ),
            cta_label="Accept invitation",
            cta_url=f"{settings.webapp_url}/auth/signin",
        )
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [email],
            "subject": f"You're invited to {org_name} on Humanbased",
            "html": html,
        })
        return True
    except Exception:
        logger.exception("Failed to send invite email to %s", email)
        return False


def send_welcome_email(
    email: str, role: str, org_name: str,
) -> bool:
    """Send welcome email after user joins an org."""
    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY not set — skipping welcome to %s", email)
        return False
    try:
        resend.api_key = settings.resend_api_key
        html = render_email(
            heading=f"Welcome to {org_name} on Humanbased",
            body_html=body_text(
                f"You've successfully joined <strong>{org_name}"
                f"</strong> on Humanbased as a <strong>{role}</strong>.",
                "Head to the dashboard to manage API keys, "
                "browse data sources, and start pulling data.",
            ),
            cta_label="Go to dashboard",
            cta_url=f"{settings.webapp_url}/dashboard",
        )
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [email],
            "subject": f"Welcome to {org_name} on Humanbased",
            "html": html,
        })
        return True
    except Exception:
        logger.exception("Failed to send welcome email to %s", email)
        return False


def send_invite_confirmation(
    inviter_email: str,
    invitee_email: str,
    org_name: str,
) -> bool:
    """Notify the inviter that the invitation was sent."""
    if not settings.resend_api_key:
        logger.warning(
            "RESEND_API_KEY not set — skipping invite confirmation to %s",
            inviter_email,
        )
        return False
    try:
        resend.api_key = settings.resend_api_key
        html = render_email(
            heading="Invitation sent",
            body_html=body_text(
                f"Your invitation to <strong>{invitee_email}"
                f"</strong> to join <strong>{org_name}"
                f"</strong> has been sent.",
                "They'll receive an email with instructions "
                "to sign in and join the organization.",
            ),
        )
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [inviter_email],
            "subject": f"Invitation sent to {invitee_email}",
            "html": html,
        })
        return True
    except Exception:
        logger.exception(
            "Failed to send invite confirmation to %s", inviter_email,
        )
        return False


@router.post("/check-emails")
async def check_emails(
    org_id: str,
    body: CheckEmailsRequest,
    member: dict = Depends(require_org_member),
):
    """Check which emails belong to existing platform users."""
    if len(body.emails) > 50:
        raise HTTPException(status_code=400, detail="Max 50 emails per request")
    emails = [str(e).lower() for e in body.emails]
    res = supabase.table("users").select("email").in_("email", emails).execute()
    existing = {r["email"].lower() for r in (res.data or [])}
    return {
        "results": [{"email": e, "exists": e.lower() in existing} for e in emails]
    }


@router.get("")
async def list_members(org_id: str, member: dict = Depends(require_org_member)):
    logger.info("list_members org=%s", org_id)
    res = (
        supabase.table("org_memberships")
        .select(
            "*, users!org_memberships_user_id_fkey"
            "(id, name, email, avatar_url)"
        )
        .eq("org_id", org_id)
        .order("joined_at")
        .execute()
    )
    logger.info(
        "list_members org=%s returned %d members",
        org_id, len(res.data),
    )
    return {"data": res.data}


@router.get("/invitations")
async def list_invitations(org_id: str, member: dict = Depends(require_org_member)):
    logger.info("list_invitations org=%s", org_id)
    res = (
        supabase.table("org_invitations")
        .select("*")
        .eq("org_id", org_id)
        .is_("accepted_at", "null")
        .order("created_at", desc=True)
        .execute()
    )
    logger.info(
        "list_invitations org=%s returned %d pending",
        org_id, len(res.data),
    )
    return {"data": res.data}


@router.post("/invite")
async def invite_member(
    org_id: str, body: InviteMemberRequest, admin: dict = Depends(require_org_admin)
):
    logger.info(
        "invite_member org=%s email=%s role=%s",
        org_id, body.email, body.role,
    )
    if body.role not in ("admin", "member"):
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'member'")

    permissions = (
        body.permissions if body.permissions is not None
        else _default_permissions(body.role)
    )

    org_res = (
        supabase.table("organizations")
        .select("name")
        .eq("id", org_id)
        .single()
        .execute()
    )
    org_name = org_res.data["name"] if org_res.data else "your organization"

    # Get inviter's user id
    inviter_res = (
        supabase.table("users")
        .select("id")
        .eq("auth_id", admin["id"])
        .single()
        .execute()
    )
    inviter_id = inviter_res.data["id"] if inviter_res.data else None

    user_res = (
        supabase.table("users").select("id").eq("email", body.email).execute()
    )

    # Get inviter's email for confirmation
    inviter_email_res = (
        supabase.table("users")
        .select("email")
        .eq("auth_id", admin["id"])
        .single()
        .execute()
    )
    inviter_email = inviter_email_res.data["email"] if inviter_email_res.data else None

    if user_res.data:
        # User exists — check if already a member
        existing_membership = (
            supabase.table("org_memberships")
            .select("id")
            .eq("org_id", org_id)
            .eq("user_id", user_res.data[0]["id"])
            .execute()
        )
        if existing_membership.data:
            raise HTTPException(
                status_code=409,
                detail="User is already a member of this organization",
            )

        # Add membership directly
        res = (
            supabase.table("org_memberships")
            .insert({
                "org_id": org_id,
                "user_id": user_res.data[0]["id"],
                "role": body.role,
                "permissions": permissions,
                "invited_by": inviter_id,
            })
            .execute()
        )
        email_sent = send_invite_email(body.email, body.role, org_name)
        if inviter_email:
            queue_invite_notification(inviter_email, body.email, org_name, "added")
        logger.info(
            "invite_member org=%s email=%s → added (existing user), email_sent=%s",
            org_id, body.email, email_sent,
        )
        return {"data": res.data[0], "status": "added", "email_sent": email_sent}
    else:
        # User doesn't exist — check for existing pending invitation
        existing_inv = (
            supabase.table("org_invitations")
            .select("id")
            .eq("org_id", org_id)
            .eq("email", str(body.email))
            .is_("accepted_at", "null")
            .execute()
        )
        if existing_inv.data:
            raise HTTPException(
                status_code=409,
                detail="A pending invitation already exists for this email",
            )

        # Store pending invitation
        inv_res = (
            supabase.table("org_invitations")
            .insert({
                "org_id": org_id,
                "email": body.email,
                "role": body.role,
                "permissions": permissions,
                "invited_by": inviter_id,
            })
            .execute()
        )
        email_sent = send_invite_email(body.email, body.role, org_name)
        if inviter_email:
            queue_invite_notification(inviter_email, body.email, org_name, "pending_signup")
        logger.info(
            "invite_member org=%s email=%s → pending_signup, email_sent=%s",
            org_id, body.email, email_sent,
        )
        return {
            "data": inv_res.data[0] if inv_res.data else {"email": body.email, "role": body.role},
            "status": "pending_signup",
            "email_sent": email_sent,
        }


@router.delete("/invitations/{invitation_id}")
async def revoke_invitation(
    org_id: str, invitation_id: str, admin: dict = Depends(require_org_admin)
):
    res = (
        supabase.table("org_invitations")
        .delete()
        .eq("id", invitation_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Invitation not found")
    return {"ok": True}


@router.patch("/{member_id}")
async def update_member(
    org_id: str, member_id: str, body: UpdateMemberRequest, admin: dict = Depends(require_org_admin)
):
    # Prevent modifying owner
    existing = (
        supabase.table("org_memberships")
        .select("role")
        .eq("id", member_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not existing.data:
        raise HTTPException(status_code=404, detail="Member not found")
    if existing.data["role"] == "owner":
        raise HTTPException(status_code=403, detail="Cannot modify owner")

    updates = {}
    if body.role is not None:
        if body.role not in ("admin", "member"):
            raise HTTPException(status_code=400, detail="Role must be 'admin' or 'member'")
        updates["role"] = body.role
    if body.permissions is not None:
        invalid = [p for p in body.permissions if p not in ALL_PERMISSIONS]
        if invalid:
            raise HTTPException(status_code=400, detail=f"Invalid permissions: {invalid}")
        updates["permissions"] = body.permissions

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    res = (
        supabase.table("org_memberships")
        .update(updates)
        .eq("id", member_id)
        .eq("org_id", org_id)
        .execute()
    )
    return {"data": res.data[0]}


@router.patch("/{member_id}/role")
async def update_role(
    org_id: str, member_id: str, body: UpdateRoleRequest, admin: dict = Depends(require_org_admin)
):
    res = (
        supabase.table("org_memberships")
        .update({"role": body.role})
        .eq("id", member_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"data": res.data[0]}


@router.delete("/{member_id}")
async def remove_member(org_id: str, member_id: str, admin: dict = Depends(require_org_admin)):
    supabase.table("org_memberships").delete().eq(
        "id", member_id
    ).eq("org_id", org_id).execute()
    return {"ok": True}
