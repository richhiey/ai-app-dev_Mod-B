from pydantic import Field
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse


class PilotRequest(DiagnosticRequest):
    question: str = Field(min_length=1, max_length=600)


class PilotResponse(DiagnosticResponse):
    pass
