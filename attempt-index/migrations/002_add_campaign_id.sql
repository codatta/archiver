-- Migration 002: add campaign_id for isolated campaign-scope dedup
-- Nullable: task/frontier/global records do not require a campaign_id.
-- campaign-scoped queries filter by campaign_id rather than uniqueness_scope.

ALTER TABLE attempt_records
    ADD COLUMN IF NOT EXISTS campaign_id text;

-- Partial index: only rows with a campaign_id are included.
-- Covers the campaign-scope query: (campaign_id, sample_key, match_key).
-- Note: column was named match_ref when this migration was applied;
-- migration 003 renames it to match_key (PostgreSQL auto-updates the index).
CREATE INDEX IF NOT EXISTS idx_attempt_campaign_lookup
    ON attempt_records (campaign_id, sample_key, match_ref)
    WHERE campaign_id IS NOT NULL;
