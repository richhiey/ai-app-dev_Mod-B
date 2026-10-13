from pydantic import Field

from .schemas import AnswerRequest, AnswerResponse


class PilotRequest(AnswerRequest):
    question: str = Field(min_length=1, max_length=600)


class PilotResponse(AnswerResponse):
    pass
