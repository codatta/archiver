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


async def test_create_subscription(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
        data=[{
            "id": "sub-1", "org_id": "org-1",
            "vertical_id": "vert-1",
            "topic_ids": ["topic-1"],
            "delivery_mode": "pull",
            "status": "active",
        }]
    )

    res = await client.post(
        "/v1/orgs/org-1/subscriptions",
        json={
            "vertical_id": "vert-1",
            "topic_ids": ["topic-1"],
            "delivery_mode": "pull",
        },
        headers=AUTH_HEADERS,
    )

    assert res.status_code == 200
    data = res.json()["data"]
    assert data["vertical_id"] == "vert-1"
    assert data["status"] == "active"


async def test_list_subscriptions(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.order.return_value.execute.return_value = MagicMock(
        data=[
            {"id": "sub-1", "vertical_id": "vert-1", "status": "active"},
            {"id": "sub-2", "vertical_id": "vert-2", "status": "cancelled"},
        ]
    )

    res = await client.get("/v1/orgs/org-1/subscriptions", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2


async def test_update_subscription_filters(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "sub-1", "auto_accept": True}]
    )

    res = await client.patch(
        "/v1/orgs/org-1/subscriptions/sub-1",
        json={"auto_accept": True},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200


async def test_cancel_subscription(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "sub-1", "status": "cancelled"}]
    )

    res = await client.post(
        "/v1/orgs/org-1/subscriptions/sub-1/cancel",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "cancelled"


async def test_cancel_nonexistent(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.eq.return_value.execute.return_value = MagicMock(data=[])

    res = await client.post(
        "/v1/orgs/org-1/subscriptions/fake/cancel",
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 404
