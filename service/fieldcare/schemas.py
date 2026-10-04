"""The caller supplies an input; FieldCare returns an agreed output shape."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class DiagnosticRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    question: str = Field(min_length=1, max_length=2000)
    equipment_id: str | None = Field(default=None, min_length=1, max_length=64)


class DiagnosticResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    answer: str = Field(min_length=1)
    status: Literal["ready", "needs_clarification"]
    citations: list[str]
    mode: Literal["live"]
