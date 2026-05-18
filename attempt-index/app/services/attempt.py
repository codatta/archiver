import logging

from supabase import Client

from app.db.queries import (
    frontier_exists,
    get_by_submission_id,
    insert_record,
    query_prior_matches,
    tag_record_frontiers,
    upsert_bootstrap_records,
)
from app.matchers.hash_matcher import get_matcher
from app.models.request import BootstrapRecord, EvaluateRequest
from app.models.response import BootstrapResponse, EvaluateResponse, NearestPrior

logger = logging.getLogger(__name__)

_FAIL_OPEN_RESPONSE_FIELDS = {
    "attempt_index": 1,
    "cut_off_reached": False,
    "nearest_prior": [],
    "processing_stage": "partial",
}


def _build_nearest_prior(record: dict) -> NearestPrior:
    return NearestPrior(
        submission_id=record["submission_id"],
        match_key=record["match_key"],
        similarity=1.0,  # hash methodology: exact match = 1.0
        submitted_at=record["submitted_at"],
        state=None,
    )


def evaluate(client: Client, req: EvaluateRequest) -> EvaluateResponse:
    try:
        return _evaluate_inner(client, req)
    except Exception as exc:
        logger.exception("AttemptIndex evaluate failed — failing open: %s", exc)
        return EvaluateResponse(
            **_FAIL_OPEN_RESPONSE_FIELDS,
            cut_off_limit=req.max_attempts,
            uniqueness_scope=req.uniqueness_scope,
            uniqueness_version=req.uniqueness_version,
            match_key=req.match_key or "",
            error=str(exc),
        )


def _evaluate_inner(client: Client, req: EvaluateRequest) -> EvaluateResponse:
    # 1. Idempotency check — if submission_id already exists, reconstruct from stored record
    existing = get_by_submission_id(client, req.submission_id)
    if existing:
        prior_matches = query_prior_matches(
            client,
            task_id=req.task_id,
            sample_key=req.sample_key,
            match_key=existing["match_key"],
            uniqueness_scope=req.uniqueness_scope,
            campaign_id=req.campaign_id,
            exclude_submission_id=req.submission_id,
        )
        nearest = prior_matches[-1] if prior_matches else None
        stored_index = existing["attempt_index"]
        return EvaluateResponse(
            attempt_index=stored_index,
            cut_off_reached=stored_index >= req.max_attempts,
            cut_off_limit=req.max_attempts,
            nearest_prior=[_build_nearest_prior(nearest)] if nearest else [],
            uniqueness_scope=req.uniqueness_scope,
            uniqueness_version=existing["uniqueness_version"],
            processing_stage="complete",
            match_key=existing["match_key"],
        )

    # 2. Compute match_key
    matcher = get_matcher(req.matcher_config)
    if req.match_key:
        match_key = req.match_key
    else:
        match_key = matcher.compute_match_key(req.payload)

    # 3. Query prior matching records
    prior_matches = query_prior_matches(
        client,
        task_id=req.task_id,
        sample_key=req.sample_key,
        match_key=match_key,
        uniqueness_scope=req.uniqueness_scope,
        campaign_id=req.campaign_id,
    )

    # 4. Assign attempt_index
    attempt_index = len(prior_matches) + 1
    cut_off_reached = attempt_index >= req.max_attempts

    # 5. Write new record
    insert_record(
        client,
        submission_id=req.submission_id,
        task_id=req.task_id,
        sample_key=req.sample_key,
        contributor_uid=req.contributor_uid,
        match_key=match_key,
        payload_type=req.payload_type,
        submitted_at=req.submitted_at,
        uniqueness_version=req.uniqueness_version,
        uniqueness_scope=req.uniqueness_scope,
        campaign_id=req.campaign_id,
        attempt_index=attempt_index,
    )

    # 6. Build nearest_prior (most recent matching record)
    nearest = prior_matches[-1] if prior_matches else None

    return EvaluateResponse(
        attempt_index=attempt_index,
        cut_off_reached=cut_off_reached,
        cut_off_limit=req.max_attempts,
        nearest_prior=[_build_nearest_prior(nearest)] if nearest else [],
        uniqueness_scope=req.uniqueness_scope,
        uniqueness_version=req.uniqueness_version,
        processing_stage="complete",
        match_key=match_key,
    )


def bootstrap(client: Client, records: list[BootstrapRecord]) -> BootstrapResponse:
    # Validate all frontier_ids before writing anything
    all_frontier_ids = {fid for r in records for fid in r.frontier_ids}
    for fid in all_frontier_ids:
        if not frontier_exists(client, fid):
            raise ValueError(f"frontier_id '{fid}' does not exist")

    rows = [
        {
            "submission_id": r.submission_id,
            "task_id": r.task_id,
            "sample_key": r.sample_key,
            "contributor_uid": r.contributor_uid,
            "match_key": r.match_key,
            "payload_type": r.payload_type,
            "submitted_at": r.submitted_at.isoformat(),
            "uniqueness_version": r.uniqueness_version,
            "uniqueness_scope": r.uniqueness_scope,
            "campaign_id": r.campaign_id,
            "attempt_index": 1,
        }
        for r in records
    ]
    inserted, skipped = upsert_bootstrap_records(client, rows)

    # tag_record_frontiers is idempotent — safe to call for all records including skipped ones
    for r in records:
        if r.frontier_ids:
            tag_record_frontiers(client, r.submission_id, r.frontier_ids)

    return BootstrapResponse(inserted=inserted, skipped=skipped)
