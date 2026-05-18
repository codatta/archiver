from fastapi import APIRouter, HTTPException

from app.db.client import get_client
from app.models.request import BootstrapRequest
from app.models.response import BootstrapResponse
from app.services.attempt import bootstrap

router = APIRouter()


@router.post("/v1/bootstrap", response_model=BootstrapResponse)
def bootstrap_endpoint(req: BootstrapRequest) -> BootstrapResponse:
    try:
        return bootstrap(get_client(), req.records)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
