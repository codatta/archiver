"""Async MySQL connection pool for AliCloud RDS (supply-side, read-only).

Usage:
    from app.mysql_db import mysql_pool, fetch_all, fetch_one

    rows = await fetch_all("SELECT * FROM cfp_frontier WHERE status = %s", ("ONLINE",))
"""
import logging
from contextlib import asynccontextmanager

import aiomysql

from app.config import settings

logger = logging.getLogger(__name__)

_pool: aiomysql.Pool | None = None


async def create_pool() -> None:
    """Create the MySQL connection pool. Called on FastAPI startup."""
    global _pool
    if not settings.mysql_host:
        logger.warning("MYSQL_HOST not set — MySQL pool disabled")
        return
    try:
        _pool = await aiomysql.create_pool(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            db=settings.mysql_database,
            minsize=0,
            maxsize=10,
            autocommit=True,
            charset="utf8mb4",
            connect_timeout=30,
            pool_recycle=300,
        )
        logger.info(
            "MySQL pool created: %s:%s/%s",
            settings.mysql_host, settings.mysql_port, settings.mysql_database,
        )
    except Exception as e:
        logger.warning("MySQL pool creation failed (will retry on first query): %s", e)
        _pool = None


async def close_pool() -> None:
    """Close the MySQL connection pool. Called on FastAPI shutdown."""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
        logger.info("MySQL pool closed")


async def ensure_pool() -> aiomysql.Pool:
    """Get the connection pool, creating it lazily if needed."""
    global _pool
    if _pool is None:
        if not settings.mysql_host:
            raise RuntimeError("MYSQL_HOST not set")
        _pool = await aiomysql.create_pool(
            host=settings.mysql_host,
            port=settings.mysql_port,
            user=settings.mysql_user,
            password=settings.mysql_password,
            db=settings.mysql_database,
            minsize=0,
            maxsize=10,
            autocommit=True,
            charset="utf8mb4",
            connect_timeout=30,
            pool_recycle=300,
        )
    return _pool


@asynccontextmanager
async def get_connection():
    """Yield a MySQL connection from the pool."""
    pool = await ensure_pool()
    async with pool.acquire() as conn:
        yield conn


async def _reset_pool() -> None:
    """Destroy and recreate the pool on connection failure."""
    global _pool
    if _pool:
        _pool.close()
        await _pool.wait_closed()
        _pool = None
    logger.info("MySQL pool reset — will reconnect on next query")


async def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Execute a query and return all rows as dicts."""
    for attempt in range(3):
        try:
            async with get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    return await cur.fetchall()
        except Exception as e:
            logger.warning("MySQL query failed (attempt %d): %s", attempt + 1, e)
            await _reset_pool()
            if attempt == 2:
                raise


async def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Execute a query and return the first row as a dict, or None."""
    for attempt in range(3):
        try:
            async with get_connection() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, params)
                    return await cur.fetchone()
        except Exception as e:
            logger.warning("MySQL query failed (attempt %d): %s", attempt + 1, e)
            await _reset_pool()
            if attempt == 2:
                raise
