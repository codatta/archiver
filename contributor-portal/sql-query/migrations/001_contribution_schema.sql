-- ═══════════════════════════════════════════════════════════════════════════
-- Contributor Portal — Schema Migration 001
--
-- ADDITIVE migration for the shared Supabase instance (uxafdddzhgdhsabkwmgw).
-- Creates contribution-specific tables. Does NOT modify any existing
-- developer-portal tables.
--
-- Apply: psql $SUPABASE_DB_URL -f sql-query/migrations/001_contribution_schema.sql
-- ═══════════════════════════════════════════════════════════════════════════


-- ─── Campaign Framework ──────────────────────────────────────────────────────
-- Shared contract between developer portal (writes config) and
-- contributor portal (writes instances).

CREATE TABLE IF NOT EXISTS campaigns (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id            uuid REFERENCES organizations(id),
  frontier_id       text NOT NULL,
  template_id       text NOT NULL,
  name              text NOT NULL,
  status            text NOT NULL DEFAULT 'draft'
                    CHECK (status IN ('draft','live','paused','completed','cancelled')),
  annotation_config text,
  params            jsonb NOT NULL DEFAULT '{}',
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_campaigns_status ON campaigns (status);
CREATE INDEX IF NOT EXISTS idx_campaigns_frontier ON campaigns (frontier_id);


CREATE TABLE IF NOT EXISTS tasks (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  campaign_id       uuid NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
  task_key          text NOT NULL,
  name              text NOT NULL,
  origin            text NOT NULL CHECK (origin IN ('manual','auto_generated')),
  execution         text NOT NULL CHECK (execution IN ('human','agent')),
  annotation_config text,
  ml_backend_url    text,
  config            jsonb NOT NULL DEFAULT '{}',
  depends_on        uuid[] NOT NULL DEFAULT '{}',
  position          int NOT NULL,
  UNIQUE (campaign_id, task_key)
);

CREATE INDEX IF NOT EXISTS idx_tasks_campaign ON tasks (campaign_id);


CREATE TABLE IF NOT EXISTS task_instances (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_id               uuid NOT NULL REFERENCES tasks(id),
  campaign_id           uuid NOT NULL REFERENCES campaigns(id),
  parent_instances      uuid[] NOT NULL DEFAULT '{}',
  content_hash          text,
  annotation_config_ver text,
  contributor_id        uuid,
  quality_grade         text CHECK (quality_grade IN ('S','A','B','C','D')),
  status                text NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending','processing','submitted',
                                          'validated','rejected','failed')),
  payload               jsonb,
  submitted_at          timestamptz,
  validated_at          timestamptz,
  created_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_instances_parent ON task_instances USING GIN (parent_instances);
CREATE INDEX IF NOT EXISTS idx_instances_campaign ON task_instances (campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_instances_hash ON task_instances (content_hash);
CREATE INDEX IF NOT EXISTS idx_instances_task ON task_instances (task_id, status);
CREATE INDEX IF NOT EXISTS idx_instances_contributor ON task_instances (contributor_id);


-- ─── Vision Processing Workflow ──────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS processing_jobs (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  t1_instance_id    uuid NOT NULL REFERENCES task_instances(id),
  campaign_id       uuid NOT NULL REFERENCES campaigns(id),
  filename          text NOT NULL,
  task_name         text,
  scenario_code     text NOT NULL DEFAULT 'SCENE_01',
  status            text NOT NULL DEFAULT 'processing'
                    CHECK (status IN ('processing','ready','failed')),
  step              text NOT NULL DEFAULT 'upload',
  step_pct          int NOT NULL DEFAULT 0,
  input_type        text CHECK (input_type IN ('video','sequence')),
  file_hash         text,
  compress_px       int NOT NULL DEFAULT 0,
  detection_params  jsonb,
  result            jsonb,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_campaign ON processing_jobs (campaign_id);
CREATE INDEX IF NOT EXISTS idx_jobs_status ON processing_jobs (status);


CREATE TABLE IF NOT EXISTS clips (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id            uuid NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
  t2_instance_id    uuid REFERENCES task_instances(id),
  start_idx         int NOT NULL,
  end_idx           int NOT NULL,
  start_ms          int NOT NULL,
  end_ms            int NOT NULL,
  start_ns          bigint,
  end_ns            bigint,
  fps               float NOT NULL,
  thumb_url         text,
  blur_score        float,
  brightness        float,
  frame_count       int NOT NULL,
  actions           jsonb
);

CREATE INDEX IF NOT EXISTS idx_clips_job ON clips (job_id);


CREATE TABLE IF NOT EXISTS clip_frames (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  clip_id             uuid NOT NULL REFERENCES clips(id) ON DELETE CASCADE,
  frame_idx           int NOT NULL,
  file_url            text NOT NULL,
  timestamp_ns        bigint,
  motion_score        float,
  person_detected     boolean,
  person_bbox         jsonb,
  arm_keypoints       jsonb,
  hand_activity_score float,
  blur_score          float,
  brightness          float
);

CREATE INDEX IF NOT EXISTS idx_frames_clip ON clip_frames (clip_id, frame_idx);


CREATE TABLE IF NOT EXISTS segments (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id            uuid NOT NULL REFERENCES processing_jobs(id) ON DELETE CASCADE,
  state             text NOT NULL
                    CHECK (state IN ('keep','review','culled_motion',
                                     'culled_low_action','culled_person')),
  start_idx         int NOT NULL,
  end_idx           int NOT NULL,
  frame_count       int NOT NULL,
  duration_ms       int NOT NULL,
  thumb_url         text,
  cull_reason       text,
  is_reviewed       boolean NOT NULL DEFAULT false,
  review_decision   text CHECK (review_decision IN ('valid','invalid'))
);

CREATE INDEX IF NOT EXISTS idx_segments_job ON segments (job_id);


-- ─── Embodiment-X Annotations ────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS annotations (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  t3_instance_id    uuid NOT NULL REFERENCES task_instances(id),
  job_id            uuid NOT NULL REFERENCES processing_jobs(id),
  temporal          jsonb NOT NULL,
  spatial           jsonb,
  quality_metadata  jsonb,
  created_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_annotations_instance ON annotations (t3_instance_id);


-- ─── Contributors ────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS contributors (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  display_name      text,
  email             text,
  wallet_address    text,
  reputation_score  float NOT NULL DEFAULT 0,
  created_at        timestamptz NOT NULL DEFAULT now()
);


-- ─── Mock: On-Chain Lineage Staging ──────────────────────────────────────────
-- Schema matches InstanceRecord from data-lineage spec §3.1.
-- staging_status is always 'mock_committed' until real chain integration.

CREATE TABLE IF NOT EXISTS lineage_staging (
  instance_id         uuid PRIMARY KEY REFERENCES task_instances(id),
  contributor_did     text,
  campaign_id         uuid NOT NULL,
  task_id             uuid NOT NULL,
  frontier_id         text NOT NULL,
  parent_instances    uuid[] NOT NULL DEFAULT '{}',
  content_hash        text,
  annotation_config_ver text,
  compensation_model  text NOT NULL DEFAULT 'fixed',
  upstream_shares     jsonb,
  quality_grade       text CHECK (quality_grade IN ('S','A','B','C','D')),
  staged_at           timestamptz NOT NULL DEFAULT now(),
  staging_status      text NOT NULL DEFAULT 'mock_committed'
);
