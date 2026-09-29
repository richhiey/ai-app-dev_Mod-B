from pydantic import BaseModel, ConfigDict, Field

class TechnicianNoteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=240)
    equipment_id: str | None = Field(default=None, min_length=1, max_length=64)
