from fastapi import APIRouter, HTTPException

from module_b.openrouter import OpenRouterError

from .schemas import AnswerRequest, AnswerResponse
from .service import answer_question

router = APIRouter()


@router.post("/v1/answer", response_model=AnswerResponse)
def answer(payload: AnswerRequest):
    try:
        return answer_question(payload)
    except OpenRouterError:
        raise HTTPException(502, "The provider could not complete this request. Retry later.") from None
