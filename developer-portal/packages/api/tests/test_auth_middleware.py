from unittest.mock import MagicMock


async def test_me_success(client, mock_supabase):
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_user.email = "test@example.com"
    mock_user.user_metadata = {"full_name": "Test User"}

    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_supabase.auth.get_user.return_value = mock_result

    res = await client.get("/v1/auth/me", headers={"Authorization": "Bearer valid-token"})

    assert res.status_code == 200
    data = res.json()
    assert data["user"]["id"] == "user-123"
    assert data["user"]["email"] == "test@example.com"
    mock_supabase.auth.get_user.assert_called_once_with("valid-token")


async def test_me_missing_auth_header(client, mock_supabase):
    res = await client.get("/v1/auth/me")
    assert res.status_code == 401
    assert "Authorization" in res.json()["detail"]


async def test_me_invalid_token(client, mock_supabase):
    mock_supabase.auth.get_user.side_effect = Exception("Invalid JWT")

    res = await client.get("/v1/auth/me", headers={"Authorization": "Bearer bad-token"})
    assert res.status_code == 401


async def test_me_malformed_bearer(client, mock_supabase):
    res = await client.get("/v1/auth/me", headers={"Authorization": "Basic abc"})
    assert res.status_code == 401
