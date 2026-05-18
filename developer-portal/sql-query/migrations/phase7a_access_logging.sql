-- Phase 7A: Access Logging, Metering & Variable Pricing
-- Run against Supabase PostgreSQL

-- 1. Pricing schedule — per-frontier, per-task, per-quality-tier pricing
CREATE TABLE IF NOT EXISTS pricing_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    frontier_id TEXT NOT NULL,
    task_id TEXT,  -- null = applies to all tasks in frontier
    quality_tier TEXT,  -- null = applies to any quality tier (S/A/B/C/D)
    unit_price_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
    effective_from TIMESTAMPTZ NOT NULL DEFAULT now(),
    effective_until TIMESTAMPTZ,  -- null = no expiry
    created_by TEXT NOT NULL DEFAULT 'system',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_pricing_schedule_frontier
    ON pricing_schedule (frontier_id, task_id, quality_tier);

-- 2. Access log — append-only, every data-touching API request
CREATE TABLE IF NOT EXISTS access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    org_id UUID REFERENCES organizations(id),
    api_key_id UUID REFERENCES api_keys(id),
    user_id UUID,
    endpoint TEXT NOT NULL,
    method TEXT NOT NULL DEFAULT 'GET',
    subscription_id UUID,
    frontier_id TEXT,
    record_count INT NOT NULL DEFAULT 0,
    item_costs JSONB,  -- [{submission_id, task_id, unit_price_usd}, ...]
    total_cost_usd NUMERIC(10,6) NOT NULL DEFAULT 0,
    response_status INT NOT NULL DEFAULT 200,
    latency_ms INT NOT NULL DEFAULT 0,
    ip_address INET
);

CREATE INDEX IF NOT EXISTS idx_access_log_org_ts
    ON access_log (org_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_access_log_endpoint
    ON access_log (endpoint, timestamp DESC);

-- 3. Usage daily — aggregated rollups for billing
CREATE TABLE IF NOT EXISTS usage_daily (
    org_id UUID NOT NULL REFERENCES organizations(id),
    subscription_id UUID,
    date DATE NOT NULL,
    pull_count INT NOT NULL DEFAULT 0,
    record_count INT NOT NULL DEFAULT 0,
    adopt_count INT NOT NULL DEFAULT 0,
    dispute_count INT NOT NULL DEFAULT 0,
    preview_count INT NOT NULL DEFAULT 0,
    total_cost_usd NUMERIC(12,6) NOT NULL DEFAULT 0,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (org_id, subscription_id, date)
);

CREATE INDEX IF NOT EXISTS idx_usage_daily_org_date
    ON usage_daily (org_id, date DESC);

-- 4. Seed a default pricing schedule (free tier — $0.00 for all)
-- Real prices will be set per-frontier as contracts are created.
-- Example: INSERT INTO pricing_schedule (frontier_id, unit_price_usd) VALUES ('12345', 0.05);
