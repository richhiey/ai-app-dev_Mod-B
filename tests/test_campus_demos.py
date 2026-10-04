"""Check the supplied demonstrations without claiming real provider output."""
from contextlib import asynccontextmanager
import hashlib
import json
from pathlib import Path
import sys
import zipfile

import pytest
from fastapi.testclient import TestClient
from module_b.campus import prepare_project, save_checkpoint, read_request_records

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples" / "fieldcare"))
from app import campus_demo


@pytest.fixture
def demo(monkeypatch, tmp_path):
    @asynccontextmanager
    async def no_provider(app):
        app.state.document_store = object()
        app.state.openrouter_client = object()
        app.state.model_name = "google/gemini-3.1-flash-lite"
        app.state.diagnosis_graph = None  # clarification never invokes it
        yield
    monkeypatch.setattr(campus_demo, "lifespan", no_provider)
    monkeypatch.setenv("FIELDCARE_DISPATCH_KEY", "synthetic-dispatch")
    monkeypatch.setenv("FIELDCARE_PARTNER_KEY", "synthetic-partner")
    monkeypatch.setenv("FIELDCARE_LOG_PATH", str(tmp_path / "requests.jsonl"))
    return campus_demo.create_app


def test_version_contract_and_rerun_do_not_mutate_base_app(demo, monkeypatch):
    monkeypatch.setenv("CAMPUS_SPRINT", "1")
    from app.main import app as learner_app
    initial = learner_app.openapi()
    for _ in range(2):
        with TestClient(demo()) as client:
            body = {"question": "filter " + "x" * 693}
            assert client.post("/v1/diagnose", json=body).json()["status"] == "needs_clarification"
            assert client.post("/v2/diagnose", json=body).status_code == 422
    assert learner_app.openapi() == initial
    assert "/v2/diagnose" not in initial["paths"]


def test_auth_limit_counts_invalid_and_spans_versions(demo, monkeypatch):
    monkeypatch.setenv("CAMPUS_SPRINT", "2")
    monkeypatch.setenv("CAMPUS_ALLOWANCE", "2")
    d = {"X-API-Key": "synthetic-dispatch"}
    p = {"X-API-Key": "synthetic-partner"}
    body = {"question": "filter"}
    with TestClient(demo()) as client:
        outcomes = [client.post("/v1/diagnose", json=body).status_code,
                    client.post("/v1/diagnose", json={}, headers=d).status_code,
                    client.post("/v1/diagnose", json=body, headers=d).status_code]
        limited = client.post("/v2/diagnose", json=body, headers=d)
        outcomes += [limited.status_code, client.post("/v1/diagnose", json=body, headers=p).status_code]
    assert outcomes == [401, 422, 200, 429, 200]
    assert 1 <= int(limited.headers["retry-after"]) <= 60


def test_logger_wraps_auth_and_keeps_request_correlation(demo, monkeypatch, tmp_path):
    monkeypatch.setenv("CAMPUS_SPRINT", "3")
    monkeypatch.setenv("CAMPUS_ALLOWANCE", "4")
    with TestClient(demo()) as client:
        rejected = client.post("/v1/diagnose-stream", json={"question": "PRIVATE-SYNTHETIC"})
        clarified = client.post("/v1/diagnose-stream", json={"question": "filter"},
                                headers={"X-API-Key": "synthetic-dispatch"})
    ids = [r.headers["x-request-id"] for r in (rejected, clarified)]
    records = read_request_records(tmp_path / "requests.jsonl", ids)
    assert len(records) == 2
    assert {r["status_code"] for r in records} == {200, 401}
    assert records[0]["error_category"] == "unauthorized"
    assert records[1]["source"] == "none"
    assert "PRIVATE-SYNTHETIC" not in json.dumps(records)
    assert "synthetic-dispatch" not in json.dumps(records)
    assert clarified.json()["status"] == "needs_clarification"


def test_buffered_generation_reports_source_without_inventing_usage(demo, monkeypatch, tmp_path):
    from app import routes
    from app.schemas import DiagnosticResponse
    monkeypatch.setenv("CAMPUS_SPRINT", "3")
    monkeypatch.setenv("CAMPUS_ALLOWANCE", "4")
    monkeypatch.setattr(routes, "run_diagnosis", lambda *a, **k: DiagnosticResponse(
        answer="Explicit mocked-provider test", status="ready", citations=[], mode="live"))
    with TestClient(demo()) as client:
        response = client.post('/v1/diagnose', json={'question': 'filter'},
                               headers={'X-API-Key': 'synthetic-dispatch'})
    record = read_request_records(tmp_path / 'requests.jsonl', [response.headers['x-request-id']])[0]
    assert record['source'] == 'live_provider'
    assert record['model'] is None and record['tokens'] is None


def test_project_export_restore_preserves_edits_and_excludes_logs(tmp_path):
    project = prepare_project(ROOT, tmp_path / "project")
    (project / "app" / "my_route.py").write_text("# learner-owned route\n")
    (project / "logs").mkdir()
    (project / "logs" / "raw.jsonl").write_text("private data")
    archive = save_checkpoint(project, tmp_path, 1)
    restored = prepare_project(ROOT, tmp_path / "restored", archive)
    assert (restored / "app" / "my_route.py").read_text() == "# learner-owned route\n"
    assert not (restored / "logs").exists()
    with pytest.raises(FileExistsError):
        prepare_project(ROOT, restored, archive)
    assert prepare_project(ROOT, restored) == restored


def test_legacy_checkpoint_is_supported_and_unsafe_paths_are_rejected(tmp_path):
    archive = tmp_path / "legacy.zip"
    with zipfile.ZipFile(archive, "w") as out:
        out.writestr("app/main.py", "# preserved legacy source\n")
    restored = prepare_project(ROOT, tmp_path / "legacy", archive)
    assert (restored / "app/main.py").read_text() == "# preserved legacy source\n"
    unsafe = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(unsafe, "w") as out:
        out.writestr("../escaped.py", "invalid")
    with pytest.raises(ValueError):
        prepare_project(ROOT, tmp_path / "unsafe", unsafe)
    assert not (tmp_path / "escaped.py").exists()


def test_delivered_campus_cells_do_not_generate_source_or_reveal_solutions():
    for sprint, name in [(1, "service_foundations"), (2, "secure_service"), (3, "observable_service")]:
        path = ROOT / f"notebooks/sprint_{sprint}/sprint_{sprint}_{name}.ipynb"
        notebook = json.loads(path.read_text())
        sources = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
        for source in sources:
            assert not any(s in source for s in ["write_text(", "write_bytes(", "%%writefile", "main_source", "exec("])
        assert not any(c.get("outputs") for c in notebook["cells"])
        assert len({c["id"] for c in notebook["cells"]}) == len(notebook["cells"])
        if sprint == 2:
            assert "MY_REQUEST_PLAN = []" in "\n".join(sources)


def test_stream_source_is_the_same_supplied_pattern():
    assert (ROOT / "examples/fieldcare/app/stream_routes.py").read_bytes() == (
        ROOT / "examples/patterns/sprint_3/stream_routes.py").read_bytes()
