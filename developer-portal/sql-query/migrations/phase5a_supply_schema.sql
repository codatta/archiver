-- Phase 5A: Supply-side schema migration (AliCloud PolarDB MySQL → Supabase Postgres)
-- Creates a `supply` schema to namespace supply-side tables separately from
-- the demand-side `public` schema.
--
-- Source: cfp_metacore database on AliCloud PolarDB (MySQL)
-- Tables migrated: cfp_frontier, cfp_frontier_task, cfp_task_submission, cfp_task_audit_record
--
-- Run against: Supabase project uxafdddzhgdhsabkwmgw

-- ============================================================
-- 0. Create schema
-- ============================================================

CREATE SCHEMA IF NOT EXISTS supply;

-- ============================================================
-- 1. cfp_frontier — data domains / verticals
-- ============================================================

CREATE TABLE IF NOT EXISTS supply.cfp_frontier (
    frontier_id  BIGINT PRIMARY KEY,
    title        TEXT NOT NULL DEFAULT '',
    description  TEXT,
    logo         TEXT,
    status       TEXT NOT NULL DEFAULT 'PREPARING',
        -- PREPARING | ONLINE | PAUSED | OFFLINE
    ext_info     JSONB,
    deleted      SMALLINT NOT NULL DEFAULT 0,
    gmt_create   TIMESTAMPTZ NOT NULL DEFAULT now(),
    gmt_modified TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_frontier_status
    ON supply.cfp_frontier (status) WHERE deleted = 0;

-- ============================================================
-- 2. cfp_frontier_task — tasks within a frontier
-- ============================================================

CREATE TABLE IF NOT EXISTS supply.cfp_frontier_task (
    task_id      BIGINT PRIMARY KEY,
    frontier_id  BIGINT NOT NULL REFERENCES supply.cfp_frontier(frontier_id),
    name         TEXT NOT NULL DEFAULT '',
    task_type    TEXT NOT NULL DEFAULT 'submission',
        -- submission | validation
    status       TEXT NOT NULL DEFAULT 'PREPARING',
        -- PREPARING | COLLECTING | FINISHED | PAUSE | STOP
    template_id  BIGINT,
    data_display JSONB,
    reward_info  JSONB,
    max_count    INT,
    duplicate_permission BOOLEAN NOT NULL DEFAULT FALSE,
    deleted      SMALLINT NOT NULL DEFAULT 0,
    gmt_create   TIMESTAMPTZ NOT NULL DEFAULT now(),
    gmt_modified TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_task_frontier
    ON supply.cfp_frontier_task (frontier_id) WHERE deleted = 0;

CREATE INDEX IF NOT EXISTS idx_task_status
    ON supply.cfp_frontier_task (status) WHERE deleted = 0;

-- ============================================================
-- 3. cfp_task_submission — completed work units (4M+ rows)
-- ============================================================

CREATE TABLE IF NOT EXISTS supply.cfp_task_submission (
    submission_id  BIGINT PRIMARY KEY,
    task_id        BIGINT NOT NULL,
    user_id        BIGINT NOT NULL,
    data_submission JSONB,
    result         SMALLINT,
        -- 1-5 numeric grade: 5=S, 4=A, 3=B, 2=C, 1=D
    source         TEXT,
        -- MOBILE | PC
    status         TEXT NOT NULL DEFAULT 'PENDING',
        -- PENDING | SUBMITTED | ADOPT | REFUSED | REPORT_SPAM
    chain_status   SMALLINT NOT NULL DEFAULT 0,
        -- 0 → 1 → 2 → 3 (on-chain confirmation)
    reward_info    JSONB,
    deleted        SMALLINT NOT NULL DEFAULT 0,
    gmt_create     TIMESTAMPTZ NOT NULL DEFAULT now(),
    gmt_modified   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Primary query: pull adopted submissions by task_id, cursor on submission_id
CREATE INDEX IF NOT EXISTS idx_submission_task_status
    ON supply.cfp_task_submission (task_id, status, submission_id)
    WHERE deleted = 0;

-- Aggregate queries: count submissions per task
CREATE INDEX IF NOT EXISTS idx_submission_task_deleted
    ON supply.cfp_task_submission (task_id, deleted);

-- User lookup
CREATE INDEX IF NOT EXISTS idx_submission_user
    ON supply.cfp_task_submission (user_id) WHERE deleted = 0;

-- ============================================================
-- 4. cfp_task_audit_record — quality audit records
-- ============================================================

CREATE TABLE IF NOT EXISTS supply.cfp_task_audit_record (
    id             BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    submission_id  BIGINT NOT NULL,
    rating         SMALLINT,
    reason         TEXT,
    deleted        SMALLINT NOT NULL DEFAULT 0,
    gmt_create     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_audit_submission
    ON supply.cfp_task_audit_record (submission_id) WHERE deleted = 0;

-- ============================================================
-- 5. Grant PostgREST access to the supply schema (optional)
--    Needed if you ever want to query via Supabase client SDK
-- ============================================================

GRANT USAGE ON SCHEMA supply TO anon, authenticated, service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA supply TO anon, authenticated, service_role;
ALTER DEFAULT PRIVILEGES IN SCHEMA supply GRANT SELECT ON TABLES TO anon, authenticated, service_role;

-- ============================================================
-- 6. Comment the schema for documentation
-- ============================================================

COMMENT ON SCHEMA supply IS 'Supply-side data migrated from AliCloud PolarDB MySQL (cfp_metacore). Read-only for the developer portal.';
COMMENT ON TABLE supply.cfp_frontier IS 'Data domains / verticals — business categories for annotation tasks';
COMMENT ON TABLE supply.cfp_frontier_task IS 'Tasks within a frontier — individual work units assigned to workers';
COMMENT ON TABLE supply.cfp_task_submission IS 'Completed work units submitted by supply-side workers (~4M rows)';
COMMENT ON TABLE supply.cfp_task_audit_record IS 'Quality audit results from automated review pipeline';
