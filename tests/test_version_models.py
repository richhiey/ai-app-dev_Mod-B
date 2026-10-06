"""Verify version selection at the graph boundary, without provider claims."""
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fieldcare import config, resources, routes
from module_b.openrouter import CHAT_MODELS, DEFAULT_CHAT_MODEL

ROOT = Path(__file__).resolve().parents[1]


def load_example(monkeypatch, name):
    spec = importlib.util.spec_from_file_location(f"fieldcare.{name}", ROOT / "examples/live" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, module)
    spec.loader.exec_module(module)
    return module


def test_each_model_setting_defaults_and_validates_independently(monkeypatch):
    other = sorted(CHAT_MODELS - {DEFAULT_CHAT_MODEL})[0]
    monkeypatch.setenv("OPENROUTER_MODEL", other)
    monkeypatch.delenv("OPENROUTER_MODEL_V2", raising=False)
    assert config.openrouter_model() == other
    assert config.openrouter_model_v2() == DEFAULT_CHAT_MODEL
    for invalid in ("", "unapproved/model"):
        monkeypatch.setenv("OPENROUTER_MODEL_V2", invalid)
        with pytest.raises(ValueError, match="OPENROUTER_MODEL_V2"):
            config.openrouter_model_v2()
        assert config.openrouter_model() == other
    monkeypatch.setenv("OPENROUTER_MODEL_V2", other)
    monkeypatch.setenv("OPENROUTER_MODEL", "invalid")
    assert config.openrouter_model_v2() == other
    with pytest.raises(ValueError, match="OPENROUTER_MODEL"):
        config.openrouter_model()


def test_actual_routes_bind_separate_models_and_keep_contracts(monkeypatch):
    load_example(monkeypatch, "pilot_schemas")
    pilot = load_example(monkeypatch, "pilot_routes")
    v1, v2, changed = sorted(CHAT_MODELS)
    monkeypatch.setenv("OPENROUTER_MODEL", v1)
    monkeypatch.setenv("OPENROUTER_MODEL_V2", v2)
    captured = []
    # Only the prepared-resource and graph execution boundaries are doubled.
    monkeypatch.setattr(resources.ServiceResources, "ready", lambda self: self)
    def graph(**kwargs):
        captured.append((kwargs["model_name"], kwargs["system_prompt"]))
        return SimpleNamespace(invoke=lambda state: {"retrieved": [{"doc_id": "QA-DOUBLE"}], "answer": "TEST DOUBLE"})
    monkeypatch.setattr(resources, "build_diagnosis_graph", graph)
    app = FastAPI()
    app.state.resources = resources.ServiceResources()
    app.include_router(routes.router)
    app.include_router(pilot.router)
    body = {"question": "Which filter checks?", "equipment_id": "EQ-FC-1002"}
    with TestClient(app) as client:
        schema_before = client.get("/openapi.json").json()
        for path in ("/v1/diagnose", "/v2/diagnose"):
            assert client.post(path, json=body).status_code == 200
        assert captured == [(v1, resources.SYSTEM_PROMPT), (v2, pilot.PILOT_PROMPT)]
        monkeypatch.setenv("OPENROUTER_MODEL_V2", changed)
        captured.clear()
        for path in ("/v1/diagnose", "/v2/diagnose"):
            assert client.post(path, json=body).status_code == 200
        assert captured == [(v1, resources.SYSTEM_PROMPT), (changed, pilot.PILOT_PROMPT)]
        assert client.get("/openapi.json").json() == schema_before
        captured.clear()
        for path, statuses in (("/v1/diagnose", [200, 200, 422]), ("/v2/diagnose", [200, 422, 422])):
            bodies = [{"question": "Which filter checks?"}, {"question": "filter " + "x" * 693}, {}]
            assert [client.post(path, json=b).status_code for b in bodies] == statuses
        assert captured == []  # No model on clarification or rejected inputs.


def test_explicit_invalid_model_fails_before_resources_are_opened(monkeypatch):
    def unexpected(self):
        pytest.fail("Invalid selection must fail before opening resources")
    monkeypatch.setattr(resources.ServiceResources, "ready", unexpected)
    with pytest.raises(ValueError, match="model_name"):
        resources.ServiceResources().graph_for(model_name="unapproved/model")


@pytest.mark.parametrize("reported,usage", [(True, True), (True, False), (False, True), (False, False)])
def test_buffered_versions_log_configured_and_reported_models_separately(monkeypatch, tmp_path, reported, usage):
    """Actual routes, LangGraph and logger; only provider/retrieval IO is doubled."""
    import json
    from module_b.openrouter import ChatResponse
    from module_b.observability import ObservationMiddleware
    from fieldcare.evidence import get_equipment_record

    load_example(monkeypatch, "pilot_schemas")
    pilot = load_example(monkeypatch, "pilot_routes")
    brief = load_example(monkeypatch, "brief_routes")
    v1, v2 = sorted(CHAT_MODELS)[:2]
    monkeypatch.setenv("OPENROUTER_MODEL", v1)
    monkeypatch.setenv("OPENROUTER_MODEL_V2", v2)
    model = get_equipment_record("EQ-FC-1002")["model"]
    hit = SimpleNamespace(id="TEST-DOC", text="Synthetic filter guidance", metadata={
        "title": "Synthetic", "applies_to_models": model,
    })
    service_resources = resources.ServiceResources()
    service_resources.store = SimpleNamespace(search=lambda *a, **kw: [hit])
    service_resources.client = SimpleNamespace(chat=lambda *a, **kw: ChatResponse(
        "TEST DOUBLE", kw["model"] if reported else None, "stop",
        {"total_tokens": 12} if usage else None,
    ))
    monkeypatch.setattr(resources.ServiceResources, "ready", lambda self: self)
    app = FastAPI()
    app.state.resources = service_resources
    for router in (routes.router, pilot.router, brief.router):
        app.include_router(router)
    paths = ("/v1/diagnose", "/v2/diagnose", "/v1/diagnose-brief")
    log = tmp_path / "requests.jsonl"
    app.add_middleware(ObservationMiddleware, path=log, routes=paths, approved_models=(v1, v2))
    with TestClient(app) as client:
        for path in paths:
            response = client.post(path, json={"question": "Which filter checks?", "equipment_id": "EQ-FC-1002"})
            assert response.status_code == 200 and response.json()["status"] == "ready"
        assert client.post(paths[0], json={"question": "Which filter checks?"}).status_code == 200
    records = [json.loads(line) for line in log.read_text().splitlines()]
    for row, expected in zip(records[:3], (v1, v2, v1)):
        assert row["configured_model"] == expected
        assert row["model"] == (expected if reported else None)
        assert row["tokens"] == (12 if usage else None)
        assert row["source"] == "live_provider"
    assert records[-1]["configured_model"] is None
    assert records[-1]["model"] is None and records[-1]["source"] == "none"
    assert "TEST DOUBLE" not in log.read_text()
