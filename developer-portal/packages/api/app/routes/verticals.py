from fastapi import APIRouter

from app.db import supabase

router = APIRouter()


@router.get("")
async def list_verticals():
    v_res = (
        supabase.table("verticals")
        .select("id, slug, name, description, base_price_usd")
        .order("name")
        .execute()
    )
    t_res = (
        supabase.table("topics")
        .select("vertical_id")
        .execute()
    )
    topic_counts: dict[str, int] = {}
    for t in (t_res.data or []):
        vid = t["vertical_id"]
        topic_counts[vid] = topic_counts.get(vid, 0) + 1
    for v in (v_res.data or []):
        v["topic_count"] = topic_counts.get(v["id"], 0)
    return {"data": v_res.data}


@router.get("/{vertical_id}/sample-items")
async def sample_items(vertical_id: str, limit: int = 50):
    """Return sample delivery_items payloads for simulator seeding."""
    clamped = min(max(limit, 1), 100)
    res = (
        supabase.table("delivery_items")
        .select(
            "payload, quality_score, quality_method, "
            "validator_count, consensus_ratio, unit_price_usd"
        )
        .eq("vertical_id", vertical_id)
        .order("created_at", desc=True)
        .limit(clamped)
        .execute()
    )
    return {"data": res.data}


@router.get("/{vertical_id}/topics")
async def list_topics(vertical_id: str):
    res = (
        supabase.table("topics")
        .select("id, slug, name, description")
        .eq("vertical_id", vertical_id)
        .order("name")
        .execute()
    )
    return {"data": res.data}
