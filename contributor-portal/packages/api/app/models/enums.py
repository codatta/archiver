from enum import StrEnum


class CampaignStatus(StrEnum):
    DRAFT = "draft"
    LIVE = "live"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskOrigin(StrEnum):
    MANUAL = "manual"
    AUTO_GENERATED = "auto_generated"


class TaskExecution(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class InstanceStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUBMITTED = "submitted"
    VALIDATED = "validated"
    REJECTED = "rejected"
    FAILED = "failed"


class QualityGrade(StrEnum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class SegmentState(StrEnum):
    KEEP = "keep"
    REVIEW = "review"
    CULLED_MOTION = "culled_motion"
    CULLED_LOW_ACTION = "culled_low_action"
    CULLED_PERSON = "culled_person"


class JobStatus(StrEnum):
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
