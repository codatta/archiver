import httpx
from supabase import ClientOptions, create_client

from app.config import settings

# Increase timeouts to handle slow TLS handshakes to Supabase (Tokyo region)
_timeout = httpx.Timeout(30.0, connect=15.0)

supabase = create_client(
    settings.supabase_url,
    settings.supabase_secret_key,
    options=ClientOptions(
        postgrest_client_timeout=_timeout,
        storage_client_timeout=30,
        function_client_timeout=30,
    ),
)

# Patch auth client timeout (default is too short for slow TLS)
if hasattr(supabase.auth, "_http_client"):
    supabase.auth._http_client.timeout = _timeout
