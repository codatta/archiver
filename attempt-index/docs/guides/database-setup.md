# Database Setup

AttemptIndex uses a single table — `attempt_records` — in Supabase PostgreSQL. This guide covers initial setup, running migrations, and pre-loading data for uniqueness scanning.

---

## The schema

```sql
CREATE TABLE IF NOT EXISTS attempt_records (
    submission_id       text        PRIMARY KEY,
    task_id             text        NOT NULL,
    sample_key          text        NOT NULL,
    contributor_uid     text,                          -- nullable
    match_key           text        NOT NULL,          -- the computed match key
    payload_type        text        NOT NULL
        CHECK (payload_type IN ('structured', 'text', 'image', 'video', 'audio')),
    submitted_at        timestamptz NOT NULL,
    uniqueness_version  text        NOT NULL DEFAULT 'v1',
    uniqueness_scope    text        NOT NULL
        CHECK (uniqueness_scope IN ('task', 'campaign', 'frontier', 'global')),
    attempt_index       int         NOT NULL DEFAULT 1 CHECK (attempt_index >= 1),
    created_at          timestamptz NOT NULL DEFAULT now()
);
```

**Design notes:**
- `submission_id` is the primary key — guarantees idempotency by construction.
- `match_key` stores the computed match key (e.g. `mk:94866cf6...`) — never the raw payload.
- `attempt_index` is stored so idempotent re-calls can reconstruct the response without re-querying.

### Indexes

```sql
-- Lookup by sample within a single task (task-scope queries)
CREATE INDEX IF NOT EXISTS idx_attempt_sample_lookup
    ON attempt_records (task_id, sample_key, submitted_at);

-- Dedup lookup: find all prior records with same match key in a task
CREATE INDEX IF NOT EXISTS idx_attempt_match_lookup
    ON attempt_records (task_id, sample_key, match_key);

-- Cross-scope lookup (campaign / frontier / global)
CREATE INDEX IF NOT EXISTS idx_attempt_scope_lookup
    ON attempt_records (uniqueness_scope, sample_key, submitted_at);
```

---

## Running the migration

The migration file is at `migrations/001_attempt_records.sql`. Apply it once before the service starts.

### Option A — Supabase MCP (recommended for this project)

```python
# In a Python script or Claude Code session connected to Supabase MCP
mcp__supabase-inductive__apply_migration(
    name="attempt_records",
    query=open("migrations/001_attempt_records.sql").read()
)
```

### Option B — Supabase CLI

```bash
supabase db push
# or for a specific project
supabase db push --project-ref uxafdddzhgdhsabkwmgw
```

### Option C — Direct SQL (psql or Supabase SQL Editor)

Copy the content of `migrations/001_attempt_records.sql` into the Supabase SQL Editor and run it. The migration is idempotent (`IF NOT EXISTS`) — safe to run multiple times.

---

## Row Level Security

`attempt_records` is a service-to-service table. No end users access it directly. RLS is disabled:

```sql
ALTER TABLE attempt_records DISABLE ROW LEVEL SECURITY;
```

This was applied as part of the initial setup. If you ever re-enable RLS, you must add a service-role policy:

```sql
ALTER TABLE attempt_records ENABLE ROW LEVEL SECURITY;

CREATE POLICY "service_role_full_access" ON attempt_records
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
```

---

## Pre-loading data for uniqueness scanning

There are three reasons to pre-load data before a campaign opens:

1. **Known public datasets** — prevent contributors from submitting copies of open-source data
2. **Prior collections** — if you ran an earlier campaign, carry forward its records so new campaigns benefit from cross-campaign dedup
3. **Customer-provided historical data** — a customer brings their own prior annotations and wants to avoid re-annotating the same items

All three use the same bootstrap API. See [Bootstrapping Known Datasets](./bootstrap.md) for the full guide. Here is the database perspective.

### What a bootstrap record looks like in the table

```sql
SELECT * FROM attempt_records WHERE submission_id LIKE 'bootstrap:%' LIMIT 1;

submission_id    | bootstrap:roboarm1k-vid-042
task_id          | task-frontier-robotics
sample_key       | roboarm1k:vid-042
contributor_uid  | NULL
match_key        | mk:phash-roboarm1k-042
payload_type     | structured
submitted_at     | 2025-11-01 00:00:00+00
uniqueness_version | v1
uniqueness_scope | frontier
attempt_index    | 1
created_at       | 2026-04-27 09:00:00+00
```

Bootstrap records are indistinguishable from live submission records at the query level — they are in the same table, use the same indexes, and are found by the same queries. The only distinction is the `bootstrap:` prefix on `submission_id`, which downstream systems use as a signal in `nearest_prior`.

### Bulk pre-load via SQL (for large datasets)

For datasets with millions of records, loading via the API (1 network round-trip per record) is too slow. Use a direct SQL `COPY` or `INSERT` instead:

```sql
-- Load from a CSV file
COPY attempt_records (
    submission_id, task_id, sample_key, match_key,
    payload_type, submitted_at, uniqueness_scope,
    uniqueness_version, attempt_index
)
FROM '/path/to/bootstrap_records.csv'
WITH (FORMAT csv, HEADER true);
```

CSV format:

```
submission_id,task_id,sample_key,match_key,payload_type,submitted_at,uniqueness_scope,uniqueness_version,attempt_index
bootstrap:roboarm1k-001,task-frontier-robotics,roboarm1k:vid-001,mk:abc123,structured,2025-11-01T00:00:00Z,frontier,v1,1
bootstrap:roboarm1k-002,task-frontier-robotics,roboarm1k:vid-002,mk:def456,structured,2025-11-01T00:00:00Z,frontier,v1,1
```

Or in Python using the supabase-py client with batch inserts:

```python
from app.db.client import get_client

client = get_client()
records = [...]  # list of dicts

# Insert in batches of 500 to avoid request size limits
BATCH_SIZE = 500
for i in range(0, len(records), BATCH_SIZE):
    batch = records[i:i + BATCH_SIZE]
    client.table("attempt_records").insert(batch).execute()
    print(f"Inserted batch {i // BATCH_SIZE + 1}")
```

This is faster than the bootstrap API because it bypasses the dedup check. Use it only for the initial pre-load when you are certain the records are fresh. For incremental or repeated loads, use the API (which handles duplicates automatically).

---

## Querying the database

Common queries for monitoring and debugging:

```sql
-- Count records per task
SELECT task_id, COUNT(*) as total_records
FROM attempt_records
GROUP BY task_id
ORDER BY total_records DESC;

-- Find all attempts for a specific sample
SELECT submission_id, attempt_index, match_key, submitted_at, contributor_uid
FROM attempt_records
WHERE task_id = 'cipherowl-iran-cex-q2'
  AND sample_key = 'eth:0xabc123'
ORDER BY submitted_at;

-- Find samples that have hit their ceiling (useful for auditing)
-- (ceiling is defined per-call, not stored — query attempt_index = N)
SELECT sample_key, MAX(attempt_index) as max_attempt
FROM attempt_records
WHERE task_id = 'cipherowl-iran-cex-q2'
GROUP BY sample_key
HAVING MAX(attempt_index) >= 3
ORDER BY sample_key;

-- Find all bootstrapped records by source dataset
SELECT submission_id, sample_key, match_key, submitted_at
FROM attempt_records
WHERE submission_id LIKE 'bootstrap:roboarm1k-%'
ORDER BY submitted_at;

-- Detect duplicate match_keys (same content submitted by multiple contributors)
SELECT match_key, COUNT(*) as submission_count, array_agg(submission_id) as submissions
FROM attempt_records
WHERE task_id = 'cipherowl-iran-cex-q2'
GROUP BY match_key
HAVING COUNT(*) > 1
ORDER BY submission_count DESC;
```

---

## Resetting a campaign (development only)

To clear all records for a specific task during development:

```sql
-- ⚠️ Destructive — development use only
DELETE FROM attempt_records
WHERE task_id = 'cipherowl-test-task';
```

To clear test records (matches the test suite's cleanup pattern):

```sql
DELETE FROM attempt_records
WHERE submission_id LIKE 'test:%';
```
