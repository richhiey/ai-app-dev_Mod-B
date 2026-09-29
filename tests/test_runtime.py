"""Real loopback HTTP tests, using a tiny app unrelated to FieldCare logic."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from urllib.error import URLError
from urllib.request import Request, urlopen

import pytest

from module_b.runtime import ServiceProcess

pytestmark = pytest.mark.skipif(os.name != "posix", reason="Descriptor handoff targets Linux and macOS.")


@pytest.fixture
def project(tmp_path):
    (tmp_path / "tiny_app.py").write_text('''
import os
from fastapi import FastAPI
app = FastAPI()
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/echo")
def echo(body: dict):
    return {"received": body}
@app.get("/configuration")
def configuration():
    return {"mode": os.getenv("EXAMPLE_MODE"),
            "secret_present": "EXAMPLE_SECRET" in os.environ,
            "inherited_present": "INHERITED_SENTINEL" in os.environ,
            "dotenv_loaded": "DOTENV_ONLY_SENTINEL" in os.environ,
            "env_names": sorted(os.environ)}
''')
    (tmp_path / ".env").write_text("DOTENV_ONLY_SENTINEL=must-not-load\nEXAMPLE_MODE=from-dotenv\n")
    return tmp_path


def fetch(url, payload=None):
    request = Request(url, data=None if payload is None else json.dumps(payload).encode(),
                      headers={} if payload is None else {"Content-Type": "application/json"})
    with urlopen(request, timeout=2) as response:
        return response.status, json.load(response)


def test_real_tcp_readiness_request_and_owned_context_cleanup(project):
    process = ServiceProcess("tiny_app:app", project_dir=project)
    with process as running:
        assert running is process
        assert process.is_running and process.pid is not None
        base = process.base_url
        assert base.startswith("http://127.0.0.1:")
        assert fetch(base + "/health") == (200, {"status": "ok"})
        assert fetch(base + "/echo", {"question": "synthetic example"}) == (200, {"received": {"question": "synthetic example"}})
    assert not process.is_running and process.pid is None and process.base_url is None
    with pytest.raises((URLError, OSError)):
        fetch(base + "/health")


def test_repeat_start_reuses_owned_child_then_restart_gets_new_child(project):
    process = ServiceProcess("tiny_app:app", project_dir=project)
    try:
        process.start()
        pid, base = process.pid, process.base_url
        assert process.start() is process
        assert (process.pid, process.base_url) == (pid, base)
        process.stop()
        process.stop()
        assert not process.is_running
        process.start()
        assert process.pid != pid
        assert fetch(process.base_url + "/health")[0] == 200
    finally:
        process.stop()


def test_explicit_environment_overrides_and_removals_without_dotenv(project, monkeypatch):
    monkeypatch.setenv("EXAMPLE_MODE", "inherited-mode")
    monkeypatch.setenv("EXAMPLE_SECRET", "synthetic-inherited-secret")
    monkeypatch.setenv("INHERITED_SENTINEL", "preserved")
    monkeypatch.delenv("DOTENV_ONLY_SENTINEL", raising=False)
    monkeypatch.setenv("UVICORN_ENV_FILE", str(project / ".env"))
    monkeypatch.setenv("UVICORN_WORKERS", "4")
    monkeypatch.setenv("WEB_CONCURRENCY", "4")
    with ServiceProcess("tiny_app:app", project_dir=project,
                        env={"EXAMPLE_MODE": "explicit-mode", "EXAMPLE_SECRET": None,
                             "UVICORN_ENV_FILE": str(project / ".env")}) as process:
        configuration = fetch(process.base_url + "/configuration")[1]
        assert configuration["mode"] == "explicit-mode"
        assert configuration["secret_present"] is False
        assert configuration["inherited_present"] is True
        assert configuration["dotenv_loaded"] is False
        assert not any(name.startswith("UVICORN_") for name in configuration["env_names"])
        assert "WEB_CONCURRENCY" not in configuration["env_names"]
    assert os.environ["EXAMPLE_SECRET"] == "synthetic-inherited-secret"
    assert os.environ["EXAMPLE_MODE"] == "inherited-mode"


def test_empty_environment_accepts_explicit_settings_and_injects_no_case_policy(project, monkeypatch):
    monkeypatch.setenv("EXAMPLE_SECRET", "synthetic-parent-secret")
    monkeypatch.setenv("INHERITED_SENTINEL", "not-inherited")
    with ServiceProcess("tiny_app:app", project_dir=project, inherit_env=False,
                        env={"EXAMPLE_MODE": "isolated", "EXAMPLE_SECRET": None}) as process:
        configuration = fetch(process.base_url + "/configuration")[1]
        assert configuration["mode"] == "isolated"
        assert configuration["secret_present"] is False
        assert configuration["inherited_present"] is False
        assert configuration["dotenv_loaded"] is False
        assert not any(name.startswith(("FIELDCARE_", "OPENROUTER_")) for name in configuration["env_names"])


def test_occupied_explicit_port_is_preserved(project):
    with ServiceProcess("tiny_app:app", project_dir=project) as existing:
        original_pid = existing.pid
        port = int(existing.base_url.rsplit(":", 1)[1])
        contender = ServiceProcess("tiny_app:app", project_dir=project, port=port)
        with pytest.raises(RuntimeError, match="Cannot reserve"):
            contender.start()
        contender.stop()
        assert contender.pid is None
        assert existing.pid == original_pid and existing.is_running
        assert fetch(existing.base_url + "/health") == (200, {"status": "ok"})


def test_failed_startup_reaps_child_and_releases_port(project, monkeypatch):
    (project / "broken_app.py").write_text('raise RuntimeError("synthetic-private-error-secret")\n')
    children = []
    real_popen = subprocess.Popen

    def remember(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr("module_b.runtime.subprocess.Popen", remember)
    with socket.socket() as reserved:
        reserved.bind(("127.0.0.1", 0))
        port = reserved.getsockname()[1]
    process = ServiceProcess("broken_app:app", project_dir=project, port=port, startup_timeout=3)
    with pytest.raises(RuntimeError) as error:
        process.start()
    assert "synthetic-private-error-secret" not in str(error.value)
    assert children and all(child.poll() is not None for child in children)
    assert process.pid is None and not process.is_running
    with ServiceProcess("tiny_app:app", project_dir=project, port=port) as replacement:
        assert fetch(replacement.base_url + "/health")[0] == 200


def test_health_timeout_stops_child(project, monkeypatch):
    children = []
    real_popen = subprocess.Popen

    def remember(*args, **kwargs):
        child = real_popen(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr("module_b.runtime.subprocess.Popen", remember)
    process = ServiceProcess("tiny_app:app", project_dir=project, health_path="/absent", startup_timeout=1)
    with pytest.raises(RuntimeError, match="timeout"):
        process.start()
    assert children and all(child.poll() is not None for child in children)
    assert not process.is_running and process.pid is None


def test_health_does_not_follow_redirects(project):
    (project / "redirect_app.py").write_text('''
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
app = FastAPI()
@app.get("/health")
def health(): return RedirectResponse("/different")
@app.get("/different")
def other(): return {"status": "ok"}
''')
    process = ServiceProcess("redirect_app:app", project_dir=project, startup_timeout=1)
    with pytest.raises(RuntimeError, match="timeout"):
        process.start()
    assert not process.is_running


def test_atexit_stops_owned_child_when_parent_exits(project):
    code = (
        "from pathlib import Path; from module_b.runtime import ServiceProcess; "
        f"p=ServiceProcess('tiny_app:app', project_dir=Path({str(project)!r})).start(); "
        "print(p.base_url, flush=True)"
    )
    env = os.environ.copy()
    # Works both for an installed package and an authoring source-tree run.
    source_root = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = source_root
    result = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True, text=True, timeout=20, check=True)
    base = result.stdout.strip()
    assert base.startswith("http://127.0.0.1:")
    with pytest.raises((URLError, OSError)):
        fetch(base + "/health")


@pytest.fixture
def factory_project(tmp_path):
    # A plain ASGI factory: no FastAPI routes, models or case-specific helpers.
    (tmp_path / "factory_app.py").write_text('''

def make_app():
    async def application(scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                event = await receive()
                if event["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                elif event["type"] == "lifespan.shutdown":
                    await send({"type": "lifespan.shutdown.complete"})
                    return
        elif scope["type"] == "http":
            headers = dict(scope["headers"])
            if scope["path"] != "/ready":
                status = 404
            elif headers.get(b"x-health-token") != b"synthetic-health-token":
                status = 403
            else:
                status = 204
            await send({"type": "http.response.start", "status": status, "headers": []})
            await send({"type": "http.response.body", "body": b""})
    return application
''')
    return tmp_path


def test_plain_asgi_factory_custom_readiness_status_and_private_headers(factory_project):
    headers = {"X-Health-Token": "synthetic-health-token"}
    with ServiceProcess("factory_app:make_app", project_dir=factory_project,
                        factory=True, inherit_env=False, health_path="/ready",
                        health_status=204, health_headers=headers) as process:
        pid = process.pid
        assert process.start().pid == pid
        request = Request(process.base_url + "/ready", headers=headers)
        with urlopen(request, timeout=2) as response:
            assert response.status == 204 and response.read() == b""


def test_failed_authenticated_health_never_exposes_header_values(factory_project):
    process = ServiceProcess("factory_app:make_app", project_dir=factory_project,
                             factory=True, health_path="/ready", health_status=204,
                             health_headers={"X-Health-Token": "synthetic-private-wrong-token"},
                             startup_timeout=1)
    with pytest.raises(RuntimeError, match="timeout") as error:
        process.start()
    assert "synthetic-private-wrong-token" not in str(error.value)
    assert not process.is_running and process.pid is None
