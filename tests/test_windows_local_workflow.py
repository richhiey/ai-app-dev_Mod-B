"""Exercise the documented Windows Uvicorn path without provider access."""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

import httpx
import pytest


ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows local-development rehearsal")


def test_windows_uvicorn_auth_limit_stream_and_safe_records(tmp_path):
    entry = tmp_path / "rehearsal.py"
    entry.write_text(
        "from fieldcare.main import app\n"
        "from fieldcare.stream_routes import router\n"
        "from module_b.security import SecurityMiddleware, LimitPolicy, protected_post_paths\n"
        "from module_b.observability import ObservationMiddleware\n"
        "from fieldcare.config import work_dir, openrouter_model\n"
        "app.include_router(router)\n"
        "app.add_middleware(SecurityMiddleware, caller_env={'dispatch':'FIELDCARE_DISPATCH_KEY'}, "
        "protected_paths=protected_post_paths(app), policy=LimitPolicy(allowance=2, window_seconds=1))\n"
        "app.add_middleware(ObservationMiddleware, path=work_dir()/'requests.jsonl', "
        "routes=protected_post_paths(app), approved_models=(openrouter_model(),))\n",
        encoding="utf-8",
    )
    with socket.socket() as reservation:
        reservation.bind(("127.0.0.1", 0))
        port = reservation.getsockname()[1]
    env = os.environ.copy()
    env.update({"PYTHONPATH": os.pathsep.join((str(tmp_path), str(ROOT / "service"), str(ROOT / "src"))),
                "OPENROUTER_API_KEY": "", "FIELDCARE_DISPATCH_KEY": "SYNTHETIC_LOCAL_TEST_ONLY",
                "FIELDCARE_WORK_DIR": str(tmp_path / "var")})
    for key in list(env):
        if key.startswith("UVICORN_") or key == "WEB_CONCURRENCY":
            env.pop(key)
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "rehearsal:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    try:
        with httpx.Client(base_url=f"http://127.0.0.1:{port}", trust_env=False, timeout=3) as client:
            deadline = time.monotonic() + 25
            while True:
                assert process.poll() is None, "Owned Uvicorn process exited before readiness"
                try:
                    health = client.get("/health")
                    if health.status_code == 200:
                        break
                except httpx.TransportError:
                    pass
                assert time.monotonic() < deadline, "Local Uvicorn startup timed out"
                time.sleep(0.1)
            assert health.json()["provider_configured"] is False
            rejected = client.post("/v1/diagnose", json={"question": "Airflow"})
            assert rejected.status_code == 401
            headers = {"X-API-Key": "SYNTHETIC_LOCAL_TEST_ONLY"}
            assert client.post("/v1/diagnose", json={}, headers=headers).status_code == 422
            clarified = client.post("/v1/diagnose-stream", json={"question": "Airflow"}, headers=headers)
            assert clarified.status_code == 200 and clarified.json()["status"] == "needs_clarification"
            limited = client.post("/v1/diagnose", json={"question": "Airflow"}, headers=headers)
            assert limited.status_code == 429
            pid = process.pid
            time.sleep(int(limited.headers["Retry-After"]) + 0.1)
            renewed = client.post("/v1/diagnose", json={"question": "Airflow"}, headers=headers)
            assert renewed.status_code == 200 and renewed.json()["status"] == "needs_clarification"
            assert process.pid == pid and process.poll() is None
            records = [json.loads(line) for line in (tmp_path / "var/requests.jsonl").read_text().splitlines()]
            assert {rejected.headers["X-Request-ID"], clarified.headers["X-Request-ID"]} <= {r["request_id"] for r in records}
            saved = json.dumps(records)
            assert "SYNTHETIC_LOCAL_TEST_ONLY" not in saved and "Airflow" not in saved
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
