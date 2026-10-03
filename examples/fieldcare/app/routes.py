"""The version-one route owns its prompt and model selection."""
from fastapi import APIRouter, HTTPException, Request

from app.model import ModelUnavailable
from app.schemas import DiagnosticRequest, DiagnosticResponse
from app.service import run_diagnosis

router = APIRouter()

@router.post("/v1/diagnose", response_model=DiagnosticResponse)
def diagnose(payload: DiagnosticRequest, request: Request) -> DiagnosticResponse:
    try:
        return run_diagnosis(payload, graph=request.app.state.diagnosis_graph)
    except ModelUnavailable:
        raise HTTPException(status_code=502, detail="The model provider is unavailable. Try again later.") from None
