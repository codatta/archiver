"""Batched invite notification emails.

Instead of sending individual confirmation emails to the inviter for each
invite, we buffer invites per inviter and flush a single summary email
after 5 minutes of inactivity.

Individual invitee emails are still sent immediately (unchanged).
"""
import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timezone

import resend

from app.config import settings
from app.services.email_renderer import FROM_ADDRESS, body_text, render_email

logger = logging.getLogger(__name__)

DEBOUNCE_SECONDS = 300  # 5 minutes

_pending: dict[str, list[dict]] = defaultdict(list)
_timers: dict[str, asyncio.TimerHandle] = {}


def queue_invite_notification(
    inviter_email: str,
    invitee_email: str,
    org_name: str,
    status: str,
) -> None:
    """Queue an invite notification for batched delivery to the inviter.

    Args:
        inviter_email: The person who sent the invite.
        invitee_email: The person being invited.
        org_name: Organization name for the email body.
        status: "added" (existing user joined) or "pending_signup" (invite sent).
    """
    _pending[inviter_email].append({
        "invitee_email": invitee_email,
        "org_name": org_name,
        "status": status,
        "queued_at": datetime.now(timezone.utc).isoformat(),
    })

    # Reset the debounce timer
    if inviter_email in _timers:
        _timers[inviter_email].cancel()

    try:
        loop = asyncio.get_running_loop()
        _timers[inviter_email] = loop.call_later(
            DEBOUNCE_SECONDS,
            lambda email=inviter_email: asyncio.ensure_future(_flush(email)),
        )
    except RuntimeError:
        # No running loop (e.g., tests) — flush immediately
        _flush_sync(inviter_email)


async def _flush(inviter_email: str) -> None:
    """Send the batched summary email and clear the buffer."""
    invites = _pending.pop(inviter_email, [])
    _timers.pop(inviter_email, None)
    if not invites:
        return
    _send_batch_summary(inviter_email, invites)


def _flush_sync(inviter_email: str) -> None:
    """Synchronous flush for contexts without an event loop."""
    invites = _pending.pop(inviter_email, [])
    _timers.pop(inviter_email, None)
    if not invites:
        return
    _send_batch_summary(inviter_email, invites)


def _send_batch_summary(
    inviter_email: str, invites: list[dict],
) -> None:
    """Compose and send a single summary email."""
    if not settings.resend_api_key:
        logger.warning(
            "RESEND_API_KEY not set — skipping summary to %s",
            inviter_email,
        )
        return

    org_name = (
        invites[0]["org_name"] if invites else "your organization"
    )
    added = [i for i in invites if i["status"] == "added"]
    pending = [i for i in invites if i["status"] != "added"]

    rows = ""
    for inv in invites:
        label = "Joined" if inv["status"] == "added" else "Sent"
        color = "#16a34a" if inv["status"] == "added" else "#9B9A97"
        rows += (
            "<tr>"
            "<td style='padding:6px 16px 6px 0;"
            f"font-size:14px;color:#37352F;'>"
            f"{inv['invitee_email']}</td>"
            f"<td style='padding:6px 0;font-size:13px;"
            f"color:{color};'>{label}</td>"
            "</tr>"
        )

    parts = []
    if added:
        parts.append(
            f"{len(added)} existing user(s) added directly",
        )
    if pending:
        parts.append(f"{len(pending)} new user(s) invited")
    summary = " and ".join(parts)

    inner = body_text(
        f"Here's a summary of your recent invitations "
        f"to <strong>{org_name}</strong> on Humanbased.",
        f"{summary}.",
    )
    inner += (
        "<table style='border-collapse:collapse;"
        f"margin-top:16px;width:100%;'>{rows}</table>"
    )

    html = render_email(
        heading="Invitation summary",
        body_html=inner,
        cta_label="View team",
        cta_url=f"{settings.webapp_url}/dashboard/members",
    )

    try:
        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": FROM_ADDRESS,
            "to": [inviter_email],
            "subject": f"Invitation summary for {org_name}",
            "html": html,
        })
        logger.info(
            "Sent batch summary to %s (%d invites)",
            inviter_email, len(invites),
        )
    except Exception:
        logger.exception(
            "Failed to send batch summary to %s",
            inviter_email,
        )
