"""API key authentication for consumer-facing endpoints.

Consumer requests use `Authorization: Bearer hb_live_sk_*` keys.
This is separate from Supabase JWT auth used by the dashboard.
"""
import hashlib
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request

from app.db import supabase

KEY_PREFIX = "hb_live_sk_"


def check_subscription_scope(key_info: dict, subscription_id: str) -> None:
    """Raise 403 if the API key is scoped and the subscription is not in scope."""
    scoped_ids = key_info.get("subscription_ids")
    if scoped_ids is not None and subscription_id not in scoped_ids:
        raise HTTPException(
            status_code=403,
            detail="API key does not have access to this subscription",
        )


def get_api_key(request: Request) -> str:
    """Extract and validate the API key from the Authorization header."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing API key")
    key = auth[7:]
    if not key.startswith(KEY_PREFIX):
        raise HTTPException(status_code=401, detail="Invalid API key format")
    return key


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(key: str = Depends(get_api_key)) -> dict:
    """Verify the API key against the database.

    Returns dict with org_id, key_id, key_name on success.
    Raises 401 on invalid/expired/revoked key.
    """
    key_hash = hash_key(key)

    try:
        res = (
            supabase.table("api_keys")
            .select("id, org_id, name, status, expires_at, subscription_ids")
            .eq("key_hash", key_hash)
            .single()
            .execute()
        )
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid API key")

    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid API key")

    record = res.data

    if record["status"] != "active":
        raise HTTPException(
            status_code=401, detail=f"API key is {record['status']}"
        )

    if record.get("expires_at"):
        expires = datetime.fromisoformat(
            record["expires_at"].replace("Z", "+00:00")
        )
        if expires < datetime.now(timezone.utc):
            raise HTTPException(status_code=401, detail="API key has expired")

    # Update last_used_at (fire-and-forget, don't block)
    try:
        supabase.table("api_keys").update(
            {"last_used_at": datetime.now(timezone.utc).isoformat()}
        ).eq("id", record["id"]).execute()
    except Exception:
        pass

    return {
        "key_id": record["id"],
        "org_id": record["org_id"],
        "key_name": record["name"],
        "subscription_ids": record.get("subscription_ids"),
    }
