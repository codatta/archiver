// Domain types for the Humanbased Contributor Portal
// These mirror the Pydantic models in packages/api/app/models/

// ─── Enums ───────────────────────────────────────────────────────────────────

export type CampaignStatus = "draft" | "live" | "paused" | "completed" | "cancelled";
export type TaskOrigin = "manual" | "auto_generated";
export type TaskExecution = "human" | "agent";
export type InstanceStatus = "pending" | "processing" | "submitted" | "validated" | "rejected" | "failed";
export type QualityGrade = "S" | "A" | "B" | "C" | "D";
export type SegmentState = "keep" | "review" | "culled_motion" | "culled_low_action" | "culled_person";
export type JobStatus = "processing" | "ready" | "failed";

// ─── Campaign Framework ──────────────────────────────────────────────────────

export interface Campaign {
  id: string;
  org_id: string | null;
  frontier_id: string;
  template_id: string;
  name: string;
  status: CampaignStatus;
  annotation_config: string | null;
  params: Record<string, unknown>;
  created_at: string;
}

export interface Task {
  id: string;
  campaign_id: string;
  task_key: string;
  name: string;
  origin: TaskOrigin;
  execution: TaskExecution;
  annotation_config: string | null;
  ml_backend_url: string | null;
  config: Record<string, unknown>;
  depends_on: string[];
  position: number;
}

export interface TaskInstance {
  id: string;
  task_id: string;
  campaign_id: string;
  parent_instances: string[];
  content_hash: string | null;
  annotation_config_ver: string | null;
  contributor_id: string | null;
  quality_grade: QualityGrade | null;
  status: InstanceStatus;
  payload: Record<string, unknown> | null;
  submitted_at: string | null;
  validated_at: string | null;
  created_at: string;
}

// ─── Vision Processing ───────────────────────────────────────────────────────

export interface ProcessingJob {
  id: string;
  t1_instance_id: string;
  campaign_id: string;
  filename: string;
  task_name: string | null;
  scenario_code: string;
  status: JobStatus;
  step: string;
  step_pct: number;
  input_type: string | null;
  file_hash: string | null;
  compress_px: number;
  detection_params: Record<string, unknown> | null;
  created_at: string;
}

export interface Clip {
  id: string;
  job_id: string;
  t2_instance_id: string | null;
  start_idx: number;
  end_idx: number;
  start_ms: number;
  end_ms: number;
  start_ns: number | null;
  end_ns: number | null;
  fps: number;
  thumb_url: string | null;
  blur_score: number | null;
  brightness: number | null;
  frame_count: number;
  actions: unknown[] | null;
}

export interface ClipFrame {
  id: string;
  clip_id: string;
  frame_idx: number;
  file_url: string;
  timestamp_ns: number | null;
  motion_score: number | null;
  person_detected: boolean | null;
  person_bbox: BoundingBox | null;
  arm_keypoints: Keypoint[] | null;
  hand_activity_score: number | null;
  blur_score: number | null;
  brightness: number | null;
}

export interface Segment {
  id: string;
  job_id: string;
  state: SegmentState;
  start_idx: number;
  end_idx: number;
  frame_count: number;
  duration_ms: number;
  thumb_url: string | null;
  cull_reason: string | null;
  is_reviewed: boolean;
  review_decision: string | null;
}

// ─── Embodiment-X Annotation ─────────────────────────────────────────────────

export interface Annotation {
  id: string;
  t3_instance_id: string;
  job_id: string;
  temporal: TemporalAnnotation;
  spatial: SpatialAnnotation | null;
  quality_metadata: QualityMetadata | null;
  created_at: string;
}

export interface TemporalAnnotation {
  segments: ActionSegment[];
}

export interface ActionSegment {
  id: string;
  start_ns: number;
  end_ns: number;
  action_label: string;
  language_instruction: string | null;
  task_plan: string[] | null;
}

export interface SpatialAnnotation {
  frames: FrameSpatial[];
}

export interface FrameSpatial {
  frame_idx: number;
  timestamp_ns: number | null;
  bounding_boxes: BoundingBox[];
  keypoints: Keypoint[];
}

export interface BoundingBox {
  label: string;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence: number | null;
}

export interface Keypoint {
  label: string;
  x: number;
  y: number;
  confidence: number | null;
}

export interface QualityMetadata {
  blur_score: number | null;
  brightness: number | null;
  person_detected: boolean | null;
  hand_activity_score: number | null;
}

// ─── Lineage ─────────────────────────────────────────────────────────────────

export interface LineageStagingRecord {
  instance_id: string;
  contributor_did: string | null;
  campaign_id: string;
  task_id: string;
  frontier_id: string;
  parent_instances: string[];
  content_hash: string | null;
  annotation_config_ver: string | null;
  compensation_model: string;
  upstream_shares: UpstreamShares | null;
  quality_grade: QualityGrade | null;
  staged_at: string;
  staging_status: string;
}

export interface UpstreamShares {
  self_bps: number;
  platform_bps: number;
  parents: { id: string; bps: number }[];
}

// ─── ML Backend Protocol (Label Studio) ──────────────────────────────────────

export interface LSPrediction {
  result: LSRegion[];
  score: number | null;
  model_version: string | null;
}

export interface LSRegion {
  id: string;
  from_name: string;
  to_name: string;
  type: string;
  value: Record<string, unknown>;
}

export interface LSTask {
  id: string;
  data: Record<string, unknown>;
  predictions: LSPrediction[];
}
