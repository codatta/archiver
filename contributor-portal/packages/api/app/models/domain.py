"""Domain models for the Humanbased Contributor Portal.

These mirror the TypeScript types in packages/shared/types/index.ts
and map 1:1 to the Supabase tables defined in sql-query/migrations/.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import (
    CampaignStatus,
    InstanceStatus,
    JobStatus,
    QualityGrade,
    SegmentState,
    TaskExecution,
    TaskOrigin,
)

# ─── Campaign Framework ──────────────────────────────────────────────────────


class Campaign(BaseModel):
    id: UUID
    org_id: UUID | None = None
    frontier_id: str
    template_id: str
    name: str
    status: CampaignStatus = CampaignStatus.DRAFT
    annotation_config: str | None = None
    params: dict = Field(default_factory=dict)
    created_at: datetime


class Task(BaseModel):
    id: UUID
    campaign_id: UUID
    task_key: str
    name: str
    origin: TaskOrigin
    execution: TaskExecution
    annotation_config: str | None = None
    ml_backend_url: str | None = None
    config: dict = Field(default_factory=dict)
    depends_on: list[UUID] = Field(default_factory=list)
    position: int


class TaskInstance(BaseModel):
    id: UUID
    task_id: UUID
    campaign_id: UUID
    parent_instances: list[UUID] = Field(default_factory=list)
    content_hash: str | None = None
    annotation_config_ver: str | None = None
    contributor_id: UUID | None = None
    quality_grade: QualityGrade | None = None
    status: InstanceStatus = InstanceStatus.PENDING
    payload: dict | None = None
    submitted_at: datetime | None = None
    validated_at: datetime | None = None
    created_at: datetime


# ─── Vision Processing ────────────────────────────────────────────────────────


class ProcessingJob(BaseModel):
    id: UUID
    t1_instance_id: UUID
    campaign_id: UUID
    filename: str
    task_name: str | None = None
    scenario_code: str = "SCENE_01"
    status: JobStatus = JobStatus.PROCESSING
    step: str = "upload"
    step_pct: int = 0
    input_type: str | None = None
    file_hash: str | None = None
    compress_px: int = 0
    detection_params: dict | None = None
    result: dict | None = None
    created_at: datetime


class Clip(BaseModel):
    id: UUID
    job_id: UUID
    t2_instance_id: UUID | None = None
    start_idx: int
    end_idx: int
    start_ms: int
    end_ms: int
    start_ns: int | None = None
    end_ns: int | None = None
    fps: float
    thumb_url: str | None = None
    blur_score: float | None = None
    brightness: float | None = None
    frame_count: int
    actions: list | None = None


class ClipFrame(BaseModel):
    id: UUID
    clip_id: UUID
    frame_idx: int
    file_url: str
    timestamp_ns: int | None = None
    motion_score: float | None = None
    person_detected: bool | None = None
    person_bbox: dict | None = None
    arm_keypoints: list[dict] | None = None
    hand_activity_score: float | None = None
    blur_score: float | None = None
    brightness: float | None = None


class Segment(BaseModel):
    id: UUID
    job_id: UUID
    state: SegmentState
    start_idx: int
    end_idx: int
    frame_count: int
    duration_ms: int
    thumb_url: str | None = None
    cull_reason: str | None = None
    is_reviewed: bool = False
    review_decision: str | None = None


# ─── Embodiment-X Annotation ──────────────────────────────────────────────────


class BoundingBox(BaseModel):
    label: str
    x: float
    y: float
    w: float
    h: float
    confidence: float | None = None


class Keypoint(BaseModel):
    label: str
    x: float
    y: float
    confidence: float | None = None


class ActionSegment(BaseModel):
    id: str
    start_ns: int
    end_ns: int
    action_label: str
    language_instruction: str | None = None
    task_plan: list[str] | None = None


class FrameSpatial(BaseModel):
    frame_idx: int
    timestamp_ns: int | None = None
    bounding_boxes: list[BoundingBox] = Field(default_factory=list)
    keypoints: list[Keypoint] = Field(default_factory=list)


class QualityMetadata(BaseModel):
    blur_score: float | None = None
    brightness: float | None = None
    person_detected: bool | None = None
    hand_activity_score: float | None = None


class Annotation(BaseModel):
    id: UUID
    t3_instance_id: UUID
    job_id: UUID
    temporal: dict  # {segments: ActionSegment[]}
    spatial: dict | None = None  # {frames: FrameSpatial[]}
    quality_metadata: dict | None = None
    created_at: datetime


# ─── Contributors ─────────────────────────────────────────────────────────────


class Contributor(BaseModel):
    id: UUID
    display_name: str | None = None
    email: str | None = None
    wallet_address: str | None = None
    reputation_score: float = 0.0
    created_at: datetime


# ─── Lineage ──────────────────────────────────────────────────────────────────


class UpstreamShares(BaseModel):
    self_bps: int
    platform_bps: int
    parents: list[dict] = Field(default_factory=list)  # [{id, bps}]


class LineageStagingRecord(BaseModel):
    instance_id: UUID
    contributor_did: str | None = None
    campaign_id: UUID
    task_id: UUID
    frontier_id: str
    parent_instances: list[UUID] = Field(default_factory=list)
    content_hash: str | None = None
    annotation_config_ver: str | None = None
    compensation_model: str = "fixed"
    upstream_shares: dict | None = None
    quality_grade: QualityGrade | None = None
    staged_at: datetime
    staging_status: str = "mock_committed"
