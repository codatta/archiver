from datetime import datetime
from typing import Any

from supabase import Client

TABLE = "attempt_records"
FRONTIERS_TABLE = "frontiers"
RECORD_FRONTIERS_TABLE = "record_frontiers"


def get_by_submission_id(client: Client, submission_id: str) -> dict[str, Any] | None:
    result = (
        client.table(TABLE)
        .select("*")
        .eq("submission_id", submission_id)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


def query_prior_matches(
    client: Client,
    *,
    task_id: str,
    sample_key: str,
    match_key: str,
    uniqueness_scope: str,
    campaign_id: str | None = None,
    exclude_submission_id: str | None = None,
) -> list[dict[str, Any]]:
    """
    Fetch all prior records with the same match_key within the scope.
    Ordered by submitted_at ascending (oldest first).
    """
    q = client.table(TABLE).select("*")

    if uniqueness_scope == "task":
        q = q.eq("task_id", task_id).eq("sample_key", sample_key).eq("match_key", match_key)
    elif uniqueness_scope == "campaign":
        # Isolated per campaign_id — does not bleed across campaigns.
        q = (
            q.eq("campaign_id", campaign_id)
            .eq("sample_key", sample_key)
            .eq("match_key", match_key)
        )
    elif uniqueness_scope == "frontier":
        q = (
            q.eq("uniqueness_scope", "frontier")
            .eq("sample_key", sample_key)
            .eq("match_key", match_key)
        )
    else:  # global
        q = q.eq("sample_key", sample_key).eq("match_key", match_key)

    if exclude_submission_id:
        q = q.neq("submission_id", exclude_submission_id)

    result = q.order("submitted_at", desc=False).execute()
    return result.data or []


def insert_record(
    client: Client,
    *,
    submission_id: str,
    task_id: str,
    sample_key: str,
    contributor_uid: str | None,
    match_key: str,
    payload_type: str,
    submitted_at: datetime,
    uniqueness_version: str,
    uniqueness_scope: str,
    campaign_id: str | None,
    attempt_index: int,
) -> None:
    client.table(TABLE).insert(
        {
            "submission_id": submission_id,
            "task_id": task_id,
            "sample_key": sample_key,
            "contributor_uid": contributor_uid,
            "match_key": match_key,
            "payload_type": payload_type,
            "submitted_at": submitted_at.isoformat(),
            "uniqueness_version": uniqueness_version,
            "uniqueness_scope": uniqueness_scope,
            "campaign_id": campaign_id,
            "attempt_index": attempt_index,
        }
    ).execute()


def upsert_bootstrap_records(
    client: Client, records: list[dict[str, Any]]
) -> tuple[int, int]:
    """
    Insert bootstrap records, skipping any with existing submission_ids.
    Returns (inserted, skipped).
    """
    if not records:
        return 0, 0

    ids = [r["submission_id"] for r in records]
    existing_result = (
        client.table(TABLE).select("submission_id").in_("submission_id", ids).execute()
    )
    existing_ids = {row["submission_id"] for row in (existing_result.data or [])}

    to_insert = [r for r in records if r["submission_id"] not in existing_ids]
    skipped = len(records) - len(to_insert)

    if to_insert:
        client.table(TABLE).insert(to_insert).execute()

    return len(to_insert), skipped


# ---------------------------------------------------------------------------
# Frontier helpers
# ---------------------------------------------------------------------------


def create_frontier(
    client: Client, *, frontier_id: str, name: str, description: str | None
) -> dict[str, Any]:
    result = (
        client.table(FRONTIERS_TABLE)
        .insert({"frontier_id": frontier_id, "name": name, "description": description})
        .execute()
    )
    return result.data[0]


def frontier_exists(client: Client, frontier_id: str) -> bool:
    result = (
        client.table(FRONTIERS_TABLE)
        .select("frontier_id")
        .eq("frontier_id", frontier_id)
        .limit(1)
        .execute()
    )
    return bool(result.data)


def list_frontiers(client: Client) -> list[dict[str, Any]]:
    result = (
        client.table(FRONTIERS_TABLE)
        .select("*")
        .order("created_at", desc=False)
        .execute()
    )
    return result.data or []


def tag_record_frontiers(
    client: Client, submission_id: str, frontier_ids: list[str]
) -> None:
    """Insert frontier tags for a submission, skipping duplicates."""
    if not frontier_ids:
        return

    existing = (
        client.table(RECORD_FRONTIERS_TABLE)
        .select("frontier_id")
        .eq("submission_id", submission_id)
        .in_("frontier_id", frontier_ids)
        .execute()
    )
    already_tagged = {row["frontier_id"] for row in (existing.data or [])}
    to_insert = [
        {"submission_id": submission_id, "frontier_id": fid}
        for fid in frontier_ids
        if fid not in already_tagged
    ]
    if to_insert:
        client.table(RECORD_FRONTIERS_TABLE).insert(to_insert).execute()
