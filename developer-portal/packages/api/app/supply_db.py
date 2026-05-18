"""Async Postgres connection pool for supply-side data (Supabase direct).

Replaces mysql_db.py — connects directly to Supabase Postgres via asyncpg,
querying the `supply` schema where AliCloud data has been migrated.

Usage:
    from app.supply_db import fetch_all, fetch_one

    rows = await fetch_all(
        "SELECT * FROM supply.cfp_frontier WHERE status = $1",
        "ONLINE",
    )
"""
import logging
from contextlib import asynccontextmanager

import asyncpg

from app.config import settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


async def create_pool() -> None:
    """Create the Postgres connection pool. Called on FastAPI startup."""
    global _pool
    if not settings.supabase_db_url:
        logger.warning("SUPABASE_DB_URL not set — supply DB pool disabled")
        return
    try:
        _pool = await asyncpg.create_pool(
            dsn=settings.supabase_db_url,
            min_size=0,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Supply DB pool created (asyncpg → Supabase Postgres)")
    except Exception as e:
        logger.warning("Supply DB pool creation failed (will retry on first query): %s", e)
        _pool = None


async def close_pool() -> None:
    """Close the Postgres connection pool. Called on FastAPI shutdown."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Supply DB pool closed")


async def ensure_pool() -> asyncpg.Pool:
    """Get the connection pool, creating it lazily if needed."""
    global _pool
    if _pool is None:
        if not settings.supabase_db_url:
            raise RuntimeError("SUPABASE_DB_URL not set")
        _pool = await asyncpg.create_pool(
            dsn=settings.supabase_db_url,
            min_size=0,
            max_size=10,
            command_timeout=30,
        )
    return _pool


@asynccontextmanager
async def get_connection():
    """Yield a Postgres connection from the pool."""
    pool = await ensure_pool()
    async with pool.acquire() as conn:
        yield conn


async def _reset_pool() -> None:
    """Destroy and recreate the pool on connection failure."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
    logger.info("Supply DB pool reset — will reconnect on next query")


async def fetch_all(query: str, *args) -> list[dict]:
    """Execute a query and return all rows as dicts.

    Uses asyncpg positional params ($1, $2, ...).
    """
    for attempt in range(3):
        try:
            pool = await ensure_pool()
            rows = await pool.fetch(query, *args)
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning("Supply DB query failed (attempt %d): %s", attempt + 1, e)
            await _reset_pool()
            if attempt == 2:
                raise


async def fetch_one(query: str, *args) -> dict | None:
    """Execute a query and return the first row as a dict, or None.

    Uses asyncpg positional params ($1, $2, ...).
    """
    for attempt in range(3):
        try:
            pool = await ensure_pool()
            row = await pool.fetchrow(query, *args)
            return dict(row) if row else None
        except Exception as e:
            logger.warning("Supply DB query failed (attempt %d): %s", attempt + 1, e)
            await _reset_pool()
            if attempt == 2:
                raise
