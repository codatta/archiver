from fastapi import FastAPI

from app.routes.bootstrap import router as bootstrap_router
from app.routes.evaluate import router as evaluate_router
from app.routes.frontiers import router as frontiers_router
from app.routes.health import router as health_router

app = FastAPI(
    title="AttemptIndex",
    description="Deterministic attempt-number assignment for the Humanbased Contribution Pipeline",
    version="0.1.0",
)

app.include_router(health_router)
app.include_router(evaluate_router)
app.include_router(bootstrap_router)
app.include_router(frontiers_router)
