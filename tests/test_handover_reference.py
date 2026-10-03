"""Exercise FastAPI's real validation and deterministic clarification boundary."""
import sys
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
FIELDCARE = ROOT / "examples" / "fieldcare"


@pytest.fixture
def client():
    sys.path.insert(0, str(FIELDCARE))
    from app.routes import router

    application = FastAPI()
    application.include_router(router)

    class UnusedGraph:
        def invoke(self, *_args, **_kwargs):
            pytest.fail("Clarification must return before retrieval or generation.")

    application.state.diagnosis_graph = UnusedGraph()
    with TestClient(application) as test_client:
        yield test_client
    sys.path.remove(str(FIELDCARE))


def test_invalid_request_is_rejected_before_the_route(client):
    response = client.post("/v1/diagnose", json={"equipment_id": "EQ-FC-1002"})
    assert response.status_code == 422


def test_valid_request_without_equipment_is_clarified_without_model_work(client):
    response = client.post("/v1/diagnose", json={"question": "The unit runs hot after service."})
    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["citations"] == []


def test_supported_route_and_clarification_schema_are_current():
    source = (FIELDCARE / "app" / "main.py").read_text()
    assert "OpenRouterClient(" in source
    assert "build_document_store(" in source
    assert "build_diagnosis_graph(" in source
    assert '"mode": "demo"' not in source
