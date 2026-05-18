-- Migration 003: rename match_ref → match_key for naming consistency
-- match_key is the term used everywhere in the API, matchers, and docs.
-- PostgreSQL automatically updates all index definitions on column rename.
ALTER TABLE attempt_records RENAME COLUMN match_ref TO match_key;
