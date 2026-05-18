from fastapi import APIRouter

from app.config import settings

router = APIRouter()


@router.get("/v1/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": "contributor-portal-api",
        "version": "0.1.0",
        "config": {
            "campaign_source": settings.campaign_source,
            "attempt_index_backend": settings.attempt_index_backend,
            "lineage_backend": settings.lineage_backend,
            "vision_engine_url": settings.vision_engine_url,
        },
    }
