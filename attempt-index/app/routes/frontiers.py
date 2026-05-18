from fastapi import APIRouter, HTTPException

from app.db.client import get_client
from app.db.queries import create_frontier, frontier_exists, list_frontiers
from app.models.request import FrontierCreate
from app.models.response import FrontierResponse

router = APIRouter()


@router.post("/v1/frontiers", response_model=FrontierResponse)
def create_frontier_endpoint(req: FrontierCreate) -> FrontierResponse:
    client = get_client()
    if frontier_exists(client, req.frontier_id):
        raise HTTPException(
            status_code=409, detail=f"frontier_id '{req.frontier_id}' already exists"
        )
    row = create_frontier(
        client, frontier_id=req.frontier_id, name=req.name, description=req.description
    )
    return FrontierResponse(**row)


@router.get("/v1/frontiers", response_model=list[FrontierResponse])
def list_frontiers_endpoint() -> list[FrontierResponse]:
    rows = list_frontiers(get_client())
    return [FrontierResponse(**row) for row in rows]
