from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class AdapterConfig(BaseModel):
    canonical_fields: list[str] | None = None


class MatcherConfig(BaseModel):
    methodology: Literal["hash"] = "hash"
    adapter_config: AdapterConfig = Field(default_factory=AdapterConfig)


class EvaluateRequest(BaseModel):
    task_id: str
    sample_key: str
    submission_id: str
    payload_type: Literal["structured", "text"]
    submitted_at: datetime
    uniqueness_scope: Literal["task", "campaign", "frontier", "global"] = "campaign"
    max_attempts: int = Field(ge=1)
    matcher_config: MatcherConfig = Field(default_factory=MatcherConfig)

    # Either payload or match_key must be provided
    payload: dict[str, Any] | str | None = None
    match_key: str | None = None

    campaign_id: str | None = None
    contributor_uid: str | None = None
    uniqueness_version: str = "v1"

    @model_validator(mode="after")
    def require_payload_or_match_key(self) -> "EvaluateRequest":
        if self.payload is None and self.match_key is None:
            raise ValueError("Either 'payload' or 'match_key' must be provided")
        return self

    @model_validator(mode="after")
    def require_campaign_id_for_campaign_scope(self) -> "EvaluateRequest":
        if self.uniqueness_scope == "campaign" and not self.campaign_id:
            raise ValueError("campaign_id is required when uniqueness_scope is 'campaign'")
        return self


class BootstrapRecord(BaseModel):
    task_id: str
    sample_key: str
    submission_id: str = Field(pattern=r"^bootstrap:")
    payload_type: Literal["structured", "text"]
    match_key: str
    submitted_at: datetime
    uniqueness_scope: Literal["task", "campaign", "frontier", "global"] = "campaign"
    uniqueness_version: str = "v1"
    campaign_id: str | None = None
    contributor_uid: str | None = None
    frontier_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def require_campaign_id_for_campaign_scope(self) -> "BootstrapRecord":
        if self.uniqueness_scope == "campaign" and not self.campaign_id:
            raise ValueError("campaign_id is required when uniqueness_scope is 'campaign'")
        return self


class BootstrapRequest(BaseModel):
    records: list[BootstrapRecord] = Field(min_length=1)


class FrontierCreate(BaseModel):
    frontier_id: str
    name: str
    description: str | None = None
