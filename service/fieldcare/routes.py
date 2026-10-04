"""A buffered endpoint: validate, clarify if needed, then use the real AI graph."""

from fastapi import APIRouter, HTTPException, Request
from fieldcare.model import ModelUnavailable
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse
from fieldcare.service import clarification_for, run_diagnosis
from module_b.openrouter import OpenRouterError

router = APIRouter()


@router.post("/v1/diagnose", response_model=DiagnosticResponse)
def diagnose(payload: DiagnosticRequest, request: Request):
    clarification = clarification_for(payload)
    if clarification is not None:
        return clarification
    try:
        graph = request.app.state.resources.graph_for()
        result = run_diagnosis(payload, graph=graph)
        observation = getattr(request.state, "observation", None)
        if observation is not None and result.status == "ready":
            observation["source"] = "live_provider"
        return result
    except (ModelUnavailable, OpenRouterError):
        raise HTTPException(
            502, "The provider could not complete this request. Retry later."
        ) from None
