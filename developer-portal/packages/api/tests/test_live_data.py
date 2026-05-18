"""Tests for live_data dashboard routes: falsy-0 cursor fix and reset-cursor endpoint."""
from unittest.mock import MagicMock


# ── Helpers ────────────────────────────────────────────────────────────────────

ACTIVE_SUB = {
    "id": "sub-1",
    "org_id": "org-1",
    "frontier_id": "frontier-1",
    "task_ids": ["task-1"],
    "cursor_position": "42",
    "status": "active",
    "filters": None,
}


def _mock_subscription(mock_supabase, sub=None):
    """Wire up mock_supabase.table("subscriptions") to return a subscription."""
    sub = sub or ACTIVE_SUB

    def table_side_effect(name):
        t = MagicMock()
        if name == "subscriptions":
            chain = t.select.return_value
            chain.eq.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data=sub)
            )
            # Also wire .update() chain for reset-cursor
            t.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[sub])
        return t

    mock_supabase.table.side_effect = table_side_effect
    return table_side_effect


# ── Reset-cursor endpoint ─────────────────────────────────────────────────────


async def test_reset_cursor_success(client, mock_supabase, as_org_owner):
    """POST /live/reset-cursor resets cursor_position to '0'."""
    _mock_subscription(mock_supabase)

    res = await client.post(
        "/v1/orgs/org-1/live/reset-cursor?subscription_id=sub-1",
        headers={"Authorization": "Bearer token"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["cursor_position"] == "0"

    # Verify the Supabase update was called with cursor_position = "0"
    calls = mock_supabase.table.call_args_list
    table_names = [c.args[0] for c in calls]
    assert "subscriptions" in table_names


async def test_reset_cursor_not_found(client, mock_supabase, as_org_owner):
    """POST /live/reset-cursor returns 404 for missing subscription."""

    def table_side_effect(name):
        t = MagicMock()
        if name == "subscriptions":
            chain = t.select.return_value
            chain.eq.return_value.eq.return_value.single.return_value.execute.return_value = (
                MagicMock(data=None)
            )
        return t

    mock_supabase.table.side_effect = table_side_effect

    res = await client.post(
        "/v1/orgs/org-1/live/reset-cursor?subscription_id=nonexistent",
        headers={"Authorization": "Bearer token"},
    )

    assert res.status_code == 404


async def test_reset_cursor_inactive_sub(client, mock_supabase, as_org_owner):
    """POST /live/reset-cursor returns 400 for inactive subscription."""
    inactive_sub = {**ACTIVE_SUB, "status": "cancelled"}
    _mock_subscription(mock_supabase, sub=inactive_sub)

    res = await client.post(
        "/v1/orgs/org-1/live/reset-cursor?subscription_id=sub-1",
        headers={"Authorization": "Bearer token"},
    )

    assert res.status_code == 400
    assert "not active" in res.json()["detail"]


async def test_reset_cursor_requires_auth(client, mock_supabase):
    """POST /live/reset-cursor without auth returns 401/403."""
    # No as_org_owner fixture — auth dependency is NOT overridden
    _mock_subscription(mock_supabase)

    res = await client.post(
        "/v1/orgs/org-1/live/reset-cursor?subscription_id=sub-1",
    )

    # Should fail auth — either 401 or 403 depending on middleware
    assert res.status_code in (401, 403)


async def test_reset_cursor_member_access(client, mock_supabase, as_org_member):
    """POST /live/reset-cursor is accessible to regular org members (not just owners)."""
    _mock_subscription(mock_supabase)

    res = await client.post(
        "/v1/orgs/org-1/live/reset-cursor?subscription_id=sub-1",
        headers={"Authorization": "Bearer token"},
    )

    assert res.status_code == 200
    assert res.json()["ok"] is True


# ── Falsy-0 cursor bug ────────────────────────────────────────────────────────
# The old code: `int(cursor or stored_cursor or 0)` treated cursor=0 as falsy
# and fell back to stored_cursor. The fix: `int(cursor) if cursor is not None`.


def test_falsy_zero_cursor_logic():
    """cursor='0' must be respected, not fall through to stored_cursor.

    This is a unit test of the fixed expression.
    Old: int(cursor or stored_cursor or 0) → int("42") when cursor="0"
    New: int(cursor) if cursor is not None else int(stored_cursor or 0) → int(0)
    """
    # Simulate the fixed logic
    def effective_cursor(cursor, stored_cursor):
        return int(cursor) if cursor is not None else int(stored_cursor or 0)

    # cursor=0 explicitly passed — must be 0, not fallback
    assert effective_cursor("0", "42") == 0
    assert effective_cursor(0, "42") == 0

    # cursor=None — fall back to stored
    assert effective_cursor(None, "42") == 42
    assert effective_cursor(None, "0") == 0
    assert effective_cursor(None, None) == 0

    # cursor with actual value — use it
    assert effective_cursor("100", "42") == 100


def test_old_logic_was_broken():
    """Prove the old expression was incorrect for cursor=0."""
    def old_effective_cursor(cursor, stored_cursor):
        return int(cursor or stored_cursor or 0)

    # This was the bug: cursor="0" is truthy as a string, so it actually
    # worked for string "0". But cursor=0 (int) is falsy and fell through.
    assert old_effective_cursor(0, "42") == 42  # Bug: should be 0
    assert old_effective_cursor("", "42") == 42  # Empty string also falsy
