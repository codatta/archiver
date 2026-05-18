from unittest.mock import MagicMock

import pytest


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = "user-123"
    user.email = "test@example.com"
    return user


@pytest.fixture
def mock_session():
    session = MagicMock()
    session.access_token = "test-access-token"
    session.refresh_token = "test-refresh-token"
    session.expires_at = 1700000000
    return session


async def test_signup_endpoint_removed(client, mock_supabase):
    """POST /v1/auth/signup was removed — signup uses Supabase OTP client-side."""
    res = await client.post(
        "/v1/auth/signup",
        json={"email": "test@example.com", "password": "strongpass123", "full_name": "Test User"},
    )
    assert res.status_code in (404, 405)


async def test_signin_success(client, mock_supabase, mock_user, mock_session):
    mock_result = MagicMock()
    mock_result.user = mock_user
    mock_result.session = mock_session
    mock_supabase.auth.sign_in_with_password.return_value = mock_result

    res = await client.post(
        "/v1/auth/signin",
        json={"email": "test@example.com", "password": "strongpass123"},
    )

    assert res.status_code == 200
    data = res.json()
    assert data["user"]["id"] == "user-123"
    assert data["session"]["access_token"] == "test-access-token"
    assert data["session"]["refresh_token"] == "test-refresh-token"


async def test_signin_invalid_creds(client, mock_supabase):
    mock_supabase.auth.sign_in_with_password.side_effect = Exception("Invalid login credentials")

    res = await client.post(
        "/v1/auth/signin",
        json={"email": "test@example.com", "password": "wrongpass"},
    )

    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


async def test_signin_invalid_email_format(client, mock_supabase):
    res = await client.post(
        "/v1/auth/signin",
        json={"email": "bad-email", "password": "somepass"},
    )
    assert res.status_code == 422
