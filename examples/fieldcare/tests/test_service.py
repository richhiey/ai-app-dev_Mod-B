import json
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app import model, routes
from app.main import app

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"
VALID = json.loads((FIXTURES / "valid-request.json").read_text())


@pytest.fixture(autouse=True)
def isolated_environment(monkeypatch):
    monkeypatch.setenv("FIELDCARE_MODE", "demo")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_MODEL", raising=False)


def forbid_provider(*args, **kwargs):
    pytest.fail("This request must not call a provider")


def test_demo_complete_request_has_evidence_without_network(monkeypatch):
    monkeypatch.setattr(model.httpx, "post", forbid_provider)
    with TestClient(app) as client:
        response = client.post("/v1/diagnose", json=VALID)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "ready"
    assert result["mode"] == "demo"
    assert result["answer"].startswith("DEMO: No model was called.")
    assert result["citations"] == ["DOC-FC-TS-001", "DOC-FC-MP-014"]


@pytest.mark.parametrize("payload", [
    {}, {"question": "  "}, {"question": 42}, {"question": "x" * 2001},
    {"question": "airflow", "unexpected": "value"},
    {"question": "airflow", "equipment_id": "  "},
])
def test_malformed_input_never_reaches_model(payload, monkeypatch):
    monkeypatch.setattr(model.httpx, "post", forbid_provider)
    monkeypatch.setattr("app.service.generate_answer", forbid_provider)
    with TestClient(app) as client:
        response = client.post("/v1/diagnose", json=payload)
    assert response.status_code == 422


@pytest.mark.parametrize("payload", [
    {"question": "The unit runs hot after service."},
    {"question": "airflow", "equipment_id": "UNKNOWN"},
    {"question": "airflow", "equipment_id": "EQ-FC-1001"},
    {"question": "Is this filter repair covered by warranty?", "equipment_id": "EQ-FC-1002"},
    {"question": "Check filter and ticket history", "equipment_id": "EQ-FC-1002"},
    {"question": "Tell me a joke", "equipment_id": "EQ-FC-1002"},
])
def test_incomplete_or_unsupported_request_needs_review_without_model(payload, monkeypatch):
    monkeypatch.setattr("app.service.generate_answer", forbid_provider)
    with TestClient(app) as client:
        response = client.post("/v1/diagnose", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "needs_clarification"
    assert response.json()["citations"] == []


def test_safety_signal_precedes_missing_equipment(monkeypatch):
    monkeypatch.setattr("app.service.generate_answer", forbid_provider)
    with TestClient(app) as client:
        result = client.post("/v1/diagnose", json={"question": "Smoke after filter service"}).json()
    assert result["status"] == "needs_clarification"
    assert "Stop routine troubleshooting" in result["answer"]
    assert result["citations"] == ["DOC-FC-SAF-001"]


def configure_mock_live(monkeypatch):
    # Deliberately synthetic values, never credentials from the environment.
    monkeypatch.setenv("FIELDCARE_MODE", "live")
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "test/model")
    monkeypatch.setattr(routes, "MODEL_NAME", "test/model")


def test_live_adapter_posts_question_and_supplied_evidence(monkeypatch):
    configure_mock_live(monkeypatch)
    calls = []

    def fake_post(url, *, headers, json, timeout):
        calls.append((url, headers, json, timeout))
        return httpx.Response(200, json={"choices": [{
            "finish_reason": "stop", "message": {"content": "Inspect the supplied document checks."}
        }]}, request=httpx.Request("POST", url))

    monkeypatch.setattr(model.httpx, "post", fake_post)
    with TestClient(app) as client:
        response = client.post("/v1/diagnose", json=VALID)
    assert response.status_code == 200
    assert response.json()["mode"] == "live"
    assert response.json()["answer"] == "Inspect the supplied document checks."
    assert len(calls) == 1
    url, headers, body, timeout = calls[0]
    assert url == "https://openrouter.ai/api/v1/chat/completions"
    assert headers["Authorization"] == "Bearer synthetic-test-key"
    assert body["model"] == "test/model"
    assert body["messages"][0]["content"] == routes.SYSTEM_PROMPT
    context = json.loads(body["messages"][1]["content"])
    assert context["question"] == VALID["question"]
    assert context["evidence"]["equipment"]["model"] == "HX-220"
    assert {doc["doc_id"] for doc in context["evidence"]["documents"]} == {"DOC-FC-TS-001", "DOC-FC-MP-014"}
    assert "synthetic-test-key" not in json.dumps(body)
    assert timeout == 30.0


@pytest.mark.parametrize("case", ["http_error", "timeout", "empty", "truncated", "bad_json", "missing_choices"])
def test_provider_failure_is_safe_http_error_not_fake_answer(case, monkeypatch):
    configure_mock_live(monkeypatch)

    def fake_post(url, **kwargs):
        request = httpx.Request("POST", url)
        if case == "timeout":
            raise httpx.ReadTimeout("private-provider-detail", request=request)
        if case == "http_error":
            return httpx.Response(401, text="synthetic-test-key private-provider-detail", request=request)
        if case == "bad_json":
            return httpx.Response(200, text="not-json", request=request)
        data = {} if case == "missing_choices" else {"choices": [{
            "finish_reason": "length" if case == "truncated" else "stop",
            "message": {"content": "" if case == "empty" else "incomplete answer"},
        }]}
        return httpx.Response(200, json=data, request=request)

    monkeypatch.setattr(model.httpx, "post", fake_post)
    with TestClient(app) as client:
        response = client.post("/v1/diagnose", json=VALID)
    assert response.status_code == 502
    assert response.json() == {"detail": "The model provider is unavailable. Try again later."}
    assert "synthetic-test-key" not in response.text
    assert "private-provider-detail" not in response.text


def test_live_startup_requires_both_settings(monkeypatch):
    monkeypatch.setenv("FIELDCARE_MODE", "live")
    with pytest.raises(RuntimeError, match="Live mode requires"):
        with TestClient(app):
            pass


def test_unknown_mode_fails_startup(monkeypatch):
    monkeypatch.setenv("FIELDCARE_MODE", "typo")
    with pytest.raises(RuntimeError, match="FIELDCARE_MODE"):
        with TestClient(app):
            pass


def test_health_and_api_schema_do_not_call_provider(monkeypatch):
    monkeypatch.setattr(model.httpx, "post", forbid_provider)
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok", "mode": "demo"}
        schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/v1/diagnose"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"]["$ref"].endswith("DiagnosticRequest")
    assert operation["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("DiagnosticResponse")
