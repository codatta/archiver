from __future__ import annotations

import httpx
from supabase import Client, ClientOptions, create_client

from app.config import settings

_client: Client | None = None
_timeout = httpx.Timeout(30.0, connect=15.0)


def get_supabase() -> Client:
    """Lazy Supabase client — uses secret key if available, falls back to publishable."""
    global _client
    if _client is None:
        key = settings.supabase_secret_key or settings.supabase_publishable_key
        if not key:
            raise RuntimeError("No Supabase key configured. Set SUPABASE_SECRET_KEY or SUPABASE_PUBLISHABLE_KEY.")
        _client = create_client(
            settings.supabase_url,
            key,
            options=ClientOptions(
                postgrest_client_timeout=_timeout,
                storage_client_timeout=30,
                function_client_timeout=30,
            ),
        )
    return _client


# Backward compat — lazy property
class _LazyClient:
    def __getattr__(self, name):
        return getattr(get_supabase(), name)


supabase = _LazyClient()
