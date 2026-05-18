import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from app.auth import require_org_member
from app.config import settings
from app.db import supabase

logger = logging.getLogger(__name__)

router = APIRouter()
webhook_router = APIRouter()
mode_router = APIRouter()

stripe.api_key = settings.stripe_secret_key

ENV = settings.stripe_environment


# ── Helpers ────────────────────────────────────────────────────────────────────


def _get_or_create_account(org_id: str, environment: str) -> dict:
    """Return the account row for (org_id, environment), creating if missing."""
    res = (
        supabase.table("accounts")
        .select("*")
        .eq("org_id", org_id)
        .eq("environment", environment)
        .execute()
    )
    if res.data:
        return res.data[0]

    new = (
        supabase.table("accounts")
        .insert({
            "org_id": org_id,
            "environment": environment,
            "balance_available_usd": 10_000_000,
            "balance_frozen_usd": 0,
            "balance_spent_usd": 0,
            "balance_earnings_usd": 0,
        })
        .execute()
    )
    if not new.data:
        raise HTTPException(status_code=500, detail="Failed to create account")
    return new.data[0]


def _credit_session(
    org_id: str, env: str, amount: float, session_id: str
) -> bool:
    """Credit a Stripe session to the org's account. Returns False if already processed."""
    existing = (
        supabase.table("transactions")
        .select("id")
        .eq("reference_id", session_id)
        .execute()
    )
    if existing.data:
        return False

    account = _get_or_create_account(org_id, env)
    new_balance = float(account["balance_available_usd"]) + amount

    supabase.table("accounts").update({
        "balance_available_usd": new_balance,
    }).eq("id", account["id"]).execute()

    supabase.table("transactions").insert({
        "account_id": account["id"],
        "type": "topup",
        "amount_usd": amount,
        "balance_after_usd": new_balance,
        "reference_id": session_id,
        "description": f"Stripe top-up ${amount:.2f}",
        "environment": env,
    }).execute()

    logger.info(
        "Credited $%.2f to org %s (%s), new balance $%.2f",
        amount, org_id, env, new_balance,
    )
    return True


# ── Endpoints ──────────────────────────────────────────────────────────────────


class AddFundsRequest(BaseModel):
    amount_cents: int


class VerifySessionRequest(BaseModel):
    session_id: str


@router.get("/balance")
async def get_balance(org_id: str, member: dict = Depends(require_org_member)):
    account = _get_or_create_account(org_id, ENV)
    return {"data": account}


@router.post("/checkout")
async def create_checkout(
    org_id: str, body: AddFundsRequest, member: dict = Depends(require_org_member)
):
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "unit_amount": body.amount_cents,
                    "product_data": {"name": "Humanbased Balance Top-up"},
                },
                "quantity": 1,
            }],
            metadata={"org_id": org_id, "environment": ENV},
            success_url=(
                f"{settings.webapp_url}/dashboard/billing"
                "?status=success&session_id={CHECKOUT_SESSION_ID}"
            ),
            cancel_url=f"{settings.webapp_url}/dashboard/billing?status=cancelled",
        )
        return {"data": {"checkout_url": session.url}}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/checkout/{session_id}")
async def get_checkout_session(
    org_id: str,
    session_id: str,
    member: dict = Depends(require_org_member),
):
    """Return the payment amount for a completed Stripe checkout session."""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.metadata.get("org_id") != org_id:
        raise HTTPException(
            status_code=403, detail="Session does not belong to this org"
        )

    return {
        "data": {
            "session_id": session.id,
            "amount_usd": (session.amount_total or 0) / 100,
            "status": session.payment_status,
        }
    }


@router.post("/verify-session")
async def verify_session(
    org_id: str,
    body: VerifySessionRequest,
    member: dict = Depends(require_org_member),
):
    """Fallback for when the Stripe webhook hasn't fired.

    Retrieves the session from Stripe, verifies payment, and credits
    the account if not already processed.
    """
    try:
        session = stripe.checkout.Session.retrieve(body.session_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.metadata.get("org_id") != org_id:
        raise HTTPException(
            status_code=403, detail="Session does not belong to this org"
        )

    if session.payment_status != "paid":
        return {
            "credited": False,
            "reason": f"Payment status is '{session.payment_status}', not 'paid'",
        }

    amount = (session.amount_total or 0) / 100
    env = session.metadata.get("environment", "test")
    credited = _credit_session(org_id, env, amount, session.id)

    return {"credited": credited, "amount_usd": amount, "environment": env}


# ── Webhook ────────────────────────────────────────────────────────────────────


@webhook_router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(
            payload, sig, settings.stripe_webhook_secret
        )
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        org_id = session["metadata"]["org_id"]
        env = session["metadata"].get("environment", "test")
        amount = session["amount_total"] / 100
        session_id = session["id"]

        logger.info(
            "Webhook: checkout.session.completed org=%s env=%s amount=%.2f",
            org_id, env, amount,
        )

        credited = _credit_session(org_id, env, amount, session_id)
        if not credited:
            logger.info("Webhook: session %s already processed", session_id)

    return {"ok": True}


# ── Transactions ───────────────────────────────────────────────────────────────


@router.get("/transactions")
async def list_transactions(
    org_id: str, member: dict = Depends(require_org_member)
):
    account = _get_or_create_account(org_id, ENV)
    res = (
        supabase.table("transactions")
        .select("*")
        .eq("account_id", account["id"])
        .eq("environment", ENV)
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return {"data": res.data}


# ── Mode ───────────────────────────────────────────────────────────────────────


@mode_router.get("/mode")
async def get_billing_mode():
    """Return the current billing environment (test or live)."""
    return {"environment": ENV}
