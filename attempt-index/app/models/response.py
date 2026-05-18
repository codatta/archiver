from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class NearestPrior(BaseModel):
    submission_id: str
    match_key: str
    similarity: float
    submitted_at: datetime
    state: str | None = None


class EvaluateResponse(BaseModel):
    attempt_index: int
    cut_off_reached: bool
    cut_off_limit: int
    nearest_prior: list[NearestPrior]
    uniqueness_scope: str
    uniqueness_version: str
    processing_stage: Literal["complete", "partial"] = "complete"
    match_key: str
    error: str | None = None


class BootstrapResponse(BaseModel):
    inserted: int
    skipped: int


class FrontierResponse(BaseModel):
    frontier_id: str
    name: str
    description: str | None = None
    created_at: datetime
