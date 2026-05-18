from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import campaigns, contributions, contributors, enrollments, health, tasks

app = FastAPI(
    title="Contributor Portal API",
    version="0.1.0",
    description="Supply-side API for the Humanbased data contribution platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.webapp_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(campaigns.router)
app.include_router(contributors.router)
app.include_router(enrollments.router)
app.include_router(tasks.router)
app.include_router(contributions.router)
