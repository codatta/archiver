"""HuggingFace OAuth 2.0 / OIDC sign-in routes.

Flow:
  1. Frontend → GET /v1/auth/huggingface/start
     → 302 to huggingface.co/oauth/authorize with PKCE + signed-state cookie
  2. HF → GET /v1/auth/huggingface/callback?code=...&state=...
     → exchange code + verifier for id_token at HF token endpoint
     → decode id_token, upsert Supabase user via admin API
     → generate magiclink → 302 browser to magiclink action_link
     → Supabase verifies magiclink → 302 to app `/auth/callback`
     → existing sync-profile flow takes over
"""

from __future__ import annotations

import logging
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.config import settings
from app.db import supabase
from app.services.hf_oauth import (
    decode_id_token,
    generate_pkce_pair,
    sign_state,
    verify_state,
)

logger = logging.getLogger(__name__)
router = APIRouter()

HF_AUTHORIZE_URL = "https://huggingface.co/oauth/authorize"
HF_TOKEN_URL = "https://huggingface.co/oauth/token"
STATE_COOKIE_NAME = "hf_oauth_state"
DEFAULT_RETURN_TO = "/auth/callback"


def _require_config() -> None:
    if (
        not settings.hf_client_id
        or not settings.hf_client_secret
        or not settings.hf_redirect_uri
        or not settings.hf_oauth_state_secret
    ):
        raise HTTPException(
            status_code=503,
            detail="HuggingFace OAuth is not configured",
        )


@router.get("/huggingface/start")
async def hf_start(return_to: str | None = None):
    _require_config()

    verifier, challenge = generate_pkce_pair()
    # Only allow relative return_to paths to avoid open-redirect.
    safe_return_to = DEFAULT_RETURN_TO
    if return_to and return_to.startswith("/") and not return_to.startswith("//"):
        safe_return_to = return_to

    state = sign_state(
        {
            "verifier": verifier,
            "challenge": challenge,
            "return_to": safe_return_to,
        },
        secret=settings.hf_oauth_state_secret,
    )

    params = {
        "client_id": settings.hf_client_id,
        "redirect_uri": settings.hf_redirect_uri,
        "response_type": "code",
        "scope": "openid profile email",
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    }
    authorize_url = f"{HF_AUTHORIZE_URL}?{urlencode(params)}"

    response = RedirectResponse(url=authorize_url, status_code=302)
    response.set_cookie(
        key=STATE_COOKIE_NAME,
        value=state,
        max_age=600,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/v1/auth/huggingface",
    )
    return response


def _error_redirect(message: str) -> RedirectResponse:
    base = settings.webapp_url or "http://localhost:3000"
    params = urlencode({"error": message})
    return RedirectResponse(url=f"{base}/auth/signin?{params}", status_code=302)


@router.get("/huggingface/callback")
async def hf_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    _require_config()

    if error:
        logger.info("HF OAuth provider returned error: %s", error)
        raise HTTPException(status_code=400, detail=f"provider error: {error}")

    if not code or not state:
        raise HTTPException(status_code=400, detail="missing code or state")

    cookie_state = request.cookies.get(STATE_COOKIE_NAME)
    if not cookie_state or cookie_state != state:
        raise HTTPException(status_code=400, detail="state mismatch")

    try:
        state_payload = verify_state(state, secret=settings.hf_oauth_state_secret)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid state: {e}") from e

    verifier = state_payload.get("verifier")
    return_to = state_payload.get("return_to", DEFAULT_RETURN_TO)
    if not verifier:
        raise HTTPException(status_code=400, detail="invalid state payload")

    # Exchange code for tokens at HF
    async with httpx.AsyncClient(timeout=15.0) as http:
        token_res = await http.post(
            HF_TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.hf_redirect_uri,
                "client_id": settings.hf_client_id,
                "client_secret": settings.hf_client_secret,
                "code_verifier": verifier,
            },
            headers={"Accept": "application/json"},
        )

    if token_res.status_code != 200:
        logger.warning("HF token exchange failed: %s %s", token_res.status_code, token_res.text)
        raise HTTPException(status_code=502, detail="token exchange failed")

    token_data = token_res.json()
    id_token = token_data.get("id_token")
    if not id_token:
        raise HTTPException(status_code=502, detail="no id_token in response")

    try:
        claims = decode_id_token(id_token, audience=settings.hf_client_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"invalid id_token: {e}") from e

    email = claims["email"]
    hf_username = claims.get("preferred_username") or claims.get("name") or ""
    full_name = claims.get("name") or hf_username or email.split("@")[0]
    avatar_url = claims.get("picture")

    # Upsert Supabase user
    existing_user = None
    try:
        list_res = supabase.auth.admin.list_users()
        users = getattr(list_res, "users", list_res) or []
        for u in users:
            if getattr(u, "email", None) and u.email.lower() == email.lower():
                existing_user = u
                break
    except Exception:
        logger.exception("HF OAuth: list_users failed")
        raise HTTPException(status_code=502, detail="user lookup failed") from None

    if not existing_user:
        try:
            create_res = supabase.auth.admin.create_user({
                "email": email,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": full_name,
                    "avatar_url": avatar_url,
                    "hf_username": hf_username,
                    "provider": "huggingface",
                },
            })
            existing_user = getattr(create_res, "user", create_res)
        except Exception:
            logger.exception("HF OAuth: create_user failed")
            raise HTTPException(status_code=502, detail="user creation failed") from None

    # Generate a magiclink the browser can follow to establish a Supabase session.
    try:
        link_res = supabase.auth.admin.generate_link({
            "type": "magiclink",
            "email": email,
            "options": {
                "redirect_to": f"{settings.webapp_url}{return_to}",
            },
        })
        action_link = getattr(
            getattr(link_res, "properties", None), "action_link", None
        )
        if not action_link and isinstance(link_res, dict):
            action_link = (link_res.get("properties") or {}).get("action_link")
    except Exception:
        logger.exception("HF OAuth: generate_link failed")
        raise HTTPException(status_code=502, detail="magiclink generation failed") from None

    if not action_link:
        raise HTTPException(status_code=502, detail="no action_link from Supabase")

    response = RedirectResponse(url=action_link, status_code=302)
    response.delete_cookie(STATE_COOKIE_NAME, path="/v1/auth/huggingface")
    return response
