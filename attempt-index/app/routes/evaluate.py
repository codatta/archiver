from fastapi import APIRouter

from app.db.client import get_client
from app.models.request import EvaluateRequest
from app.models.response import EvaluateResponse
from app.services.attempt import evaluate

router = APIRouter()


@router.post("/v1/evaluate", response_model=EvaluateResponse)
def evaluate_endpoint(req: EvaluateRequest) -> EvaluateResponse:
    return evaluate(get_client(), req)
