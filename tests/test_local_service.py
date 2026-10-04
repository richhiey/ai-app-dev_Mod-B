"""Exercise the actual local application without a notebook or ServiceProcess."""

import importlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest
from fastapi.testclient import TestClient
from module_b.security import SecurityMiddleware, LimitPolicy, protected_post_paths
from module_b.observability import ObservationMiddleware

ROOT = Path(__file__).resolve().parents[1]


def fresh_app(monkeypatch, tmp_path, *, secured=False, observed=False, streaming=False):
    monkeypatch.setenv("FIELDCARE_WORK_DIR", str(tmp_path / "var"))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("FIELDCARE_DISPATCH_KEY", "synthetic-dispatch")
    monkeypatch.setenv("FIELDCARE_PARTNER_KEY", "synthetic-partner")
    from fieldcare import main

    app = importlib.reload(main).app
    if streaming:
        from fieldcare.stream_routes import router

        app.include_router(router)
    if secured:
        app.add_middleware(
            SecurityMiddleware,
            caller_env={
                "dispatch": "FIELDCARE_DISPATCH_KEY",
                "partner": "FIELDCARE_PARTNER_KEY",
            },
            protected_paths=protected_post_paths(app),
            policy=LimitPolicy(2, 60),
        )
    if observed:
        app.add_middleware(
            ObservationMiddleware,
            path=tmp_path / "var" / "requests.jsonl",
            routes=protected_post_paths(app),
        )
    return app


def test_startup_and_clarification_need_neither_provider_nor_index(
    monkeypatch, tmp_path
):
    app = fresh_app(monkeypatch, tmp_path)
    with TestClient(app) as client:
        assert client.get("/health").json() == {
            "status": "ok",
            "index_prepared": False,
            "provider_configured": False,
        }
        assert client.post("/v1/diagnose", json={}).status_code == 422
        answer = client.post("/v1/diagnose", json={"question": "Which checks?"})
        assert answer.json()["status"] == "needs_clarification"
        supported = client.post(
            "/v1/diagnose",
            json={"question": "Which filter checks?", "equipment_id": "EQ-FC-1002"},
        )
        assert supported.status_code == 503
        assert "prepare_index" in supported.json()["detail"]
    assert not (tmp_path / "var").exists()


def test_auth_limits_stream_scope_and_log_correlation(monkeypatch, tmp_path):
    app = fresh_app(monkeypatch, tmp_path, secured=True, observed=True, streaming=True)
    dispatch = {"X-API-Key": "synthetic-dispatch"}
    partner = {"X-API-Key": "synthetic-partner"}
    with TestClient(app) as client:
        missing = client.post("/v1/diagnose-stream", json={})
        assert missing.status_code == 401
        assert client.post("/v1/diagnose", headers=dispatch, json={}).status_code == 422
        assert (
            client.post(
                "/v1/diagnose-stream",
                headers=dispatch,
                json={"question": "Which checks?"},
            ).status_code
            == 200
        )
        limited = client.post("/v1/diagnose", headers=dispatch, json={})
        assert limited.status_code == 429 and int(limited.headers["retry-after"]) >= 1
        assert (
            client.post(
                "/v1/diagnose", headers=partner, json={"question": "Which checks?"}
            ).status_code
            == 200
        )
    log = (tmp_path / "var" / "requests.jsonl").read_text()
    records = [json.loads(line) for line in log.splitlines()]
    assert len(records) == 5
    assert records[0]["request_id"] == missing.headers["x-request-id"]
    assert [r["status_code"] for r in records] == [401, 422, 200, 429, 200]
    assert "synthetic-dispatch" not in log and "Which checks?" not in log


def test_local_index_and_real_retrieval_use_provider_boundary_only(
    monkeypatch, tmp_path
):
    import hashlib
    from module_b.openrouter import OpenRouterClient, ChatResponse

    app = fresh_app(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-provider")
    monkeypatch.setattr(
        OpenRouterClient,
        "embed",
        lambda self, texts: [
            [(n + 1) / 256 for n in hashlib.sha256(t.encode()).digest()] for t in texts
        ],
    )
    monkeypatch.setattr(
        OpenRouterClient,
        "chat",
        lambda *a, **kw: ChatResponse(
            "MOCK: check supplied documents.", kw["model"], "stop", {"total_tokens": 12}
        ),
    )
    from fieldcare.prepare_index import main

    main()
    with TestClient(app) as client:
        assert client.get("/health").json()["index_prepared"]
        response = client.post(
            "/v1/diagnose",
            json={"question": "Which filter checks?", "equipment_id": "EQ-FC-1002"},
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ready" and response.json()["citations"]


def test_terminal_uvicorn_lifecycle_on_windows_and_macos(tmp_path):
    """The documented launch command uses ordinary TCP, not POSIX fd passing."""
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = {
        **os.environ,
        "FIELDCARE_WORK_DIR": str(tmp_path / "var"),
        "OPENROUTER_API_KEY": "",
    }
    command = [
        sys.executable,
        "-m",
        "uvicorn",
        "fieldcare.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
    ]
    with (tmp_path / "server.log").open("w+") as output:
        child = subprocess.Popen(
            command, cwd=ROOT, env=env, stdout=output, stderr=subprocess.STDOUT
        )
        try:
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                if child.poll() is not None:
                    output.seek(0)
                    pytest.fail(output.read())
                try:
                    response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=0.5)
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    time.sleep(0.1)
            else:
                pytest.fail("The documented Uvicorn command did not become ready.")
            assert not response.json()["index_prepared"]
            result = httpx.post(
                f"http://127.0.0.1:{port}/v1/diagnose",
                json={"question": "Which checks?"},
            )
            assert result.json()["status"] == "needs_clarification"
        finally:
            child.terminate()
            child.wait(timeout=15)
    assert child.poll() is not None


def test_env_creation_preserves_existing_values_and_hides_keys(
    tmp_path, monkeypatch, capsys
):
    from tools import local_env

    monkeypatch.setattr(local_env, "ROOT", tmp_path)
    local_env.main()
    original = (tmp_path / ".env").read_text()
    values = dict(line.split("=", 1) for line in original.splitlines())
    assert values["FIELDCARE_DISPATCH_KEY"] != values["FIELDCARE_PARTNER_KEY"]
    output = capsys.readouterr().out
    assert values["FIELDCARE_DISPATCH_KEY"] not in output
    with pytest.raises(SystemExit, match="Nothing was overwritten"):
        local_env.main()
    assert (tmp_path / ".env").read_text() == original


def test_documented_attachments_and_stream_preserve_event_identity(
    monkeypatch, tmp_path
):
    import hashlib
    import re
    from module_b.openrouter import OpenRouterClient

    app = fresh_app(monkeypatch, tmp_path)
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-provider")
    monkeypatch.setattr(
        OpenRouterClient,
        "embed",
        lambda self, texts: [
            [(n + 1) / 256 for n in hashlib.sha256(t.encode()).digest()] for t in texts
        ],
    )
    from fieldcare.prepare_index import main as prepare

    prepare()
    from fieldcare import stream_routes

    async def events(context, **kwargs):
        yield {"type": "delta", "text": "MOCK provider fragment"}
        yield {"type": "usage", "model": kwargs["model"], "tokens": 12}

    monkeypatch.setattr(stream_routes, "provider_events", events)
    # Execute the exact student-facing attachment snippets, in documented order.
    sprint2 = re.findall(
        r"```python\n(.*?)```", (ROOT / "docs/sprint-2.md").read_text(), re.S
    )
    sprint3 = re.findall(
        r"```python\n(.*?)```", (ROOT / "docs/sprint-3.md").read_text(), re.S
    )
    namespace = {"app": app}
    exec(sprint3[0], namespace)
    exec(sprint2[0], namespace)
    exec(sprint3[1], namespace)
    with TestClient(app) as client:
        response = client.post(
            "/v1/diagnose-stream",
            headers={"X-API-Key": "synthetic-dispatch"},
            json={"question": "Which filter checks?", "equipment_id": "EQ-FC-1002"},
        )
        received = [json.loads(line) for line in response.text.splitlines()]
        assert [e["type"] for e in received] == [
            "metadata",
            "delta",
            "usage",
            "complete",
        ]
        request_id = response.headers["x-request-id"]
        assert received[0]["request_id"] == received[-1]["request_id"] == request_id
    record = json.loads((tmp_path / "var" / "requests.jsonl").read_text())
    assert record["request_id"] == request_id and record["outcome"] == "completed"
    assert record["tokens"] == 12 and record["source"] == "live_provider"
    assert "MOCK provider fragment" not in json.dumps(record)
    exec(sprint3[2], {})  # The supplied synthetic privacy check must also run.


def test_evaluation_client_runs_original_cases():
    result = subprocess.run(
        [sys.executable, "-m", "clients.evaluate", "EVAL-FC-005", "EVAL-FC-003"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stderr
    assert "original_module_a_deterministic_evaluator" in result.stdout
    assert '"pipeline_pass": true' in result.stdout
