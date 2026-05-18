"""Price resolver — looks up per-record pricing from pricing_schedule table.

Pricing cascades with fallback:
  1. frontier_id + task_id + quality_tier → exact match
  2. frontier_id + task_id → any quality tier
  3. frontier_id → any task/tier
  4. System default → $0.00 (free tier)

Prices are cached in memory and refreshed every 5 minutes.
"""
import logging
import time
from decimal import Decimal

from app.db import supabase

logger = logging.getLogger(__name__)

_cache: list[dict] = []
_cache_ts: float = 0
CACHE_TTL = 300  # 5 minutes

DEFAULT_PRICE = Decimal("0.00")


def _refresh_cache() -> None:
    global _cache, _cache_ts
    now = time.monotonic()
    if _cache and (now - _cache_ts) < CACHE_TTL:
        return
    try:
        res = (
            supabase.table("pricing_schedule")
            .select(
                "frontier_id, task_id, quality_tier, "
                "unit_price_usd, effective_from, effective_until"
            )
            .order("effective_from", desc=True)
            .execute()
        )
        _cache = res.data or []
        _cache_ts = now
        logger.info("Pricing cache refreshed: %d schedules loaded", len(_cache))
    except Exception as e:
        logger.warning("Failed to refresh pricing cache: %s", e)
        # Keep stale cache if refresh fails


def resolve_price(
    frontier_id: str,
    task_id: str | None = None,
    quality_tier: str | None = None,
) -> Decimal:
    """Resolve the unit price for a data record.

    Returns the price in USD as a Decimal. Falls back through
    progressively broader matches until a price is found.
    """
    _refresh_cache()

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()

    best_price: Decimal | None = None
    best_specificity = -1  # higher = more specific match

    for schedule in _cache:
        # Check time validity
        if schedule.get("effective_from") and schedule["effective_from"] > now:
            continue
        if schedule.get("effective_until") and schedule["effective_until"] < now:
            continue

        # Check frontier match
        if schedule["frontier_id"] != frontier_id:
            continue

        # Score specificity
        specificity = 1  # frontier matches
        task_match = schedule.get("task_id") is None or schedule["task_id"] == task_id
        tier_match = (
            schedule.get("quality_tier") is None
            or schedule["quality_tier"] == quality_tier
        )

        if not task_match or not tier_match:
            # If schedule specifies a task/tier that doesn't match, skip
            if schedule.get("task_id") and schedule["task_id"] != task_id:
                continue
            if schedule.get("quality_tier") and schedule["quality_tier"] != quality_tier:
                continue

        if schedule.get("task_id") == task_id and task_id is not None:
            specificity += 2
        if schedule.get("quality_tier") == quality_tier and quality_tier is not None:
            specificity += 1

        if specificity > best_specificity:
            best_specificity = specificity
            best_price = Decimal(str(schedule["unit_price_usd"]))

    return best_price if best_price is not None else DEFAULT_PRICE
