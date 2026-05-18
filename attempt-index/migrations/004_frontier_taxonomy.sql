-- Migration 004: frontier taxonomy — named domain categories + record tagging
-- Option A: metadata tags only; query_prior_matches is unchanged.

CREATE TABLE IF NOT EXISTS frontiers (
    frontier_id   text        PRIMARY KEY,
    name          text        NOT NULL,
    description   text,
    created_at    timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS record_frontiers (
    submission_id  text NOT NULL REFERENCES attempt_records(submission_id),
    frontier_id    text NOT NULL REFERENCES frontiers(frontier_id),
    PRIMARY KEY (submission_id, frontier_id)
);

-- Reverse index: find all records tagged to a given frontier.
CREATE INDEX IF NOT EXISTS idx_record_frontiers_by_frontier
    ON record_frontiers (frontier_id);

-- Service-to-service tables: no end-user access, RLS disabled.
ALTER TABLE frontiers DISABLE ROW LEVEL SECURITY;
ALTER TABLE record_frontiers DISABLE ROW LEVEL SECURITY;
