"""Independent LS13–LS14 teaching surface of the course service.

Reuses the neutral Live API and the course security/observation/OpenRouter code.
Fixture mode is explicit and makes no model call. No Campus equipment is used.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PRIVATE = HERE / ".private"


def initialize():
    PRIVATE.mkdir(mode=0o700, exist_ok=True)
    paths = [PRIVATE / "service.json", PRIVATE / "ui.json"]
    if any(p.exists() for p in paths):
        raise SystemExit("Private settings already exist. Keep them; nothing was overwritten.")
    reader, editor = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    values = [{"WORKSHOP_READER_KEY": reader, "WORKSHOP_EDITOR_KEY": editor},
              {"base_url": "http://127.0.0.1:8013", "caller_key": reader}]
    for path, value in zip(paths, values):
        with path.open("x") as stream:
            json.dump(value, stream)
        path.chmod(0o600)
    print("Private service and UI settings created. No credential values were displayed.")


def build_app(mode):
    # Model configuration is read in the service process, never by app.py.
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env", override=False)
    settings_path = PRIVATE / "service.json"
    if not settings_path.exists():
        raise SystemExit("Run server.py init before starting the service.")
    settings = json.loads(settings_path.read_text())
    for name in ("WORKSHOP_READER_KEY", "WORKSHOP_EDITOR_KEY"):
        os.environ[name] = settings[name]
    os.environ["WORKSHOP_WORK_DIR"] = str(PRIVATE / "var")
    sys.path.insert(0, str(HERE.parent))
    if mode == "provider":
        from sprint1_concept_api.live_observed import app
        return app

    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, StreamingResponse
    from sprint1_concept_api.schemas import AnswerRequest
    from sprint1_concept_api.security_settings import CALLER_ENV
    from sprint1_concept_api.service import selected_model
    from module_b.observability import ObservationMiddleware
    from module_b.security import LimitPolicy, SecurityMiddleware, protected_post_paths
    from module_b.streaming import encode_event

    app = FastAPI(title="Live concept API: labelled HTTP fixture")

    @app.get("/health")
    def health():
        return {"status": "ready", "mode": "fixture"}

    @app.post("/v1/answer-stream")
    def answer_stream(payload: AnswerRequest, request: Request):
        if payload.context is None or not payload.context.strip():
            return JSONResponse({"answer": None, "status": "needs_context", "references": []})
        request_id = request.state.request_id

        def events():
            yield encode_event({"type": "metadata", "request_id": request_id,
                                "references": ["provided_context"], "mode": "fixture"})
            yield encode_event({"type": "delta", "text": "FIXTURE ONLY: A useful note "})
            yield encode_event({"type": "delta", "text": "states the decision and names its owner."})
            yield encode_event({"type": "complete", "request_id": request_id})

        return StreamingResponse(events(), media_type="application/x-ndjson")

    paths = protected_post_paths(app)
    app.add_middleware(SecurityMiddleware, caller_env=CALLER_ENV, protected_paths=paths,
                       policy=LimitPolicy(allowance=2, window_seconds=60))
    app.add_middleware(ObservationMiddleware, path=PRIVATE / "var" / "requests.jsonl",
                       routes=paths, approved_models=(selected_model(),))
    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("init", "serve", "record"))
    parser.add_argument("--mode", choices=("fixture", "provider"), default="fixture")
    parser.add_argument("--request-id")
    args = parser.parse_args()
    if args.action == "init":
        initialize()
    elif args.action == "serve":
        import uvicorn
        print(f"Mode: {args.mode}; two admissions per caller per 60 seconds. Restart resets counters.")
        uvicorn.run(build_app(args.mode), host="127.0.0.1", port=8013)
    else:
        import uuid
        try:
            selected = str(uuid.UUID(args.request_id))
        except (ValueError, TypeError, AttributeError):
            raise SystemExit("Use --request-id with the actual UUID displayed for the attempt.")
        path = PRIVATE / "var" / "requests.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        matches = [row for row in rows if row.get("request_id") == selected]
        print(json.dumps(matches, indent=2))
        if not matches:
            print("No matching record in this lab. Check the exact response ID and service target.")


if __name__ == "__main__":
    main()
