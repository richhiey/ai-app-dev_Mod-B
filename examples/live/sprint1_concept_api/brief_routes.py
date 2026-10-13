from fastapi import APIRouter, HTTPException, Request

from module_b.openrouter import OpenRouterError

from .brief_schemas import BriefRequest, BriefResponse
from .service import answer_question

router = APIRouter()
BRIEF_PROMPT = (
    "Answer the question using only the supplied context. Keep the response short, "
    "then name one useful follow-up question."
)


@router.post("/v1/answer-brief", response_model=BriefResponse)
def answer_brief(payload: BriefRequest, request: Request):
    try:
        result = answer_question(
            payload, system_prompt=BRIEF_PROMPT, response_shape="brief",
            observation=getattr(request.state, "observation", None),
        )
        return BriefResponse(**result.model_dump())
    except OpenRouterError:
        raise HTTPException(502, "The provider could not complete this request. Retry later.") from None
