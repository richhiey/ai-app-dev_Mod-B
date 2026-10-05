"""Contract behavior taught in the Sprint 1 notebook matches the service models."""
import json
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "service"))
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse


def test_checkpoint_observes_submitted_service_without_creating_v2():
    from module_b.openrouter import DEFAULT_CHAT_MODEL

    notebook = json.loads((ROOT / "notebooks/sprint_1/sprint_1_service_foundations.ipynb").read_text())
    cells = {cell["id"]: "".join(cell["source"]) for cell in notebook["cells"]}
    # Execute the actual observation cell against the untouched starter. It must
    # report a missing assessment route, never manufacture a completed endpoint.
    namespace = {"REPO": ROOT, "CHECKPOINT_MODEL": DEFAULT_CHAT_MODEL, "json": json}
    exec(compile(cells["checkpoint-03"], "checkpoint-03", "exec"), namespace)
    assert len(namespace["boundary_body"]["question"]) == 1000
    assert len(namespace["long_body"]["question"]) == 1001
    observations = namespace["observations"]
    assert [row["http_status"] for row in observations if row["path"] == "/v1/diagnose"] == [200, 200, 200, 422]
    assert [row["http_status"] for row in observations if row["path"] == "/v2/diagnose"] == [404, 404, 404, 404]
    assert not namespace["generation_attempted"]


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
