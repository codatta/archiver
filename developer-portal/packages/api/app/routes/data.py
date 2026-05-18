"""Consumer-facing data API.

These endpoints are authenticated with API keys (hb_live_sk_*),
NOT Supabase JWTs. This is what consumers call from their code/CLI.

Balance lifecycle:
  1. Data received → freeze (available -= price, frozen += price)
  2. Data adopted  → settle (frozen -= price, spent += price)
  3. Dispute valid → refund (frozen -= price, available += price)  [admin]
  4. Dispute rejected → settle (frozen -= price, spent += price)  [admin]
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.apikey_auth import check_subscription_scope, verify_api_key
from app.auth import require_org_member
from app.config import settings
from app.db import supabase

logger = logging.getLogger(__name__)

ENV = settings.stripe_environment

router = APIRouter()
# Dashboard-facing router (JWT auth) for simulator and direct adopt/dispute
dashboard_router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _freeze_on_receive(org_id: str, env: str, price: float, item_id: str) -> bool:
    """Freeze balance when data is received. Returns False if underfunded."""
    acct = (
        supabase.table("accounts")
        .select("id, balance_available_usd, balance_frozen_usd")
        .eq("org_id", org_id)
        .eq("environment", env)
        .execute()
    )
    if not acct.data:
        logger.warning("No account for org %s env %s — cannot freeze", org_id, env)
        return False

    account = acct.data[0]
    available = float(account["balance_available_usd"])
    frozen = float(account["balance_frozen_usd"])

    if available < price:
        logger.warning(
            "Underfunded: org %s needs %.4f, has %.4f — freezing partial",
            org_id, price, available,
        )
        return False

    supabase.table("accounts").update({
        "balance_available_usd": available - price,
        "balance_frozen_usd": frozen + price,
    }).eq("id", account["id"]).execute()

    supabase.table("transactions").insert({
        "account_id": account["id"],
        "type": "freeze",
        "amount_usd": -price,
        "balance_after_usd": available - price,
        "description": f"Data received — item {item_id[:8]}",
        "environment": env,
    }).execute()

    return True


def _settle_on_adopt(org_id: str, env: str, price: float, item_id: str) -> bool:
    """Settle frozen balance when data is adopted. frozen → spent."""
    acct = (
        supabase.table("accounts")
        .select("id, balance_frozen_usd, balance_spent_usd")
        .eq("org_id", org_id)
        .eq("environment", env)
        .execute()
    )
    if not acct.data:
        logger.warning("No account for org %s env %s — cannot settle", org_id, env)
        return False

    account = acct.data[0]
    frozen = float(account["balance_frozen_usd"])
    spent = float(account["balance_spent_usd"])

    supabase.table("accounts").update({
        "balance_frozen_usd": max(frozen - price, 0),
        "balance_spent_usd": spent + price,
    }).eq("id", account["id"]).execute()

    supabase.table("transactions").insert({
        "account_id": account["id"],
        "type": "settle",
        "amount_usd": -price,
        "balance_after_usd": float(
            (supabase.table("accounts")
             .select("balance_available_usd")
             .eq("id", account["id"])
             .execute()).data[0]["balance_available_usd"]
        ),
        "description": f"Data adopted — item {item_id[:8]}",
        "environment": env,
    }).execute()

    return True


# ── Endpoints ─────────────────────────────────────────────────────────────────


@router.post("/auth/verify-key")
async def verify_key(key_info: dict = Depends(verify_api_key)):
    """Verify an API key and return org info."""
    return key_info


@router.get("/data/verticals")
async def list_verticals_public():
    """List available data verticals (no auth required)."""
    res = (
        supabase.table("verticals")
        .select("id, slug, name, description, base_price_usd")
        .order("name")
        .execute()
    )
    return {"data": res.data}


@router.get("/data/pull")
async def pull_data(
    subscription_id: str = Query(...),
    limit: int = Query(default=50, le=200),
    key_info: dict = Depends(verify_api_key),
):
    """Pull pending delivery items for a subscription.

    On receive: freeze balance for each item (available → frozen).
    """
    org_id = key_info["org_id"]

    # Enforce API key subscription scope
    check_subscription_scope(key_info, subscription_id)

    # Verify subscription belongs to the org
    sub_res = (
        supabase.table("subscriptions")
        .select("id, org_id, vertical_id, status")
        .eq("id", subscription_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not sub_res.data:
        raise HTTPException(status_code=404, detail="Subscription not found")
    if sub_res.data["status"] != "active":
        raise HTTPException(
            status_code=400, detail="Subscription is not active"
        )

    # Get new (unfrozen) delivery items for this vertical
    res = (
        supabase.table("delivery_items")
        .select("*")
        .eq("vertical_id", sub_res.data["vertical_id"])
        .eq("status", "pending")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )

    # Freeze balance for each item that hasn't been frozen yet
    for item in res.data:
        price = float(item.get("unit_price_usd") or 0)
        if price <= 0:
            continue
        # Tag the item with org_id/environment if not already set
        updates: dict = {}
        if not item.get("org_id"):
            updates["org_id"] = org_id
        if not item.get("environment"):
            updates["environment"] = ENV

        funded = _freeze_on_receive(org_id, ENV, price, item["id"])
        if not funded:
            updates["underfunded"] = True

        if updates:
            supabase.table("delivery_items").update(
                updates
            ).eq("id", item["id"]).execute()

    return {"data": res.data, "count": len(res.data)}


@router.post("/data/items/{item_id}/adopt")
async def adopt_item(
    item_id: str,
    key_info: dict = Depends(verify_api_key),
):
    """Adopt a delivery item — settle the frozen charge (frozen → spent)."""
    item_res = (
        supabase.table("delivery_items")
        .select("id, delivery_id, unit_price_usd, org_id, status, environment")
        .eq("id", item_id)
        .single()
        .execute()
    )
    if not item_res.data:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_res.data.get("status") == "adopted":
        return {"ok": True, "item_id": item_id, "status": "adopted"}

    if item_res.data.get("status") not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot adopt item with status '{item_res.data['status']}'",
        )

    # Verify org ownership
    org_id = key_info["org_id"]
    item_org = item_res.data.get("org_id")
    if item_org and item_org != org_id:
        raise HTTPException(
            status_code=403, detail="Item does not belong to your org"
        )

    # Settle: frozen → spent
    price = float(item_res.data.get("unit_price_usd") or 0)
    settled = False
    if price > 0:
        env = item_res.data.get("environment") or ENV
        settled = _settle_on_adopt(org_id, env, price, item_id)

    # Update item status
    supabase.table("delivery_items").update(
        {"status": "adopted", "reviewed_at": "now()"}
    ).eq("id", item_id).execute()

    if item_res.data.get("delivery_id"):
        supabase.table("deliveries").update(
            {"status": "accepted"}
        ).eq("id", item_res.data["delivery_id"]).execute()

    return {
        "ok": True, "item_id": item_id, "status": "adopted",
        "settled_usd": price if settled else 0,
    }


@router.post("/data/items/{item_id}/dispute")
async def dispute_item(
    item_id: str,
    key_info: dict = Depends(verify_api_key),
):
    """Mark a delivery item as disputed. Balance stays frozen until admin resolves."""
    item_res = (
        supabase.table("delivery_items")
        .select("id, delivery_id, status, org_id")
        .eq("id", item_id)
        .single()
        .execute()
    )
    if not item_res.data:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_res.data.get("status") not in ("pending",):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot dispute item with status '{item_res.data['status']}'",
        )

    # Verify org ownership
    org_id = key_info["org_id"]
    item_org = item_res.data.get("org_id")
    if item_org and item_org != org_id:
        raise HTTPException(
            status_code=403, detail="Item does not belong to your org"
        )

    # Update item status — balance stays frozen, no refund yet
    supabase.table("delivery_items").update(
        {"status": "disputed", "reviewed_at": "now()"}
    ).eq("id", item_id).execute()

    if item_res.data.get("delivery_id"):
        supabase.table("deliveries").update(
            {"status": "rejected"}
        ).eq("id", item_res.data["delivery_id"]).execute()

    return {"ok": True, "item_id": item_id, "status": "disputed"}


@router.get("/data/deliveries")
async def list_deliveries(
    limit: int = Query(default=50, le=200),
    key_info: dict = Depends(verify_api_key),
):
    """List deliveries for the org."""
    subs_res = (
        supabase.table("subscriptions")
        .select("id")
        .eq("org_id", key_info["org_id"])
        .execute()
    )
    if not subs_res.data:
        return {"data": []}

    sub_ids = [s["id"] for s in subs_res.data]

    res = (
        supabase.table("deliveries")
        .select("*")
        .in_("subscription_id", sub_ids)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return {"data": res.data}


@router.get("/data/deliveries/{delivery_id}/items")
async def delivery_items(
    delivery_id: str,
    key_info: dict = Depends(verify_api_key),
):
    """Get items in a specific delivery."""
    res = (
        supabase.table("delivery_items")
        .select("*")
        .eq("delivery_id", delivery_id)
        .order("created_at", desc=True)
        .execute()
    )
    return {"data": res.data}


# ── Dashboard endpoints (JWT auth) ───────────────────────────────────────────


class SimulateReceiveRequest(BaseModel):
    vertical_id: str
    payload: dict
    quality_score: float
    quality_method: str
    validator_count: int = 1
    consensus_ratio: float = 1.0
    unit_price_usd: float
    vertical_slug: Optional[str] = None


@dashboard_router.post("/simulate-receive")
async def simulate_receive(
    org_id: str,
    body: SimulateReceiveRequest,
    member: dict = Depends(require_org_member),
):
    """Insert a simulated delivery_item into DB and freeze balance.

    Used by the dashboard simulator to create real test-mode records.
    """
    # Insert the delivery item
    item_data = {
        "vertical_id": body.vertical_id,
        "payload": body.payload,
        "quality_score": body.quality_score,
        "quality_method": body.quality_method,
        "validator_count": body.validator_count,
        "consensus_ratio": body.consensus_ratio,
        "unit_price_usd": body.unit_price_usd,
        "org_id": org_id,
        "environment": "test",
        "status": "pending",
    }
    res = (
        supabase.table("delivery_items")
        .insert(item_data)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=500, detail="Failed to create item")

    item = res.data[0]

    # Freeze balance
    price = float(body.unit_price_usd)
    underfunded = False
    if price > 0:
        funded = _freeze_on_receive(org_id, "test", price, item["id"])
        if not funded:
            underfunded = True
            supabase.table("delivery_items").update(
                {"underfunded": True}
            ).eq("id", item["id"]).execute()
            item["underfunded"] = True

    return {"data": item, "underfunded": underfunded}


@dashboard_router.post("/items/{item_id}/adopt")
async def dashboard_adopt_item(
    org_id: str,
    item_id: str,
    member: dict = Depends(require_org_member),
):
    """Adopt a delivery item from the dashboard (JWT auth). Settle frozen → spent."""
    item_res = (
        supabase.table("delivery_items")
        .select("id, delivery_id, unit_price_usd, org_id, status, environment")
        .eq("id", item_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not item_res.data:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_res.data.get("status") == "adopted":
        return {"ok": True, "item_id": item_id, "status": "adopted"}

    if item_res.data.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot adopt item with status '{item_res.data['status']}'",
        )

    price = float(item_res.data.get("unit_price_usd") or 0)
    settled = False
    if price > 0:
        env = item_res.data.get("environment") or "test"
        settled = _settle_on_adopt(org_id, env, price, item_id)

    supabase.table("delivery_items").update(
        {"status": "adopted", "reviewed_at": "now()"}
    ).eq("id", item_id).execute()

    return {
        "ok": True, "item_id": item_id, "status": "adopted",
        "settled_usd": price if settled else 0,
    }


@dashboard_router.post("/items/{item_id}/dispute")
async def dashboard_dispute_item(
    org_id: str,
    item_id: str,
    member: dict = Depends(require_org_member),
):
    """Dispute a delivery item from the dashboard (JWT auth). Balance stays frozen."""
    item_res = (
        supabase.table("delivery_items")
        .select("id, delivery_id, status, org_id")
        .eq("id", item_id)
        .eq("org_id", org_id)
        .single()
        .execute()
    )
    if not item_res.data:
        raise HTTPException(status_code=404, detail="Item not found")

    if item_res.data.get("status") != "pending":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot dispute item with status '{item_res.data['status']}'",
        )

    supabase.table("delivery_items").update(
        {"status": "disputed", "reviewed_at": "now()"}
    ).eq("id", item_id).execute()

    return {"ok": True, "item_id": item_id, "status": "disputed"}
