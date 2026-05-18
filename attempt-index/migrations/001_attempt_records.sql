-- AttemptIndex: attempt_records table
-- V0: supports structured and text payload types
-- Stores one record per accepted submission. No raw payloads stored.

CREATE TABLE IF NOT EXISTS attempt_records (
    submission_id       text        PRIMARY KEY,
    task_id             text        NOT NULL,
    sample_key          text        NOT NULL,
    contributor_uid     text,
    match_ref           text        NOT NULL,
    payload_type        text        NOT NULL
        CHECK (payload_type IN ('structured', 'text', 'image', 'video', 'audio')),
    submitted_at        timestamptz NOT NULL,
    uniqueness_version  text        NOT NULL DEFAULT 'v1',
    uniqueness_scope    text        NOT NULL
        CHECK (uniqueness_scope IN ('task', 'campaign', 'frontier', 'global')),
    attempt_index       int         NOT NULL DEFAULT 1 CHECK (attempt_index >= 1),
    created_at          timestamptz NOT NULL DEFAULT now()
);

-- Lookup by sample within a single task (task-scope queries + exact match)
CREATE INDEX IF NOT EXISTS idx_attempt_sample_lookup
    ON attempt_records (task_id, sample_key, submitted_at);

-- Lookup by match_ref within a task (hash dedup)
CREATE INDEX IF NOT EXISTS idx_attempt_match_lookup
    ON attempt_records (task_id, sample_key, match_ref);

-- Lookup across scopes (campaign / frontier / global)
CREATE INDEX IF NOT EXISTS idx_attempt_scope_lookup
    ON attempt_records (uniqueness_scope, sample_key, submitted_at);
