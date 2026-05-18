from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.enums import CampaignStatus
from app.services.template_loader import list_templates, load_template

router = APIRouter(prefix="/v1/campaigns", tags=["campaigns"])

# ─── In-memory store (replaced by Supabase once migration is applied) ─────────
# This is intentionally simple: seed creates data, GET reads it.
# No persistence across restarts — that comes when Supabase is wired.

_campaigns: dict[str, dict] = {}
_tasks: dict[str, list[dict]] = {}  # campaign_id → tasks


# ─── Request / Response models ────────────────────────────────────────────────


class SeedRequest(BaseModel):
    template_id: str = "robotics_video_collection"
    name: str | None = None


class CampaignSummary(BaseModel):
    id: str
    frontier_id: str
    template_id: str
    name: str
    status: str
    task_count: int
    created_at: str


class TaskSummary(BaseModel):
    id: str
    task_key: str
    name: str
    origin: str
    execution: str
    position: int
    depends_on: list[str]
    has_annotation_config: bool
    ml_backend_url: str | None


class CampaignDetail(BaseModel):
    id: str
    org_id: str | None
    frontier_id: str
    template_id: str
    name: str
    status: str
    params: dict
    tasks: list[TaskSummary]
    created_at: str


# ─── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/seed", response_model=CampaignDetail)
async def seed_campaign(body: SeedRequest) -> CampaignDetail:
    """Create a campaign from a template. Mock endpoint for standalone dev."""
    try:
        template = load_template(body.template_id)
    except FileNotFoundError:
        raise HTTPException(404, f"Template not found: {body.template_id}")

    campaign_id = str(uuid4())
    now = "2026-04-12T00:00:00Z"

    campaign = {
        "id": campaign_id,
        "org_id": None,
        "frontier_id": template["frontier_id"],
        "template_id": template["template_id"],
        "name": body.name or template["name"],
        "status": CampaignStatus.LIVE,
        "annotation_config": None,
        "params": {
            "defaults": template.get("defaults", {}),
            "detection_presets": template.get("detection_presets", {}),
            "action_vocabulary": template.get("action_vocabulary", []),
        },
        "created_at": now,
    }
    _campaigns[campaign_id] = campaign

    # Build task ID map for resolving depends_on references
    task_key_to_id: dict[str, str] = {}
    tasks: list[dict] = []

    for task_def in template.get("tasks", []):
        task_id = str(uuid4())
        task_key_to_id[task_def["task_key"]] = task_id

    for task_def in template.get("tasks", []):
        task_id = task_key_to_id[task_def["task_key"]]
        depends_on_ids = [
            task_key_to_id[dep] for dep in task_def.get("depends_on", [])
        ]
        task = {
            "id": task_id,
            "campaign_id": campaign_id,
            "task_key": task_def["task_key"],
            "name": task_def["name"],
            "origin": task_def["origin"],
            "execution": task_def["execution"],
            "annotation_config": task_def.get("annotation_config"),
            "ml_backend_url": task_def.get("ml_backend_url"),
            "config": {},
            "depends_on": depends_on_ids,
            "position": task_def["position"],
        }
        tasks.append(task)

    _tasks[campaign_id] = tasks

    return _build_detail(campaign, tasks)


@router.get("", response_model=list[CampaignSummary])
async def list_campaigns() -> list[CampaignSummary]:
    """List all campaigns."""
    return [
        CampaignSummary(
            id=c["id"],
            frontier_id=c["frontier_id"],
            template_id=c["template_id"],
            name=c["name"],
            status=c["status"],
            task_count=len(_tasks.get(c["id"], [])),
            created_at=c["created_at"],
        )
        for c in _campaigns.values()
    ]


@router.get("/templates", response_model=list[str])
async def get_templates() -> list[str]:
    """List available campaign template IDs."""
    return list_templates()


@router.get("/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(campaign_id: str) -> CampaignDetail:
    """Get campaign detail with task DAG."""
    campaign = _campaigns.get(campaign_id)
    if not campaign:
        raise HTTPException(404, "Campaign not found")
    tasks = _tasks.get(campaign_id, [])
    return _build_detail(campaign, tasks)


@router.get("/{campaign_id}/tasks/{task_id}/config")
async def get_task_config(campaign_id: str, task_id: str) -> dict:
    """Get the LS XML annotation config for a specific task."""
    tasks = _tasks.get(campaign_id, [])
    for task in tasks:
        if task["id"] == task_id:
            return {
                "task_key": task["task_key"],
                "annotation_config": task.get("annotation_config"),
            }
    raise HTTPException(404, "Task not found")


# ─── Helpers ──────────────────────────────────────────────────────────────────


def _build_detail(campaign: dict, tasks: list[dict]) -> CampaignDetail:
    return CampaignDetail(
        id=campaign["id"],
        org_id=campaign.get("org_id"),
        frontier_id=campaign["frontier_id"],
        template_id=campaign["template_id"],
        name=campaign["name"],
        status=campaign["status"],
        params=campaign.get("params", {}),
        tasks=[
            TaskSummary(
                id=t["id"],
                task_key=t["task_key"],
                name=t["name"],
                origin=t["origin"],
                execution=t["execution"],
                position=t["position"],
                depends_on=t.get("depends_on", []),
                has_annotation_config=t.get("annotation_config") is not None,
                ml_backend_url=t.get("ml_backend_url"),
            )
            for t in sorted(tasks, key=lambda x: x["position"])
        ],
        created_at=campaign["created_at"],
    )
