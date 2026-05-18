#!/usr/bin/env python3
"""ETL script: Migrate supply-side data from AliCloud PolarDB (MySQL) → Supabase Postgres.

Prerequisites:
    1. Run the schema migration first:
       sql-query/migrations/phase5a_supply_schema.sql
    2. Set environment variables (or use .env):
       MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE
       SUPABASE_DB_URL (direct Postgres connection string)

Usage:
    cd packages/api
    uv run python ../../scripts/migrate_mysql_to_supabase.py [--table TABLE] [--batch-size N] [--dry-run]

Tables migrated (in order, respecting foreign keys):
    1. cfp_frontier          (~12 rows)
    2. cfp_frontier_task     (~100s rows)
    3. cfp_task_submission   (~4M rows)  ← bulk, batched
    4. cfp_task_audit_record (~2.7M rows) ← bulk, batched
"""
import argparse
import asyncio
import json
import logging
import os
import sys
import time

import aiomysql
import asyncpg

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────

BATCH_SIZE = 5000  # rows per INSERT batch (tunable)

TABLES = [
    {
        "name": "cfp_frontier",
        "mysql_query": """
            SELECT frontier_id, title, COALESCE(description, '') AS description,
                   logo, status, ext_info, deleted, gmt_create, gmt_modified
            FROM cfp_frontier
        """,
        "pg_insert": """
            INSERT INTO supply.cfp_frontier
                (frontier_id, title, description, logo, status, ext_info,
                 deleted, gmt_create, gmt_modified)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT (frontier_id) DO UPDATE SET
                title = EXCLUDED.title,
                status = EXCLUDED.status,
                gmt_modified = EXCLUDED.gmt_modified
        """,
        "columns": [
            "frontier_id", "title", "description", "logo", "status",
            "ext_info", "deleted", "gmt_create", "gmt_modified",
        ],
        "json_columns": {"ext_info"},
    },
    {
        "name": "cfp_frontier_task",
        "mysql_query": """
            SELECT task_id, frontier_id, COALESCE(name, '') AS name,
                   COALESCE(task_type, 'submission') AS task_type,
                   status, template_id, data_display, reward_info,
                   max_count, duplicate_permission, deleted,
                   gmt_create, gmt_modified
            FROM cfp_frontier_task
        """,
        "pg_insert": """
            INSERT INTO supply.cfp_frontier_task
                (task_id, frontier_id, name, task_type, status, template_id,
                 data_display, reward_info, max_count, duplicate_permission,
                 deleted, gmt_create, gmt_modified)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            ON CONFLICT (task_id) DO UPDATE SET
                name = EXCLUDED.name,
                status = EXCLUDED.status,
                gmt_modified = EXCLUDED.gmt_modified
        """,
        "columns": [
            "task_id", "frontier_id", "name", "task_type", "status",
            "template_id", "data_display", "reward_info", "max_count",
            "duplicate_permission", "deleted", "gmt_create", "gmt_modified",
        ],
        "json_columns": {"data_display", "reward_info"},
    },
    {
        "name": "cfp_task_submission",
        "mysql_query": """
            SELECT submission_id, task_id, user_id, data_submission,
                   result, source, status, chain_status, reward_info,
                   deleted, gmt_create, gmt_modified
            FROM cfp_task_submission
        """,
        "pg_insert": """
            INSERT INTO supply.cfp_task_submission
                (submission_id, task_id, user_id, data_submission,
                 result, source, status, chain_status, reward_info,
                 deleted, gmt_create, gmt_modified)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            ON CONFLICT (submission_id) DO NOTHING
        """,
        "columns": [
            "submission_id", "task_id", "user_id", "data_submission",
            "result", "source", "status", "chain_status", "reward_info",
            "deleted", "gmt_create", "gmt_modified",
        ],
        "json_columns": {"data_submission", "reward_info"},
        "batch_column": "submission_id",  # for cursor-based batching
    },
    {
        "name": "cfp_task_audit_record",
        "mysql_query": """
            SELECT submission_id, rating, reason, deleted, gmt_create
            FROM cfp_task_audit_record
        """,
        "pg_insert": """
            INSERT INTO supply.cfp_task_audit_record
                (submission_id, rating, reason, deleted, gmt_create)
            VALUES ($1, $2, $3, $4, $5)
        """,
        "columns": ["submission_id", "rating", "reason", "deleted", "gmt_create"],
        "json_columns": set(),
        "truncate_first": True,  # no PK in source, so truncate + reload
    },
]


# ── Helpers ──────────────────────────────────────────────────────────────────


def _parse_json(value):
    """Convert MySQL JSON text/string to Python dict for asyncpg jsonb."""
    if value is None:
        return None
    if isinstance(value, dict):
        return json.dumps(value)
    if isinstance(value, str):
        try:
            json.loads(value)  # validate
            return value  # already valid JSON string
        except (json.JSONDecodeError, TypeError):
            return None
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8")
    return json.dumps(value)


def _row_to_params(row: dict, table_spec: dict) -> tuple:
    """Convert a MySQL row dict to an asyncpg parameter tuple."""
    params = []
    for col in table_spec["columns"]:
        val = row.get(col)
        if col in table_spec["json_columns"]:
            val = _parse_json(val)
        if col == "duplicate_permission":
            val = bool(val) if val is not None else False
        params.append(val)
    return tuple(params)


# ── Migration logic ─────────────────────────────────────────────────────────


async def migrate_table(
    mysql_pool: aiomysql.Pool,
    pg_pool: asyncpg.Pool,
    table_spec: dict,
    batch_size: int,
    dry_run: bool = False,
):
    """Migrate a single table from MySQL to Postgres."""
    name = table_spec["name"]
    logger.info("━━━ Migrating %s ━━━", name)

    # Count source rows
    async with mysql_pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(f"SELECT COUNT(*) FROM {name}")
            (source_count,) = await cur.fetchone()
    logger.info("Source rows: %d", source_count)

    if dry_run:
        logger.info("[DRY RUN] Would migrate %d rows from %s", source_count, name)
        return

    # Truncate if specified (for tables without stable PK)
    if table_spec.get("truncate_first"):
        async with pg_pool.acquire() as conn:
            await conn.execute(f"TRUNCATE supply.{name}")
        logger.info("Truncated supply.%s", name)

    # Batch migration
    batch_col = table_spec.get("batch_column")
    total_migrated = 0
    last_cursor = 0
    start_time = time.monotonic()

    while True:
        # Fetch batch from MySQL
        if batch_col:
            query = (
                f"{table_spec['mysql_query']} "
                f"WHERE {batch_col} > %s ORDER BY {batch_col} ASC LIMIT %s"
            )
            async with mysql_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(query, (last_cursor, batch_size))
                    rows = await cur.fetchall()
        else:
            # Small tables — fetch all at once
            async with mysql_pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cur:
                    await cur.execute(table_spec["mysql_query"])
                    rows = await cur.fetchall()

        if not rows:
            break

        # Convert and insert into Postgres
        pg_rows = [_row_to_params(r, table_spec) for r in rows]

        async with pg_pool.acquire() as conn:
            await conn.executemany(table_spec["pg_insert"], pg_rows)

        total_migrated += len(rows)
        elapsed = time.monotonic() - start_time
        rate = total_migrated / elapsed if elapsed > 0 else 0
        logger.info(
            "  %s: %d / %d (%.0f rows/s)",
            name, total_migrated, source_count, rate,
        )

        if batch_col:
            last_cursor = rows[-1][batch_col]
        else:
            break  # small table, done in one pass

    # Validate
    async with pg_pool.acquire() as conn:
        dest_count = await conn.fetchval(f"SELECT COUNT(*) FROM supply.{name}")

    logger.info(
        "✓ %s: source=%d, dest=%d, match=%s",
        name, source_count, dest_count, source_count == dest_count,
    )
    if source_count != dest_count:
        logger.warning(
            "⚠ Row count mismatch for %s: source=%d, dest=%d (delta=%d)",
            name, source_count, dest_count, dest_count - source_count,
        )


async def main():
    parser = argparse.ArgumentParser(description="Migrate MySQL → Supabase Postgres")
    parser.add_argument("--table", help="Migrate only this table")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    parser.add_argument("--dry-run", action="store_true", help="Count only, no writes")
    args = parser.parse_args()

    # Load env from .env if present
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    mysql_host = os.environ.get("MYSQL_HOST", "")
    supabase_db_url = os.environ.get("SUPABASE_DB_URL", "")

    if not mysql_host:
        logger.error("MYSQL_HOST not set")
        sys.exit(1)
    if not supabase_db_url:
        logger.error("SUPABASE_DB_URL not set")
        sys.exit(1)

    # Connect to both databases
    mysql_pool = await aiomysql.create_pool(
        host=mysql_host,
        port=int(os.environ.get("MYSQL_PORT", 3306)),
        user=os.environ.get("MYSQL_USER", ""),
        password=os.environ.get("MYSQL_PASSWORD", ""),
        db=os.environ.get("MYSQL_DATABASE", "cfp_metacore"),
        charset="utf8mb4",
        autocommit=True,
        maxsize=5,
        connect_timeout=30,
    )
    logger.info("Connected to MySQL: %s", mysql_host)

    pg_pool = await asyncpg.create_pool(dsn=supabase_db_url, min_size=2, max_size=5)
    logger.info("Connected to Supabase Postgres")

    # Migrate
    tables = TABLES
    if args.table:
        tables = [t for t in tables if t["name"] == args.table]
        if not tables:
            logger.error("Unknown table: %s", args.table)
            sys.exit(1)

    start = time.monotonic()
    for table_spec in tables:
        await migrate_table(mysql_pool, pg_pool, table_spec, args.batch_size, args.dry_run)

    elapsed = time.monotonic() - start
    logger.info("━━━ Migration complete in %.1f seconds ━━━", elapsed)

    mysql_pool.close()
    await mysql_pool.wait_closed()
    await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
