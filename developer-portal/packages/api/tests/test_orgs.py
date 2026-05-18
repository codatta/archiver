from unittest.mock import MagicMock

AUTH_HEADERS = {"Authorization": "Bearer valid-token"}


def setup_auth(mock_supabase):
    mock_supabase.auth.get_user.side_effect = None
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "admin@example.com"
    mock_user.email_confirmed_at = "2026-01-01T00:00:00Z"
    mock_user.user_metadata = {}
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result


async def test_get_org(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data={"id": "org-1", "name": "Acme", "slug": "acme"}
    )

    res = await client.get("/v1/orgs/org-1", headers=AUTH_HEADERS)
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Acme"


async def test_get_org_not_found(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.select.return_value
    chain.eq.return_value.single.return_value.execute.return_value = MagicMock(data=None)

    res = await client.get("/v1/orgs/fake", headers=AUTH_HEADERS)
    assert res.status_code == 404


async def test_update_org(client, mock_supabase, as_org_owner):
    setup_auth(mock_supabase)
    chain = mock_supabase.table.return_value.update.return_value
    chain.eq.return_value.execute.return_value = MagicMock(
        data=[{"id": "org-1", "name": "Acme Updated", "slug": "acme"}]
    )

    res = await client.patch(
        "/v1/orgs/org-1",
        json={"name": "Acme Updated", "slug": "acme"},
        headers=AUTH_HEADERS,
    )
    assert res.status_code == 200
    assert res.json()["data"]["name"] == "Acme Updated"
