"""Tests for HuggingFace OAuth flow.

Covers: PKCE generation, signed state cookie, id_token decoding, and the
/start + /callback endpoints with mocked HF token endpoint and Supabase
admin client.
"""

import base64
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.hf_oauth import (
    STATE_MAX_AGE_SECONDS,
    decode_id_token,
    generate_pkce_pair,
    sign_state,
    verify_state,
)

# --- Unit: PKCE generation ---------------------------------------------------


def test_generate_pkce_pair_returns_verifier_and_challenge():
    verifier, challenge = generate_pkce_pair()
    assert isinstance(verifier, str)
    assert isinstance(challenge, str)
    # Code verifier must be 43-128 chars per RFC 7636
    assert 43 <= len(verifier) <= 128
    # S256 challenge is base64url-encoded SHA-256 (43 chars, no padding)
    assert len(challenge) == 43
    assert "=" not in challenge


def test_generate_pkce_pair_is_unique():
    v1, c1 = generate_pkce_pair()
    v2, c2 = generate_pkce_pair()
    assert v1 != v2
    assert c1 != c2


# --- Unit: signed state cookie ----------------------------------------------


def test_sign_state_roundtrip():
    secret = "test-secret"
    payload = {"nonce": "abc123", "verifier": "v" * 50, "return_to": "/dashboard"}
    token = sign_state(payload, secret=secret)
    decoded = verify_state(token, secret=secret)
    assert decoded["nonce"] == "abc123"
    assert decoded["verifier"] == "v" * 50
    assert decoded["return_to"] == "/dashboard"


def test_verify_state_tampered_rejected():
    secret = "test-secret"
    payload = {"nonce": "abc", "verifier": "v" * 50}
    token = sign_state(payload, secret=secret)
    # Flip one char in the payload portion
    body, sig = token.rsplit(".", 1)
    # Decode, mutate, re-encode
    decoded_payload = json.loads(base64.urlsafe_b64decode(body + "=="))
    decoded_payload["nonce"] = "evil"
    tampered_body = base64.urlsafe_b64encode(
        json.dumps(decoded_payload).encode()
    ).rstrip(b"=").decode()
    tampered = f"{tampered_body}.{sig}"
    with pytest.raises(ValueError, match="signature"):
        verify_state(tampered, secret=secret)


def test_verify_state_wrong_secret_rejected():
    token = sign_state({"nonce": "x", "verifier": "v" * 50}, secret="secret-a")
    with pytest.raises(ValueError, match="signature"):
        verify_state(token, secret="secret-b")


def test_verify_state_expired_rejected():
    secret = "test-secret"
    # Build a state with an old timestamp
    old_ts = int(time.time()) - STATE_MAX_AGE_SECONDS - 60
    body = {"nonce": "x", "verifier": "v" * 50, "ts": old_ts}
    encoded_body = base64.urlsafe_b64encode(json.dumps(body).encode()).rstrip(b"=").decode()
    sig = hmac.new(secret.encode(), encoded_body.encode(), "sha256").hexdigest()
    token = f"{encoded_body}.{sig}"
    with pytest.raises(ValueError, match="expired"):
        verify_state(token, secret=secret)


def test_verify_state_malformed_rejected():
    with pytest.raises(ValueError):
        verify_state("not-a-valid-token", secret="s")
    with pytest.raises(ValueError):
        verify_state("", secret="s")


# --- Unit: id_token decoding ------------------------------------------------


def _make_jwt(payload: dict) -> str:
    """Construct an unsigned JWT (header.payload.sig) for decode tests."""
    header = base64.urlsafe_b64encode(
        json.dumps({"alg": "RS256", "typ": "JWT"}).encode()
    ).rstrip(b"=").decode()
    body = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    return f"{header}.{body}.fakesig"


def test_decode_id_token_extracts_claims():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "test-client-id",
        "sub": "hf-user-42",
        "email": "alice@example.com",
        "email_verified": True,
        "preferred_username": "alice",
        "name": "Alice Example",
        "picture": "https://huggingface.co/avatars/alice.png",
        "iat": now,
        "exp": now + 3600,
    })
    claims = decode_id_token(token, audience="test-client-id")
    assert claims["email"] == "alice@example.com"
    assert claims["preferred_username"] == "alice"
    assert claims["name"] == "Alice Example"
    assert claims["picture"] == "https://huggingface.co/avatars/alice.png"


def test_decode_id_token_rejects_wrong_issuer():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://evil.example.com",
        "aud": "test-client-id",
        "sub": "x",
        "email": "a@b.com",
        "iat": now,
        "exp": now + 3600,
    })
    with pytest.raises(ValueError, match="issuer"):
        decode_id_token(token, audience="test-client-id")


def test_decode_id_token_rejects_wrong_audience():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "other-client",
        "sub": "x",
        "email": "a@b.com",
        "iat": now,
        "exp": now + 3600,
    })
    with pytest.raises(ValueError, match="audience"):
        decode_id_token(token, audience="test-client-id")


def test_decode_id_token_rejects_expired():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "test-client-id",
        "sub": "x",
        "email": "a@b.com",
        "iat": now - 7200,
        "exp": now - 3600,
    })
    with pytest.raises(ValueError, match="expired"):
        decode_id_token(token, audience="test-client-id")


def test_decode_id_token_requires_email():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "test-client-id",
        "sub": "x",
        "iat": now,
        "exp": now + 3600,
    })
    with pytest.raises(ValueError, match="email"):
        decode_id_token(token, audience="test-client-id")


def test_decode_id_token_requires_verified_email():
    now = int(time.time())
    token = _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "test-client-id",
        "sub": "x",
        "email": "a@b.com",
        "email_verified": False,
        "iat": now,
        "exp": now + 3600,
    })
    with pytest.raises(ValueError, match="verified"):
        decode_id_token(token, audience="test-client-id")


# --- Integration: /v1/auth/huggingface/start --------------------------------


async def test_hf_start_redirects_to_authorize_url(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.hf_client_id", "test-client-id")
    monkeypatch.setattr("app.config.settings.hf_client_secret", "test-client-secret")
    monkeypatch.setattr(
        "app.config.settings.hf_redirect_uri",
        "http://localhost:8000/v1/auth/huggingface/callback",
    )
    monkeypatch.setattr("app.config.settings.hf_oauth_state_secret", "test-secret")

    res = await client.get("/v1/auth/huggingface/start", follow_redirects=False)
    assert res.status_code == 302
    location = res.headers["location"]
    assert location.startswith("https://huggingface.co/oauth/authorize")
    assert "client_id=test-client-id" in location
    assert "response_type=code" in location
    assert "code_challenge=" in location
    assert "code_challenge_method=S256" in location
    assert "scope=openid" in location
    assert "state=" in location
    # State cookie must be set
    assert "hf_oauth_state=" in res.headers.get("set-cookie", "")


async def test_hf_start_requires_config(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.hf_client_id", "")
    res = await client.get("/v1/auth/huggingface/start", follow_redirects=False)
    assert res.status_code == 503


async def test_hf_start_accepts_return_to(client, monkeypatch):
    monkeypatch.setattr("app.config.settings.hf_client_id", "test-client-id")
    monkeypatch.setattr("app.config.settings.hf_client_secret", "test-client-secret")
    monkeypatch.setattr(
        "app.config.settings.hf_redirect_uri",
        "http://localhost:8000/v1/auth/huggingface/callback",
    )
    monkeypatch.setattr("app.config.settings.hf_oauth_state_secret", "test-secret")
    res = await client.get(
        "/v1/auth/huggingface/start?return_to=/onboarding",
        follow_redirects=False,
    )
    assert res.status_code == 302


# --- Integration: /v1/auth/huggingface/callback ------------------------------


@pytest.fixture
def hf_oauth_config(monkeypatch):
    monkeypatch.setattr("app.config.settings.hf_client_id", "test-client-id")
    monkeypatch.setattr("app.config.settings.hf_client_secret", "test-client-secret")
    monkeypatch.setattr(
        "app.config.settings.hf_redirect_uri",
        "http://localhost:8000/v1/auth/huggingface/callback",
    )
    monkeypatch.setattr("app.config.settings.hf_oauth_state_secret", "test-secret")
    monkeypatch.setattr("app.config.settings.webapp_url", "http://localhost:3000")


def _build_state_cookie(return_to: str = "/auth/callback") -> tuple[str, str]:
    """Return (state_token, verifier) and pre-install into sign_state logic."""
    verifier, challenge = generate_pkce_pair()
    nonce = "test-nonce-1234567890"
    state = sign_state(
        {"nonce": nonce, "verifier": verifier, "return_to": return_to, "challenge": challenge},
        secret="test-secret",
    )
    return state, verifier


def _valid_id_token(email: str = "alice@example.com") -> str:
    now = int(time.time())
    return _make_jwt({
        "iss": "https://huggingface.co",
        "aud": "test-client-id",
        "sub": "hf-user-42",
        "email": email,
        "email_verified": True,
        "preferred_username": "alice",
        "name": "Alice Example",
        "picture": "https://hf.co/avatars/alice.png",
        "iat": now,
        "exp": now + 3600,
    })


async def test_hf_callback_success_new_user(client, hf_oauth_config, mock_supabase):
    state, _verifier = _build_state_cookie()

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json = MagicMock(
        return_value={"access_token": "hf-at", "id_token": _valid_id_token()}
    )

    # User does not yet exist in Supabase
    mock_list = MagicMock(users=[])
    mock_supabase.auth.admin.list_users.return_value = mock_list

    created_user = MagicMock()
    created_user.id = "new-auth-uuid"
    created_user.email = "alice@example.com"
    mock_supabase.auth.admin.create_user.return_value = MagicMock(user=created_user)

    mock_supabase.auth.admin.generate_link.return_value = MagicMock(
        properties=MagicMock(action_link="http://localhost:3000/auth/callback#magic=xyz")
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_token_response)):
        res = await client.get(
            f"/v1/auth/huggingface/callback?code=hfcode&state={state}",
            cookies={"hf_oauth_state": state},
            follow_redirects=False,
        )

    assert res.status_code == 302
    assert "magic=xyz" in res.headers["location"]
    mock_supabase.auth.admin.create_user.assert_called_once()
    create_args = mock_supabase.auth.admin.create_user.call_args[0][0]
    assert create_args["email"] == "alice@example.com"
    assert create_args["email_confirm"] is True
    assert create_args["user_metadata"]["provider"] == "huggingface"
    assert create_args["user_metadata"]["hf_username"] == "alice"


async def test_hf_callback_success_existing_user(client, hf_oauth_config, mock_supabase):
    state, _verifier = _build_state_cookie()

    mock_token_response = MagicMock()
    mock_token_response.status_code = 200
    mock_token_response.json = MagicMock(
        return_value={"access_token": "hf-at", "id_token": _valid_id_token()}
    )

    # Existing Supabase user with same email
    existing = MagicMock()
    existing.id = "existing-auth-uuid"
    existing.email = "alice@example.com"
    mock_supabase.auth.admin.list_users.return_value = MagicMock(users=[existing])
    mock_supabase.auth.admin.generate_link.return_value = MagicMock(
        properties=MagicMock(action_link="http://localhost:3000/auth/callback#magic=abc")
    )

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_token_response)):
        res = await client.get(
            f"/v1/auth/huggingface/callback?code=hfcode&state={state}",
            cookies={"hf_oauth_state": state},
            follow_redirects=False,
        )

    assert res.status_code == 302
    assert "magic=abc" in res.headers["location"]
    mock_supabase.auth.admin.create_user.assert_not_called()
    mock_supabase.auth.admin.generate_link.assert_called_once()


async def test_hf_callback_bad_state(client, hf_oauth_config):
    res = await client.get(
        "/v1/auth/huggingface/callback?code=hfcode&state=tampered",
        cookies={"hf_oauth_state": "different-cookie"},
        follow_redirects=False,
    )
    assert res.status_code == 400


async def test_hf_callback_missing_code(client, hf_oauth_config):
    state, _ = _build_state_cookie()
    res = await client.get(
        f"/v1/auth/huggingface/callback?state={state}",
        cookies={"hf_oauth_state": state},
        follow_redirects=False,
    )
    assert res.status_code == 400


async def test_hf_callback_token_exchange_fails(client, hf_oauth_config):
    state, _ = _build_state_cookie()

    mock_token_response = MagicMock()
    mock_token_response.status_code = 400
    mock_token_response.text = "invalid_grant"

    with patch("httpx.AsyncClient.post", new=AsyncMock(return_value=mock_token_response)):
        res = await client.get(
            f"/v1/auth/huggingface/callback?code=hfcode&state={state}",
            cookies={"hf_oauth_state": state},
            follow_redirects=False,
        )
    assert res.status_code == 502


async def test_hf_callback_state_cookie_mismatch(client, hf_oauth_config):
    """If the state param doesn't match the cookie, reject."""
    state_a, _ = _build_state_cookie()
    state_b, _ = _build_state_cookie()
    # Valid signatures on both but they differ
    res = await client.get(
        f"/v1/auth/huggingface/callback?code=hfcode&state={state_a}",
        cookies={"hf_oauth_state": state_b},
        follow_redirects=False,
    )
    assert res.status_code == 400
