"""Supabase Auth Hook handlers.

Supabase calls these endpoints instead of sending emails itself.
Requires Supabase Pro and the hook configured in:
  Dashboard → Auth → Hooks → Send Email → HTTP
  URL: {API_URL}/v1/auth/hooks/send-email
  Secret: value of SUPABASE_AUTH_HOOK_SECRET
"""

import logging

import resend
from fastapi import APIRouter, BackgroundTasks, Header, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.services.email_renderer import FROM_ADDRESS, body_text, render_email

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# Payload models
# ---------------------------------------------------------------------------

class EmailData(BaseModel):
    token: str = ""
    token_hash: str = ""
    redirect_to: str = ""
    email_action_type: str = ""
    site_url: str = ""
    token_new: str = ""
    token_hash_new: str = ""


class HookUser(BaseModel):
    id: str = ""
    email: str = ""
    user_metadata: dict = {}


class SendEmailPayload(BaseModel):
    user: HookUser
    email_data: EmailData


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _verify_secret(authorization: str | None) -> None:
    """Reject requests that don't carry the correct hook secret."""
    expected = f"Bearer {settings.supabase_auth_hook_secret}"
    if not settings.supabase_auth_hook_secret:
        # Secret not configured — allow through in local dev, warn loudly.
        logger.warning("SUPABASE_AUTH_HOOK_SECRET not set — hook is unprotected")
        return
    if authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid hook secret")


def _verify_url(token_hash: str, action_type: str, redirect_to: str) -> str:
    return (
        f"{settings.supabase_url}/auth/v1/verify"
        f"?token={token_hash}&type={action_type}&redirect_to={redirect_to}"
    )


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

def _dispatch_email(email: str, ed: EmailData) -> None:
    """Route to the correct sender based on action type. Runs in background."""
    action = ed.email_action_type
    resend.api_key = settings.resend_api_key
    try:
        if action == "signup":
            _send_signup_confirmation(email, ed)
        elif action == "recovery":
            _send_password_reset(email, ed)
        elif action in ("magic_link", "magiclink"):
            _send_otp_code(email, ed)
        elif action in ("email_change_new", "email_change_current"):
            _send_email_change(email, ed, action)
        else:
            logger.warning("Unhandled auth hook action type: %s", action)
    except Exception:
        logger.exception(
            "Failed to send auth hook email to %s (action=%s)", email, action
        )
        # Swallow — a send failure shouldn't crash the background task.
        # Monitor Resend dashboard / logs for delivery issues.


@router.post("/send-email", status_code=200)
async def send_email_hook(
    payload: SendEmailPayload,
    background_tasks: BackgroundTasks,
    authorization: str | None = Header(default=None),
) -> dict:
    """Handle all Supabase auth emails via Resend + render_email().

    Supabase enforces a 5-second timeout on auth hooks. The Resend API call
    from Tokyo to the US can take 500-2000ms per request, and Python's sync
    blocking can push total time over the limit under load. We return 200
    immediately and dispatch the email in a background task so the hook never
    blocks on the outbound call.
    """
    _verify_secret(authorization)

    if not settings.resend_api_key:
        logger.warning(
            "RESEND_API_KEY not set — skipping auth hook email to %s (action=%s)",
            payload.user.email, payload.email_data.email_action_type,
        )
        return {}

    background_tasks.add_task(_dispatch_email, payload.user.email, payload.email_data)
    return {}


# ---------------------------------------------------------------------------
# Per-action senders
# ---------------------------------------------------------------------------

def _send_signup_confirmation(email: str, ed: EmailData) -> None:
    """Send signup confirmation as a 6-digit OTP code (not a magic link)."""
    token = ed.token
    if not token:
        logger.error("No OTP token in signup hook payload for %s", email)
        return
    html = render_email(
        heading="Your verification code",
        body_html=(
            "<p style='font-size:15px;color:#37352F;"
            "line-height:1.6;margin:0 0 16px 0;'>"
            "Enter this code to verify your email on Humanbased:</p>"
            "<div style='text-align:center;margin:24px 0;'>"
            "<span style='font-family:monospace;font-size:32px;"
            "font-weight:700;letter-spacing:0.3em;color:#1B1034;"
            f"padding:12px 24px;background:#F0EBFF;'>{token}</span>"
            "</div>"
            "<p style='font-size:14px;color:#9B9A97;"
            "line-height:1.6;margin:0;'>"
            "This code expires in 1 hour. "
            "If you didn't create an account, you can safely ignore this email."
            "</p>"
        ),
    )
    resend.Emails.send({
        "from": FROM_ADDRESS,
        "to": [email],
        "subject": f"{token} is your Humanbased verification code",
        "html": html,
    })


def _send_password_reset(email: str, ed: EmailData) -> None:
    reset_url = _verify_url(ed.token_hash, "recovery", ed.redirect_to or ed.site_url)
    html = render_email(
        heading="Reset your password",
        body_html=body_text(
            "We received a request to reset your Humanbased password. "
            "Click below to choose a new one.",
            "This link expires in 1 hour. If you didn't request a reset, "
            "you can safely ignore this email.",
        ),
        cta_label="Reset password",
        cta_url=reset_url,
    )
    resend.Emails.send({
        "from": FROM_ADDRESS,
        "to": [email],
        "subject": "Reset your Humanbased password",
        "html": html,
    })


def _send_otp_code(email: str, ed: EmailData) -> None:
    """Send a 6-digit OTP verification code via Resend. No magic links."""
    token = ed.token
    if not token:
        logger.error("No OTP token in hook payload for %s", email)
        return
    html = render_email(
        heading="Your verification code",
        body_html=(
            "<p style='font-size:15px;color:#37352F;"
            "line-height:1.6;margin:0 0 16px 0;'>"
            "Enter this code to verify your email on Humanbased:</p>"
            "<div style='text-align:center;margin:24px 0;'>"
            "<span style='font-family:monospace;font-size:32px;"
            "font-weight:700;letter-spacing:0.3em;color:#1B1034;"
            f"padding:12px 24px;background:#F0EBFF;'>{token}</span>"
            "</div>"
            "<p style='font-size:14px;color:#9B9A97;"
            "line-height:1.6;margin:0;'>"
            "This code expires in 10 minutes. "
            "If you didn't request this, you can safely ignore this email."
            "</p>"
        ),
    )
    resend.Emails.send({
        "from": FROM_ADDRESS,
        "to": [email],
        "subject": f"{token} is your Humanbased verification code",
        "html": html,
    })


def _send_email_change(email: str, ed: EmailData, action: str) -> None:
    if action == "email_change_new":
        token_hash = ed.token_hash_new or ed.token_hash
        verify_type = "email_change"
        subject = "Confirm your new email address"
        body = "Click below to confirm this email address as your new Humanbased login."
    else:
        token_hash = ed.token_hash
        verify_type = "email_change"
        subject = "Confirm your email change"
        body = "We received a request to change the email address on your Humanbased account."

    confirm_url = _verify_url(token_hash, verify_type, ed.redirect_to or ed.site_url)
    html = render_email(
        heading=subject,
        body_html=body_text(
            body,
            "If you didn't request this change, contact support immediately.",
        ),
        cta_label="Confirm email",
        cta_url=confirm_url,
    )
    resend.Emails.send({
        "from": FROM_ADDRESS,
        "to": [email],
        "subject": f"Humanbased — {subject}",
        "html": html,
    })
