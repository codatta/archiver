"""Public sandbox endpoint — no auth required.

Returns mock items for a given vertical slug so the dashboard and
API consumers get data from the same simulator source.
"""

import random
import uuid
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import APIRouter, Query

router = APIRouter()

# ── Mock payload generators (mirrors frontend generators) ─────────

_CHAINS = [
    "ethereum", "base", "polygon", "arbitrum",
    "bsc", "optimism", "solana",
]
_CATEGORIES = [
    "dex", "cex", "staking", "bridge", "mixer",
    "scam", "mev_bot", "vault", "lending", "nft", "cold_storage",
]
_ENTITIES = [
    "Uniswap", "Coinbase", "Lido", "Stargate",
    "Unknown", "Binance", "Aave", "Curve",
]
_SOURCES = ["ground_truth", "machine_learning", "research", "heuristic"]


def _mock_crypto() -> dict:
    chain = random.choice(_CHAINS)
    cat = random.choice(_CATEGORIES)
    ent = random.choice(_ENTITIES)
    addr = "0x" + "".join(random.choices("0123456789abcdef", k=40))
    return {
        "address": addr,
        "chain": chain,
        "category": cat,
        "entity": f"{ent}_{cat}".lower().replace(" ", "_"),
        "source": random.choice(_SOURCES),
        "description": f"{ent} {cat} contract on {chain}",
    }


_FASHION_BRANDS = [
    "Nike", "Adidas", "Patagonia", "Zara",
    "Levi's", "Arc'teryx", "Louis Vuitton", "H&M",
]
_FASHION_CATS = [
    "sneakers", "jacket", "jeans", "dress", "bag",
    "coat", "t_shirt", "boots", "activewear",
]
_MATERIALS = [
    "cotton", "polyester", "leather", "nylon",
    "recycled_polyester", "denim", "wool", "silk",
]
_TIERS = ["budget", "mid_range", "premium", "luxury", "ultra_luxury"]
_SUSTAIN = ["A", "B", "C", "D"]


def _mock_fashion() -> dict:
    brand = random.choice(_FASHION_BRANDS)
    cat = random.choice(_FASHION_CATS)
    return {
        "brand": brand,
        "product_name": f"{brand} {cat.replace('_', ' ')}",
        "category": cat,
        "material": random.choice(_MATERIALS),
        "price_tier": random.choice(_TIERS),
        "sustainability_tier": random.choice(_SUSTAIN),
        "condition": "new",
    }


_FOOD_BRANDS = [
    "Oatly", "Chobani", "KIND", "Nestle",
    "Bob's Red Mill", "Organic Valley", "Kellogg's",
]
_FOOD_CATS = [
    "dairy", "snacks", "beverages", "pasta_grains",
    "fresh_produce", "bakery", "sweets", "health_food",
]
_NUTRISCORES = ["A", "B", "C", "D", "E"]


def _mock_food() -> dict:
    brand = random.choice(_FOOD_BRANDS)
    cat = random.choice(_FOOD_CATS)
    return {
        "brand": brand,
        "product_name": f"{brand} {cat.replace('_', ' ')}",
        "category": cat,
        "nutriscore": random.choice(_NUTRISCORES),
        "nova_group": random.randint(1, 4),
        "ingredients_count": random.randint(1, 20),
    }


_GENERATORS: dict[str, Callable[[], dict]] = {
    "crypto_account_annotation": _mock_crypto,
    "fashion_item_annotation": _mock_fashion,
    "food_product_intelligence": _mock_food,
}

_QUALITY_METHODS = ["consensus", "expert_review", "single_review"]


def _generate_item(vertical_slug: str) -> dict:
    gen = _GENERATORS.get(vertical_slug, _mock_crypto)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": str(uuid.uuid4()),
        "vertical_slug": vertical_slug,
        "payload": gen(),
        "quality_score": round(0.70 + random.random() * 0.30, 4),
        "quality_method": random.choice(_QUALITY_METHODS),
        "validator_count": random.randint(1, 4),
        "consensus_ratio": round(0.70 + random.random() * 0.30, 4),
        "unit_price_usd": round(random.random() * 0.08 + 0.01, 4),
        "status": "pending",
        "environment": "sandbox",
        "created_at": now,
    }


@router.get("/simulate")
async def sandbox_simulate(
    vertical_slug: str = Query(
        ..., description="Vertical slug, e.g. crypto_account_annotation"
    ),
    limit: int = Query(5, ge=1, le=50),
):
    """Return mock annotation items for the given vertical.

    Public endpoint — no auth required. Used by:
    - Dashboard sandbox mode (users without orgs)
    - CLI/API sandbox testing
    """
    items = [_generate_item(vertical_slug) for _ in range(limit)]
    return {"data": items}
