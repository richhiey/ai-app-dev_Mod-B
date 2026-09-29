from pydantic import BaseModel, ConfigDict, Field

class HandoverV2Request(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=600)
    equipment_id: str | None = Field(default=None, min_length=1, max_length=64)
