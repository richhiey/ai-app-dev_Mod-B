from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AnswerRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1, max_length=2000)
    context: str | None = Field(default=None, min_length=1, max_length=4000)


class AnswerResponse(BaseModel):
    answer: str | None
    status: Literal["ready", "needs_context"]
    references: list[str]
