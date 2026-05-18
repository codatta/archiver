from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.access_log import AccessLogMiddleware
from app.config import settings
from app.mysql_db import close_pool, create_pool
from app.routes import (
    admin,
    auth,
    auth_hf,
    auth_hooks,
    billing,
    data,
    domains,
    health,
    keys,
    live_data,
    members,
    onboarding,
    orgs,
    sandbox,
    subscriptions,
    verticals,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_pool()
    yield
    await close_pool()


app = FastAPI(title="Humanbased API", version="0.2.0", lifespan=lifespan)

_cors_origins = list({settings.webapp_url, "http://localhost:3000", "http://localhost:3001"})

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AccessLogMiddleware)

app.include_router(health.router)
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(auth_hf.router, prefix="/v1/auth", tags=["auth-hf"])
app.include_router(auth_hooks.router, prefix="/v1/auth/hooks", tags=["auth-hooks"])
app.include_router(onboarding.router, prefix="/v1/onboarding", tags=["onboarding"])
app.include_router(orgs.router, prefix="/v1/orgs", tags=["orgs"])
app.include_router(keys.router, prefix="/v1/orgs/{org_id}/keys", tags=["keys"])
app.include_router(members.router, prefix="/v1/orgs/{org_id}/members", tags=["members"])
app.include_router(billing.router, prefix="/v1/orgs/{org_id}/billing", tags=["billing"])
app.include_router(billing.webhook_router, prefix="/v1/billing", tags=["billing-webhook"])
app.include_router(billing.mode_router, prefix="/v1/billing", tags=["billing-mode"])
app.include_router(
    subscriptions.router, prefix="/v1/orgs/{org_id}/subscriptions", tags=["subscriptions"]
)
app.include_router(verticals.router, prefix="/v1/verticals", tags=["verticals"])
app.include_router(domains.router, prefix="/v1/domains", tags=["domains"])
# Backward-compat alias — old /v1/frontiers still works
app.include_router(domains.router, prefix="/v1/frontiers", tags=["domains"])
app.include_router(live_data.router, prefix="/v1", tags=["live-data"])
app.include_router(
    live_data.dashboard_router, prefix="/v1/orgs/{org_id}", tags=["dashboard-live"]
)
app.include_router(data.router, prefix="/v1", tags=["consumer-api"])
app.include_router(data.dashboard_router, prefix="/v1/orgs/{org_id}/data", tags=["dashboard-data"])
app.include_router(sandbox.router, prefix="/v1/sandbox", tags=["sandbox"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
