from fastapi import APIRouter, HTTPException, Request
from fieldcare.model import ModelUnavailable
from fieldcare.resources import SYSTEM_PROMPT
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse
from fieldcare.service import clarification_for, run_diagnosis
from module_b.openrouter import OpenRouterError

router = APIRouter()
BRIEF_PROMPT = SYSTEM_PROMPT + (
    " Present the documented checks as three concise technician bullets. "
    "Keep source IDs and distinguish documented guidance from observations "
    "that the technician still needs to verify."
)


@router.post("/v1/diagnose-brief", response_model=DiagnosticResponse)
def brief_diagnose(payload: DiagnosticRequest, request: Request):
    clarification = clarification_for(payload)
    if clarification is not None:
        return clarification
    try:
        graph = request.app.state.resources.graph_for(system_prompt=BRIEF_PROMPT)
        return run_diagnosis(
            payload, graph=graph, observation=getattr(request.state, "observation", None)
        )
    except (ModelUnavailable, OpenRouterError):
        raise HTTPException(
            502, "The provider could not complete this request. Retry later."
        ) from None
