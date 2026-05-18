import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import require_org_member
from app.db import supabase

logger = logging.getLogger(__name__)
router = APIRouter()

KEY_PREFIX = "hb_live_sk_"


def generate_api_key() -> str:
    return KEY_PREFIX + secrets.token_urlsafe(32)


def hash_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()


def mask_key(key: str) -> str:
    return key[:14] + "\u2022" * 8


class CreateKeyRequest(BaseModel):
    name: str
    expires_in_days: int | None = 90
    subscription_ids: list[str]  # Required — at least one subscription
    daily_limit_usd: float | None = None  # None = no limit


@router.post("")
async def create_key(
    org_id: str, body: CreateKeyRequest, member: dict = Depends(require_org_member)
):
    logger.info("create_key org=%s name=%s expires=%s", org_id, body.name, body.expires_in_days)

    if not body.subscription_ids:
        raise HTTPException(
            status_code=422,
            detail="At least one subscription must be selected",
        )

    # Prevent duplicate key names within the same org
    existing_name = (
        supabase.table("api_keys")
        .select("id")
        .eq("org_id", org_id)
        .eq("name", body.name)
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if existing_name.data:
        raise HTTPException(
            status_code=409,
            detail="An active API key with this name already exists",
        )

    # Validate that all subscription_ids belong to this org and are active
    org_subs_res = (
        supabase.table("subscriptions")
        .select("id")
        .eq("org_id", org_id)
        .eq("status", "active")
        .execute()
    )
    valid_ids = {s["id"] for s in org_subs_res.data}
    invalid = [sid for sid in body.subscription_ids if sid not in valid_ids]
    if invalid:
        raise HTTPException(
            status_code=403,
            detail=f"Invalid or inactive subscription IDs: {', '.join(invalid)}",
        )

    raw_key = generate_api_key()
    key_hash = hash_key(raw_key)
    expires_at = None
    if body.expires_in_days:
        expires_at = (
            datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)
        ).isoformat()

    row: dict = {
        "org_id": org_id,
        "name": body.name,
        "key_hash": key_hash,
        "key_prefix": raw_key[:20],
        "status": "active",
        "expires_at": expires_at,
        "created_by": member["id"],
        "subscription_ids": body.subscription_ids,
    }
    if body.daily_limit_usd is not None:
        row["daily_limit_usd"] = body.daily_limit_usd

    res = supabase.table("api_keys").insert(row).execute()
    logger.info("create_key org=%s key_id=%s", org_id, res.data[0]["id"])
    return {"data": {**res.data[0], "raw_key": raw_key}}


@router.get("")
async def list_keys(org_id: str, member: dict = Depends(require_org_member)):
    logger.info("list_keys org=%s", org_id)
    res = (
        supabase.table("api_keys")
        .select(
            "id, name, key_prefix, status, expires_at, last_used_at, "
            "created_at, subscription_ids, daily_limit_usd, created_by"
        )
        .eq("org_id", org_id)
        .order("created_at", desc=True)
        .execute()
    )
    keys = res.data

    # Fetch creator names for keys that have created_by set
    creator_ids = list({k["created_by"] for k in keys if k.get("created_by")})
    creator_map: dict[str, str] = {}
    if creator_ids:
        users_res = (
            supabase.table("users")
            .select("auth_id, name, email")
            .in_("auth_id", creator_ids)
            .execute()
        )
        for u in users_res.data:
            creator_map[u["auth_id"]] = u["name"] or u["email"] or "Unknown"

    for k in keys:
        k["created_by_name"] = creator_map.get(k.get("created_by"), None)

    return {"data": keys}


@router.post("/{key_id}/revoke")
async def revoke_key(org_id: str, key_id: str, member: dict = Depends(require_org_member)):
    logger.info("revoke_key org=%s key_id=%s", org_id, key_id)
    res = (
        supabase.table("api_keys")
        .update({"status": "revoked"})
        .eq("id", key_id)
        .eq("org_id", org_id)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=404, detail="Key not found")
    return {"data": res.data[0]}
