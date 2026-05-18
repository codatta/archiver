"""Tests for API key authentication middleware."""
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.apikey_auth import check_subscription_scope

VALID_KEY = "hb_live_sk_abc123xyz456"
KEY_HASH = "placeholder"  # will be computed by the middleware


def make_key_record(status="active", expires_at=None, subscription_ids=None):
    return {
        "id": "key-1",
        "org_id": "org-1",
        "name": "Test Key",
        "key_hash": KEY_HASH,
        "key_prefix": VALID_KEY[:20],
        "status": status,
        "expires_at": expires_at,
        "last_used_at": None,
        "subscription_ids": subscription_ids,
    }


async def test_verify_key_success(client, mock_supabase):
    """Valid key returns 200 with org info."""
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=make_key_record()
    )
    mock_supabase.table.return_value.update.return_value \
        .eq.return_value.execute.return_value = MagicMock(data=[{}])

    res = await client.post(
        "/v1/auth/verify-key",
        headers={"Authorization": f"Bearer {VALID_KEY}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["org_id"] == "org-1"
    assert data["key_name"] == "Test Key"


async def test_verify_key_missing_header(client, mock_supabase):
    """No Authorization header returns 401."""
    res = await client.post("/v1/auth/verify-key")
    assert res.status_code == 401


async def test_verify_key_malformed(client, mock_supabase):
    """Key not starting with hb_live_sk_ returns 401."""
    res = await client.post(
        "/v1/auth/verify-key",
        headers={"Authorization": "Bearer bad_prefix_key"},
    )
    assert res.status_code == 401


async def test_verify_key_not_found(client, mock_supabase):
    """Key hash not in DB returns 401."""
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=None
    )

    res = await client.post(
        "/v1/auth/verify-key",
        headers={"Authorization": f"Bearer {VALID_KEY}"},
    )
    assert res.status_code == 401


async def test_verify_key_revoked(client, mock_supabase):
    """Revoked key returns 401."""
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=make_key_record(status="revoked")
    )

    res = await client.post(
        "/v1/auth/verify-key",
        headers={"Authorization": f"Bearer {VALID_KEY}"},
    )
    assert res.status_code == 401


async def test_verify_key_expired(client, mock_supabase):
    """Expired key returns 401."""
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=make_key_record(expires_at="2020-01-01T00:00:00Z")
    )

    res = await client.post(
        "/v1/auth/verify-key",
        headers={"Authorization": f"Bearer {VALID_KEY}"},
    )
    assert res.status_code == 401


# -- Subscription scope enforcement tests --


def test_scope_allows_matching_subscription():
    """Scoped key allows access to a subscription in its scope."""
    key_info = {"subscription_ids": ["sub-1", "sub-2"]}
    check_subscription_scope(key_info, "sub-1")  # Should not raise


def test_scope_rejects_non_matching_subscription():
    """Scoped key rejects access to a subscription not in scope."""
    key_info = {"subscription_ids": ["sub-1", "sub-2"]}
    with pytest.raises(HTTPException) as exc_info:
        check_subscription_scope(key_info, "sub-999")
    assert exc_info.value.status_code == 403


def test_scope_null_allows_all():
    """Null subscription_ids allows access to any subscription."""
    key_info = {"subscription_ids": None}
    check_subscription_scope(key_info, "sub-anything")


def test_scope_missing_key_allows_all():
    """Missing subscription_ids key allows access (backward compat)."""
    key_info = {}
    check_subscription_scope(key_info, "sub-anything")
