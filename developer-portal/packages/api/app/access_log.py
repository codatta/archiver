"""Access logging middleware — records every data-touching API request.

Logs to `access_log` table in Supabase asynchronously (fire-and-forget)
so it adds no latency to the response path.

Also provides `log_access()` for explicit logging from route handlers
when per-record cost details are available.
"""
import asyncio
import logging
import time
from typing import Any

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.db import supabase

logger = logging.getLogger(__name__)

# Endpoints that touch production data — only these get logged.
DATA_ENDPOINTS = (
    "/v1/live/",
    "/v1/frontiers/",
    "/v1/data/",
    "/v1/orgs/",  # catches /v1/orgs/{id}/live/*, /v1/orgs/{id}/data/*
)


def _is_data_endpoint(path: str) -> bool:
    return any(path.startswith(prefix) for prefix in DATA_ENDPOINTS)


def _extract_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _fire_and_forget(row: dict[str, Any]) -> None:
    """Insert access log row without blocking the response."""
    try:
        supabase.table("access_log").insert(row).execute()
    except Exception as e:
        logger.warning("access_log insert failed: %s", e)


def log_access(
    *,
    request: Request,
    org_id: str | None = None,
    api_key_id: str | None = None,
    user_id: str | None = None,
    subscription_id: str | None = None,
    frontier_id: str | None = None,
    record_count: int = 0,
    item_costs: list[dict] | None = None,
    total_cost_usd: float = 0.0,
    response_status: int = 200,
    latency_ms: int = 0,
) -> None:
    """Explicit access log from a route handler (for per-record cost details).

    Called by pull/preview/feedback endpoints after building the response,
    with enriched data like item_costs and total_cost_usd.
    """
    row = {
        "org_id": org_id,
        "api_key_id": api_key_id,
        "user_id": user_id,
        "endpoint": str(request.url.path),
        "method": request.method,
        "subscription_id": subscription_id,
        "frontier_id": frontier_id,
        "record_count": record_count,
        "item_costs": item_costs,
        "total_cost_usd": float(total_cost_usd),
        "response_status": response_status,
        "latency_ms": latency_ms,
        "ip_address": _extract_ip(request),
    }
    # Remove None values so Supabase uses column defaults
    row = {k: v for k, v in row.items() if v is not None}

    asyncio.get_event_loop().call_soon(lambda: _fire_and_forget(row))


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Middleware that logs data-endpoint requests automatically.

    This catches requests that don't call log_access() explicitly
    (e.g., error responses, non-pull endpoints like frontiers list).
    Route handlers that call log_access() directly should set
    request.state.access_logged = True to avoid double-logging.
    """

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        if not _is_data_endpoint(request.url.path):
            return await call_next(request)

        request.state.access_logged = False
        start = time.monotonic()
        response = await call_next(request)
        latency_ms = int((time.monotonic() - start) * 1000)

        # Skip if the route handler already logged explicitly
        if getattr(request.state, "access_logged", False):
            return response

        # Auto-log for data endpoints that didn't log explicitly
        row = {
            "endpoint": str(request.url.path),
            "method": request.method,
            "response_status": response.status_code,
            "latency_ms": latency_ms,
            "ip_address": _extract_ip(request),
        }
        asyncio.get_event_loop().call_soon(lambda r=row: _fire_and_forget(r))

        return response
