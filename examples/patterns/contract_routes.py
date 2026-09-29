"""A separate instructional caller; never replaces the original endpoint."""
from fastapi import APIRouter, HTTPException

from app.contract_schemas import TechnicianNoteRequest
from app.model import ModelUnavailable
from app.routes import MODEL_NAME, SYSTEM_PROMPT
from app.schemas import DiagnosticResponse
from app.service import run_diagnosis

router = APIRouter()


@router.post('/practice/technician-note', response_model=DiagnosticResponse)
def technician_note(request: TechnicianNoteRequest) -> DiagnosticResponse:
    try:
        return run_diagnosis(request, system_prompt=SYSTEM_PROMPT, model_name=MODEL_NAME)
    except ModelUnavailable:
        raise HTTPException(status_code=502, detail='The model provider is unavailable. Try again later.') from None
