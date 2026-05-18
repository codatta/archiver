from unittest.mock import MagicMock

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase):
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "dev@example.com"
    mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
    mock_user.user_metadata = {}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


def _setup_create_key(mock_supabase, valid_sub_ids, created_key_data=None):
    """Set up mocks for the create_key handler."""
    if created_key_data is None:
        created_key_data = {
            "id": "key-1", "org_id": "org-1", "name": "Prod",
            "key_prefix": "hb_live_sk_xxxx", "status": "active",
            "subscription_ids": valid_sub_ids,
        }

    def table_router(name):
        m = MagicMock()
        if name == "subscriptions":
            m.select.return_value.eq.return_value.eq.return_value \
                .execute.return_value = MagicMock(
                data=[{"id": sid} for sid in valid_sub_ids]
            )
        elif name == "api_keys":
            m.insert.return_value.execute.return_value = MagicMock(
                data=[created_key_data]
            )
        return m

    mock_supabase.table.side_effect = table_router


def _cleanup_side_effect(mock_supabase):
    mock_supabase.table.side_effect = None


async def test_create_key(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    _setup_create_key(mock_supabase, ["sub-1", "sub-2"])

    res = await client.post(
        "/v1/orgs/org-1/keys",
        json={
            "name": "Prod",
            "expires_in_days": 90,
            "subscription_ids": ["sub-1"],
        },
        headers=AUTH_HEADERS,
    )
    _cleanup_side_effect(mock_supabase)

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["raw_key"].startswith("hb_live_sk_")
    assert data["name"] == "Prod"


async def test_create_key_no_expiry(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    _setup_create_key(mock_supabase, ["sub-1"])

    res = await client.post(
        "/v1/orgs/org-1/keys",
        json={
            "name": "CI",
            "expires_in_days": None,
            "subscription_ids": ["sub-1"],
        },
        headers=AUTH_HEADERS,
    )
    _cleanup_side_effect(mock_supabase)

    assert res.status_code == 200


async def test_create_key_empty_subscription_ids(client, mock_supabase, as_org_owner):
    """Empty subscription_ids should fail with 422."""
    setup_auth(mock_supabase)
    _setup_create_key(mock_supabase, ["sub-1"])

    res = await client.post(
        "/v1/orgs/org-1/keys",
        json={"name": "Empty", "subscription_ids": []},
        headers=AUTH_HEADERS,
    )
    _cleanup_side_effect(mock_supabase)

    assert res.status_code == 422


async def test_create_key_missing_subscription_ids(client, mock_supabase, as_org_owner):
    """Missing subscription_ids field should fail with 422."""
    setup_auth(mock_supabase)

    res = await client.post(
        "/v1/orgs/org-1/keys",
        json={"name": "NoScope"},
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 422


async def test_create_key_invalid_subscription_id(client, mock_supabase, as_org_owner):
    """subscription_id not belonging to org should fail with 403."""
    setup_auth(mock_supabase)
    _setup_create_key(mock_supabase, ["sub-1"])

    res = await client.post(
        "/v1/orgs/org-1/keys",
        json={
            "name": "Bad",
            "subscription_ids": ["sub-1", "sub-999"],
        },
        headers=AUTH_HEADERS,
    )
    _cleanup_side_effect(mock_supabase)

    assert res.status_code == 403
    assert "sub-999" in res.json()["detail"]


async def test_list_keys(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[
            {
                "id": "key-1", "name": "Prod",
                "key_prefix": "hb_live_sk_xxxx",
                "status": "active", "created_by": None,
            },
            {
                "id": "key-2", "name": "CI",
                "key_prefix": "hb_live_sk_yyyy",
                "status": "revoked", "created_by": None,
            },
        ]
    )

    res = await client.get("/v1/orgs/org-1/keys", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2


async def test_revoke_key(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "key-1", "status": "revoked"}]
    )

    res = await client.post(
        "/v1/orgs/org-1/keys/key-1/revoke",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "revoked"


async def test_revoke_nonexistent_key(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[]
    )

    res = await client.post(
        "/v1/orgs/org-1/keys/fake-id/revoke",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 404
