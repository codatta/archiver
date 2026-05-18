// Mock workspace data — shapes mirror the Supabase tables defined in
// sql-query/migrations/001_contribution_schema.sql. When I0-4 lands (API wired
// to Supabase), these imports will be replaced with fetch() calls; the consumer
// components should not change.

// ─── Campaign config (read-only, from campaigns table) ───────────────────────

export type DetectionPreset = {
  id: string;
  name: string;
  description: string;
  params: Record<string, string | number | boolean>;
};

export type ActionLabel = {
  value: string;
  background: string; // hex color for timeline chip + palette swatch
  shortcut: string; // keyboard 1–9
};

export type CampaignConfig = {
  id: string;
  name: string;
  frontier: string;
  detectionPresets: DetectionPreset[];
  actionVocabulary: ActionLabel[];
};

export const MOCK_CAMPAIGN: CampaignConfig = {
  id: "camp-k1m",
  name: "Kitchen Manipulation",
  frontier: "Robotics",
  detectionPresets: [
    {
      id: "universal",
      name: "Universal",
      description: "Default YOLO detection, no filtering. Good for exploratory captures.",
      params: { filter_humans: false, require_center: false, motion_threshold: 0.15 },
    },
    {
      id: "yolo_human_filter",
      name: "YOLO Human Filter",
      description: "Keeps segments where a person is detected near frame center.",
      params: { filter_humans: true, require_center: true, motion_threshold: 0.2 },
    },
    {
      id: "workstation",
      name: "Workstation",
      description: "Tuned for stationary camera watching a work surface. Higher arm confidence.",
      params: { workstation_mode: true, arm_conf_threshold: 0.6, motion_threshold: 0.1 },
    },
    {
      id: "workstation_pose",
      name: "Workstation + Pose",
      description: "Workstation mode with full-body pose estimation. Slowest, richest output.",
      params: {
        workstation_mode: true,
        arm_conf_threshold: 0.6,
        pose_estimation: true,
        full_body: true,
      },
    },
  ],
  actionVocabulary: [
    { value: "fold_box", background: "#FF6B6B", shortcut: "1" },
    { value: "fold_textile", background: "#4ECDC4", shortcut: "2" },
    { value: "packing", background: "#45B7D1", shortcut: "3" },
    { value: "pick_place", background: "#96CEB4", shortcut: "4" },
    { value: "other_valid", background: "#FFEAA7", shortcut: "5" },
  ],
};

// ─── Segments (segments table) ───────────────────────────────────────────────

export type SegmentState =
  | "keep" // Vision Engine kept this — green
  | "review" // Vision Engine unsure — yellow
  | "culled_motion" // too little/too much motion
  | "culled_low_action" // no meaningful arm activity
  | "culled_person"; // person not detected / off-center

export type Segment = {
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
  review_decision: "valid" | "invalid" | null;
};

export const MOCK_SEGMENTS: Segment[] = [
  {
    id: "seg-01",
    job_id: "job-001",
    state: "keep",
    start_idx: 0,
    end_idx: 89,
    frame_count: 90,
    duration_ms: 3000,
    thumb_url: null,
    cull_reason: null,
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-02",
    job_id: "job-001",
    state: "culled_low_action",
    start_idx: 90,
    end_idx: 149,
    frame_count: 60,
    duration_ms: 2000,
    thumb_url: null,
    cull_reason: "arm activity below threshold",
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-03",
    job_id: "job-001",
    state: "keep",
    start_idx: 150,
    end_idx: 299,
    frame_count: 150,
    duration_ms: 5000,
    thumb_url: null,
    cull_reason: null,
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-04",
    job_id: "job-001",
    state: "review",
    start_idx: 300,
    end_idx: 389,
    frame_count: 90,
    duration_ms: 3000,
    thumb_url: null,
    cull_reason: "partial person occlusion",
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-05",
    job_id: "job-001",
    state: "culled_motion",
    start_idx: 390,
    end_idx: 419,
    frame_count: 30,
    duration_ms: 1000,
    thumb_url: null,
    cull_reason: "camera shake",
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-06",
    job_id: "job-001",
    state: "keep",
    start_idx: 420,
    end_idx: 569,
    frame_count: 150,
    duration_ms: 5000,
    thumb_url: null,
    cull_reason: null,
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-07",
    job_id: "job-001",
    state: "culled_person",
    start_idx: 570,
    end_idx: 629,
    frame_count: 60,
    duration_ms: 2000,
    thumb_url: null,
    cull_reason: "person not detected",
    is_reviewed: false,
    review_decision: null,
  },
  {
    id: "seg-08",
    job_id: "job-001",
    state: "keep",
    start_idx: 630,
    end_idx: 749,
    frame_count: 120,
    duration_ms: 4000,
    thumb_url: null,
    cull_reason: null,
    is_reviewed: false,
    review_decision: null,
  },
];

// Total frame count for the job (sum of segment frame_counts).
export const MOCK_TOTAL_FRAMES = MOCK_SEGMENTS.reduce((sum, s) => sum + s.frame_count, 0);

// ─── Frames (clip_frames table) ──────────────────────────────────────────────

export type BoundingBox = {
  x: number;
  y: number;
  width: number;
  height: number;
};

export type Keypoint = {
  name: string;
  x: number;
  y: number;
  confidence: number;
};

export type ClipFrame = {
  id: string;
  clip_id: string;
  frame_idx: number;
  file_url: string | null;
  motion_score: number;
  person_detected: boolean;
  person_bbox: BoundingBox | null;
  arm_keypoints: Keypoint[];
  blur_score: number;
  brightness: number;
};

// Generate a deterministic mock frame for a given segment and frame index.
// Frame image is null (rendered as a gray placeholder in FramePlayer);
// bbox and keypoints are populated so Konva overlay logic is exercised.
export function mockFrameForIndex(segmentId: string, frameIdx: number): ClipFrame {
  const hasPerson = !segmentId.includes("07"); // seg-07 has no person
  const jitter = (frameIdx % 10) * 2;

  return {
    id: `frame-${segmentId}-${frameIdx}`,
    clip_id: `clip-${segmentId}`,
    frame_idx: frameIdx,
    file_url: null,
    motion_score: 0.3 + (frameIdx % 5) * 0.1,
    person_detected: hasPerson,
    person_bbox: hasPerson
      ? { x: 180 + jitter, y: 90 + jitter / 2, width: 240, height: 300 }
      : null,
    arm_keypoints: hasPerson
      ? [
          { name: "left_shoulder", x: 220 + jitter, y: 140, confidence: 0.92 },
          { name: "left_elbow", x: 200 + jitter, y: 220, confidence: 0.88 },
          { name: "left_wrist", x: 210 + jitter, y: 300, confidence: 0.81 },
          { name: "right_shoulder", x: 380 - jitter, y: 140, confidence: 0.93 },
          { name: "right_elbow", x: 400 - jitter, y: 220, confidence: 0.85 },
          { name: "right_wrist", x: 390 - jitter, y: 300, confidence: 0.79 },
        ]
      : [],
    blur_score: 0.05 + (frameIdx % 3) * 0.02,
    brightness: 0.6,
  };
}

// Thumbnail grid for FilmstripScrubber — one thumbnail per N frames.
export function mockFilmstripThumbnails(
  segmentId: string,
  frameCount: number,
  stride: number = 5
) {
  const thumbs = [];
  for (let i = 0; i < frameCount; i += stride) {
    thumbs.push({
      frame_idx: i,
      url: null,
      segmentId,
    });
  }
  return thumbs;
}

// ─── Processing job (processing_jobs table) ──────────────────────────────────

export type ProcessingJob = {
  id: string;
  status: "processing" | "ready" | "failed";
  step: string;
  step_pct: number;
  filename: string;
  input_type: "video" | "sequence";
};

export const MOCK_JOB: ProcessingJob = {
  id: "job-001",
  status: "ready",
  step: "segmentation_complete",
  step_pct: 100,
  filename: "kitchen_fold_demo_01.mp4",
  input_type: "video",
};

// ─── Annotation draft state (builds up across review/annotate/export) ────────

export type ActionSegmentDraft = {
  segmentId: string;
  startFrame: number;
  endFrame: number;
  actionLabel: string | null;
  languageInstruction: string;
  taskPlan: string[];
};

export const MOCK_DRAFT_SEGMENTS: ActionSegmentDraft[] = [
  {
    segmentId: "seg-01",
    startFrame: 0,
    endFrame: 89,
    actionLabel: null,
    languageInstruction: "",
    taskPlan: [],
  },
  {
    segmentId: "seg-03",
    startFrame: 150,
    endFrame: 299,
    actionLabel: null,
    languageInstruction: "",
    taskPlan: [],
  },
  {
    segmentId: "seg-06",
    startFrame: 420,
    endFrame: 569,
    actionLabel: null,
    languageInstruction: "",
    taskPlan: [],
  },
  {
    segmentId: "seg-08",
    startFrame: 630,
    endFrame: 749,
    actionLabel: null,
    languageInstruction: "",
    taskPlan: [],
  },
];
