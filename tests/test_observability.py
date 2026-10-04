"""Unit checks for log minimization, OpenRouter SSE parsing and Module A evaluation."""
import asyncio
import hashlib
import json
import uuid

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from module_b._module_a import project as module_a
from module_b.evaluation import evaluate_selected
from module_b.observability import FIELDS, ObservationMiddleware, safe_record
from module_b.streaming import StreamFailure, provider_events

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_allowlist_discards_unapproved_text_and_invalid_numeric_values():
    marker = "SYNTHETIC-private@example.invalid"
    row = safe_record(
        {
            "request_id": str(uuid.uuid4()), "prompt": marker,
            "error": {"secret": marker}, "model": marker, "tokens": True,
            "latency_ms": float("nan"), "route": "/" + marker,
            "error_category": marker,
        },
        routes=["/safe"],
    )
    assert marker not in json.dumps(row)
    assert row["tokens"] is None and row["model"] is None
    assert row["route"] == "unmatched" and row["error_category"] == "internal_error"
    assert set(row) == set(FIELDS)


def test_observation_middleware_records_safe_http_metadata(tmp_path):
    app = FastAPI()
    app.add_middleware(
        ObservationMiddleware, path=tmp_path / "requests.jsonl",
        routes=("/v1/check",),
    )

    @app.post("/v1/check")
    def check(_body: dict):
        return {"status": "accepted"}

    marker = "SYNTHETIC-PRIVATE-MARKER"
    with TestClient(app) as client:
        response = client.post("/v1/check", json={"question": marker})
    assert response.status_code == 200
    assert response.headers.get("x-request-id")
    record = json.loads((tmp_path / "requests.jsonl").read_text())
    assert record["route"] == "/v1/check" and record["outcome"] == "completed"
    assert marker not in json.dumps(record)


def test_existing_request_id_header_is_not_duplicated(tmp_path):
    from fastapi import Request
    from fastapi.responses import JSONResponse
    app = FastAPI()
    app.add_middleware(ObservationMiddleware, path=tmp_path / 'requests.jsonl', routes=('/stream',))

    @app.post('/stream')
    def stream(request: Request):
        return JSONResponse({'ok': True}, headers={'X-Request-ID': request.state.request_id})

    with TestClient(app) as client:
        response = client.post('/stream')
    record = json.loads((tmp_path / 'requests.jsonl').read_text())
    assert response.headers.get_list('x-request-id') == [record['request_id']]


def test_provider_event_parser_accepts_complete_real_protocol_shape(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "SYNTHETIC-TEST-KEY")
    monkeypatch.setenv("OPENROUTER_MODEL", "approved")
    body = (
        'data: {"choices":[{"delta":{"content":"step "}}]}\n\n'
        'data: {"choices":[{"delta":{"content":"one"},"finish_reason":"stop"}],'
        '"model":"approved","usage":{"total_tokens":17}}\n\n'
        'data: [DONE]\n\n'
    )

    async def collect():
        def respond(_request):
            return httpx.Response(200, text=body)
        transport = httpx.MockTransport(respond)
        return [event async for event in provider_events(
            {}, model="approved", system_prompt="Use only supplied evidence.", transport=transport
        )]

    assert asyncio.run(collect()) == [
        {"type": "delta", "text": "step "},
        {"type": "delta", "text": "one"},
        {"type": "usage", "model": "approved", "tokens": 17},
    ]


@pytest.mark.parametrize("body", [
    "",
    'data: {"error":{"message":"SYNTHETIC-PRIVATE"}}\n\n',
    'data: {"choices":[{"finish_reason":"length"}]}\n\ndata: [DONE]\n\n',
])
def test_provider_event_parser_fails_safely_on_incomplete_or_error_frames(monkeypatch, body):
    monkeypatch.setenv("OPENROUTER_API_KEY", "SYNTHETIC-TEST-KEY")
    monkeypatch.setenv("OPENROUTER_MODEL", "approved")

    async def collect():
        def respond(_request):
            return httpx.Response(200, text=body)
        async for _event in provider_events(
            {}, model="approved", system_prompt="Use only supplied evidence.",
            transport=httpx.MockTransport(respond),
        ):
            pass

    with pytest.raises(StreamFailure) as error:
        asyncio.run(collect())
    assert "SYNTHETIC" not in str(error.value)


def test_original_module_a_evaluator_detects_a_pipeline_design_regression(tmp_path):
    design_path = tmp_path / "pipeline_design.json"
    design_path.write_text(json.dumps(module_a.default_pipeline_design()))
    before = evaluate_selected(design_path, ["EVAL-FC-005", "EVAL-FC-003"])
    design = json.loads(design_path.read_text())
    design["response_policy"]["ask_before_model_specific_guidance_when_ids_missing"] = False
    design_path.write_text(json.dumps(design))
    after = evaluate_selected(design_path, ["EVAL-FC-005", "EVAL-FC-003"])
    assert before["rows"][0]["pipeline_pass"]
    assert not after["rows"][0]["pipeline_pass"]
    assert after["rows"][1]["pipeline_pass"]
    assert after["design_revision"] != before["design_revision"]


def test_bundled_module_a_evaluator_matches_its_provenance_hashes():
    vendor = ROOT / "src/module_b/_module_a"
    provenance = json.loads((vendor / "provenance.json").read_text())
    for name, digest in provenance["files"].items():
        assert hashlib.sha256((vendor / name).read_bytes()).hexdigest() == digest, name
    assert "actual pipeline run" in module_a.evaluate_case.__doc__
