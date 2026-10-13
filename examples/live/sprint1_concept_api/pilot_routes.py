from fastapi import APIRouter, HTTPException

from module_b.openrouter import OpenRouterError

from .pilot_schemas import PilotRequest, PilotResponse
from .service import answer_question, selected_model

router = APIRouter()
PILOT_PROMPT = (
    "Answer the question using only the supplied context. Make the answer easy to scan "
    "and state when the context is insufficient."
)


@router.post("/v2/answer", response_model=PilotResponse)
def pilot_answer(payload: PilotRequest):
    try:
        result = answer_question(
            payload, system_prompt=PILOT_PROMPT,
            model_name=selected_model("OPENROUTER_MODEL_V2"),
        )
        return PilotResponse(**result.model_dump())
    except OpenRouterError:
        raise HTTPException(502, "The provider could not complete this request. Retry later.") from None
