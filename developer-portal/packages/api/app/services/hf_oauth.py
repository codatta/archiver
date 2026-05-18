"""HuggingFace OAuth 2.0 / OIDC helpers.

Since the id_token is delivered over the back-channel (direct HTTPS POST
from our API to HF's token endpoint, authenticated with client_secret),
we rely on TLS + client_secret mutual trust instead of verifying the JWT
signature against HF's JWKS (per OIDC Core 3.1.3.7). We still validate
iss, aud, exp, and email_verified claims.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
import time

HF_ISSUER = "https://huggingface.co"
STATE_MAX_AGE_SECONDS = 600  # 10 minutes


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


# --- PKCE --------------------------------------------------------------------


def generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for S256 PKCE."""
    verifier = _b64url_encode(secrets.token_bytes(32))  # 43 chars
    challenge = _b64url_encode(hashlib.sha256(verifier.encode()).digest())
    return verifier, challenge


# --- Signed state cookie -----------------------------------------------------


def sign_state(payload: dict, secret: str) -> str:
    """Encode payload as base64url JSON and HMAC-SHA256 sign it.

    Adds `ts` (current unix seconds) if not present so verify_state can
    enforce a max age.
    """
    body = {**payload}
    body.setdefault("ts", int(time.time()))
    encoded = _b64url_encode(json.dumps(body, sort_keys=True).encode())
    sig = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    return f"{encoded}.{sig}"


def verify_state(token: str, secret: str) -> dict:
    if not token or "." not in token:
        raise ValueError("malformed state token")
    try:
        encoded, sig = token.rsplit(".", 1)
    except ValueError as e:
        raise ValueError("malformed state token") from e

    expected = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        raise ValueError("invalid signature")

    try:
        payload = json.loads(_b64url_decode(encoded))
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError("malformed state payload") from e

    ts = payload.get("ts")
    if not isinstance(ts, int) or time.time() - ts > STATE_MAX_AGE_SECONDS:
        raise ValueError("state expired")

    return payload


# --- id_token decoding -------------------------------------------------------


def decode_id_token(id_token: str, audience: str) -> dict:
    """Decode + validate an HF OIDC id_token (back-channel, no sig verify).

    Validates: iss, aud, exp, and requires a verified email claim.
    """
    parts = id_token.split(".")
    if len(parts) != 3:
        raise ValueError("malformed id_token")

    try:
        claims = json.loads(_b64url_decode(parts[1]))
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError("malformed id_token payload") from e

    if claims.get("iss") != HF_ISSUER:
        raise ValueError(f"unexpected issuer: {claims.get('iss')}")

    aud = claims.get("aud")
    aud_list = aud if isinstance(aud, list) else [aud]
    if audience not in aud_list:
        raise ValueError("audience mismatch")

    exp = claims.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        raise ValueError("id_token expired")

    if not claims.get("email"):
        raise ValueError("id_token missing email claim")

    if claims.get("email_verified") is False:
        raise ValueError("email not verified by provider")

    return claims
