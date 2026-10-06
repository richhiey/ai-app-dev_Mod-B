from fastapi import APIRouter, HTTPException, Request
from fieldcare.config import openrouter_model_v2
from fieldcare.model import ModelUnavailable
from fieldcare.pilot_schemas import PilotRequest, PilotResponse
from fieldcare.resources import SYSTEM_PROMPT
from fieldcare.service import clarification_for, run_diagnosis
from module_b.openrouter import OpenRouterError

router = APIRouter()
PILOT_PROMPT = SYSTEM_PROMPT + (
    " For this pilot, present the documented checks in two short paragraphs: "
    "first the checks, then what the technician still needs to verify."
)


@router.post("/v2/diagnose", response_model=PilotResponse)
def pilot_diagnose(payload: PilotRequest, request: Request):
    clarification = clarification_for(payload)
    if clarification is not None:
        return PilotResponse.model_validate(clarification.model_dump())
    try:
        graph = request.app.state.resources.graph_for(
            system_prompt=PILOT_PROMPT, model_name=openrouter_model_v2()
        )
        result = run_diagnosis(
            payload, graph=graph, observation=getattr(request.state, "observation", None)
        )
        return PilotResponse.model_validate(result.model_dump())
    except (ModelUnavailable, OpenRouterError):
        raise HTTPException(
            502, "The provider could not complete this request. Retry later."
        ) from None
