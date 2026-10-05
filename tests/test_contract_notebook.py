"""Contract behavior taught in the Sprint 1 notebook matches the service models."""
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "fieldcare"))
from app.schemas import DiagnosticRequest, DiagnosticResponse


def test_checkpoint_asks_the_learner_to_exercise_the_versioned_supervisor_route():
    notebook = json.loads((ROOT / "notebooks/sprint_1/sprint_1_service_foundations.ipynb").read_text())
    cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
    assert "SUPERVISOR_PATH" in cells["run-supported"]
    assert '"/v2/diagnose"' in cells["run-supported"]
    assert "supported_body = json.loads(body_text)" in cells["run-supported"]
    assert "httpx.post(service.base_url + SUPERVISOR_PATH" in cells["run-supported"]
    assert "DiagnosticRequest.model_validate" not in "\n".join(cells.values())


def test_request_contract_accepts_optional_context_and_rejects_invalid_shapes():
    assert DiagnosticRequest.model_validate({"question": "Airflow"}).equipment_id is None
    assert DiagnosticRequest.model_validate({"question": " Airflow "}).question == "Airflow"
    for payload in ({}, {"question": "   "}, {"question": "Airflow", "unknown": True}):
        with pytest.raises(ValidationError):
            DiagnosticRequest.model_validate(payload)


def test_response_contract_requires_declared_status_and_citations_shape():
    response = DiagnosticResponse.model_validate({
        "answer": "Check the intake filter.",
        "status": "ready",
        "citations": ["DOC-FC-TS-001"],
        "mode": "live",
    })
    assert response.citations == ["DOC-FC-TS-001"]
    for changes in ({"status": "finished"}, {"citations": "DOC-FC-TS-001"}):
        payload = response.model_dump() | changes
        with pytest.raises(ValidationError):
            DiagnosticResponse.model_validate(payload)
