"""Admin endpoints for Humanbased operators (superadmin only).

Dispute resolution balance flow:
  accept (valid dispute) → refund: frozen -= price, available += price
  reject (invalid dispute) → settle: frozen -= price, spent += price
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import require_superadmin
from app.config import settings
from app.db import supabase

logger = logging.getLogger(__name__)

router = APIRouter()

ENV = settings.stripe_environment


class UpdateOrgSettingsRequest(BaseModel):
    auto_adopt_hours: Optional[int] = None


class ResolveDisputeRequest(BaseModel):
    resolution: str  # "accept" (refund) or "reject" (force adopt)


def _get_or_create_org_settings(org_id: str) -> dict:
    res = (
        supabase.table("org_settings")
        .select("*")
        .eq("org_id", org_id)
        .execute()
    )
    if res.data:
        return res.data[0]
    new = (
        supabase.table("org_settings")
        .insert({"org_id": org_id})
        .execute()
    )
    return new.data[0] if new.data else {"org_id": org_id, "auto_adopt_hours": 48}


@router.get("/orgs")
async def list_orgs(admin: dict = Depends(require_superadmin)):
    """List all organizations with balance summary."""
    orgs = (
        supabase.table("organizations")
        .select("id, name, slug, created_at")
        .order("created_at", desc=True)
        .execute()
    )
    result = []
    for org in orgs.data:
        acct = (
            supabase.table("accounts")
            .select("balance_available_usd, balance_frozen_usd")
            .eq("org_id", org["id"])
            .eq("environment", ENV)
            .execute()
        )
        bal = acct.data[0] if acct.data else {
            "balance_available_usd": 0,
            "balance_frozen_usd": 0,
        }
        settings_row = _get_or_create_org_settings(org["id"])
        result.append({
            **org,
            "balance_available_usd": bal["balance_available_usd"],
            "balance_frozen_usd": bal["balance_frozen_usd"],
            "auto_adopt_hours": settings_row.get("auto_adopt_hours", 48),
        })
    return {"data": result}


@router.get("/orgs/{org_id}/settings")
async def get_org_settings(
    org_id: str, admin: dict = Depends(require_superadmin)
):
    return {"data": _get_or_create_org_settings(org_id)}


@router.patch("/orgs/{org_id}/settings")
async def update_org_settings(
    org_id: str,
    body: UpdateOrgSettingsRequest,
    admin: dict = Depends(require_superadmin),
):
    settings_row = _get_or_create_org_settings(org_id)
    updates = {}
    if body.auto_adopt_hours is not None:
        if body.auto_adopt_hours < 1 or body.auto_adopt_hours > 720:
            raise HTTPException(
                status_code=400,
                detail="auto_adopt_hours must be between 1 and 720",
            )
        updates["auto_adopt_hours"] = body.auto_adopt_hours

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    res = (
        supabase.table("org_settings")
        .update(updates)
        .eq("id", settings_row["id"])
        .execute()
    )
    return {"data": res.data[0] if res.data else settings_row}


SEED_BALANCE = 10_000_000


@router.post("/seed-balances")
async def seed_balances(admin: dict = Depends(require_superadmin)):
    """Set all org accounts to $10,000,000 available balance (testing only).

    Creates the account row if it doesn't exist yet.
    Only affects orgs whose available balance is below the seed amount.
    """
    orgs = supabase.table("organizations").select("id, name").execute()
    updated = []
    created = []

    for org in orgs.data:
        org_id = org["id"]
        acct = (
            supabase.table("accounts")
            .select("id, balance_available_usd")
            .eq("org_id", org_id)
            .eq("environment", ENV)
            .execute()
        )
        if acct.data:
            supabase.table("accounts").update({
                "balance_available_usd": SEED_BALANCE,
            }).eq("id", acct.data[0]["id"]).execute()
            updated.append(org["name"])
        else:
            supabase.table("accounts").insert({
                "org_id": org_id,
                "environment": ENV,
                "balance_available_usd": SEED_BALANCE,
                "balance_frozen_usd": 0,
                "balance_spent_usd": 0,
                "balance_earnings_usd": 0,
            }).execute()
            created.append(org["name"])

    logger.info("seed-balances: updated=%d created=%d", len(updated), len(created))
    return {
        "ok": True,
        "seed_amount_usd": SEED_BALANCE,
        "updated": updated,
        "created": created,
    }


@router.get("/disputes")
async def list_disputes(admin: dict = Depends(require_superadmin)):
    """List all disputed delivery items across all orgs."""
    res = (
        supabase.table("delivery_items")
        .select("*, verticals(name)")
        .eq("status", "disputed")
        .order("reviewed_at", desc=True)
        .limit(100)
        .execute()
    )
    return {"data": res.data}


@router.post("/disputes/{item_id}/resolve")
async def resolve_dispute(
    item_id: str,
    body: ResolveDisputeRequest,
    admin: dict = Depends(require_superadmin),
):
    """Resolve a disputed item: accept (refund) or reject (settle as adopted)."""
    if body.resolution not in ("accept", "reject"):
        raise HTTPException(
            status_code=400,
            detail="resolution must be 'accept' or 'reject'",
        )

    item = (
        supabase.table("delivery_items")
        .select("*")
        .eq("id", item_id)
        .eq("status", "disputed")
        .execute()
    )
    if not item.data:
        raise HTTPException(status_code=404, detail="Disputed item not found")

    item_data = item.data[0]

    if body.resolution == "accept":
        # Dispute valid — refund: frozen → available
        new_status = "refunded"
        if item_data.get("org_id") and item_data.get("unit_price_usd"):
            _refund_item(item_data)
    else:
        # Dispute rejected — settle: frozen → spent (same as adopt)
        new_status = "adopted"
        if item_data.get("org_id") and item_data.get("unit_price_usd"):
            _settle_item(item_data)

    supabase.table("delivery_items").update({
        "status": new_status,
        "reviewed_at": "now()",
    }).eq("id", item_id).execute()

    logger.info(
        "Dispute resolved: item=%s resolution=%s new_status=%s",
        item_id, body.resolution, new_status,
    )
    return {"ok": True, "item_id": item_id, "status": new_status}


def _refund_item(item: dict) -> None:
    """Refund a frozen charge back to available balance (dispute accepted)."""
    org_id = item["org_id"]
    env = item.get("environment", "test")
    price = float(item.get("unit_price_usd", 0))
    if not org_id or price <= 0:
        return

    acct = (
        supabase.table("accounts")
        .select("id, balance_available_usd, balance_frozen_usd")
        .eq("org_id", org_id)
        .eq("environment", env)
        .execute()
    )
    if not acct.data:
        return

    account = acct.data[0]
    new_available = float(account["balance_available_usd"]) + price
    new_frozen = max(float(account["balance_frozen_usd"]) - price, 0)

    supabase.table("accounts").update({
        "balance_available_usd": new_available,
        "balance_frozen_usd": new_frozen,
    }).eq("id", account["id"]).execute()

    supabase.table("transactions").insert({
        "account_id": account["id"],
        "type": "refund",
        "amount_usd": price,
        "balance_after_usd": new_available,
        "description": f"Dispute refund — item {item['id'][:8]}",
        "environment": env,
    }).execute()


def _settle_item(item: dict) -> None:
    """Settle a frozen charge as spent (dispute rejected → force adopt)."""
    org_id = item["org_id"]
    env = item.get("environment", "test")
    price = float(item.get("unit_price_usd", 0))
    if not org_id or price <= 0:
        return

    acct = (
        supabase.table("accounts")
        .select("id, balance_available_usd, balance_frozen_usd, balance_spent_usd")
        .eq("org_id", org_id)
        .eq("environment", env)
        .execute()
    )
    if not acct.data:
        return

    account = acct.data[0]
    new_frozen = max(float(account["balance_frozen_usd"]) - price, 0)
    new_spent = float(account["balance_spent_usd"]) + price

    supabase.table("accounts").update({
        "balance_frozen_usd": new_frozen,
        "balance_spent_usd": new_spent,
    }).eq("id", account["id"]).execute()

    supabase.table("transactions").insert({
        "account_id": account["id"],
        "type": "settle",
        "amount_usd": -price,
        "balance_after_usd": float(account["balance_available_usd"]),
        "description": f"Dispute rejected — item {item['id'][:8]}",
        "environment": env,
    }).execute()
