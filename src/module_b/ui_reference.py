"""Public local UI reference; never changes the learner's cumulative service.

Fixture mode exercises HTTP, streaming, authentication and observation without AI.
Provider mode mounts the existing FieldCare streaming route and real resources.
"""
import argparse
import asyncio
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import secrets
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from fieldcare.config import ROOT, openrouter_model
from fieldcare.schemas import DiagnosticRequest
from fieldcare.service import clarification_for
from module_b.observability import ObservationMiddleware
from module_b.security import LimitPolicy, SecurityMiddleware
from module_b.streaming import encode_event

STATE = ROOT / "var" / "ui-reference"
STREAM_PATH = "/v1/diagnose-stream"


def create_app(mode="fixture", *, log_path=None):
    if mode not in {"fixture", "provider"}:
        raise ValueError("Choose fixture or provider mode.")

    @asynccontextmanager
    async def lifespan(app):
        if mode == "provider":
            from fieldcare.resources import ServiceResources
            app.state.resources = ServiceResources()
        try:
            yield
        finally:
            if mode == "provider":
                app.state.resources.close()

    app = FastAPI(title=f"FieldCare public UI reference ({mode})", lifespan=lifespan)

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": mode, "provider_verified": False}

    if mode == "provider":
        from fieldcare.stream_routes import router
        app.include_router(router)
    else:
        @app.post(STREAM_PATH)
        async def fixture(payload: DiagnosticRequest, request: Request):
            clarification = clarification_for(payload)
            if clarification is not None:
                return JSONResponse({**clarification.model_dump(), "mode": "fixture"})
            request_id = request.state.request_id

            async def events():
                yield encode_event({"type": "metadata", "status": "ready", "mode": "fixture",
                                    "citations": [], "request_id": request_id})
                for text in ("FIXTURE ONLY — ", "the local request and stream worked. ",
                             "No model was called; this is not equipment guidance."):
                    yield encode_event({"type": "delta", "text": text})
                    await asyncio.sleep(0.03)
                yield encode_event({"type": "complete", "request_id": request_id})
            return StreamingResponse(events(), media_type="application/x-ndjson")

    app.add_middleware(SecurityMiddleware, caller_env={"reference": "FIELDCARE_REFERENCE_KEY"},
                       protected_paths=(STREAM_PATH,), policy=LimitPolicy(4, 60))
    app.add_middleware(ObservationMiddleware, path=log_path or STATE / f"{mode}-events.jsonl",
                       routes=(STREAM_PATH,), approved_models=(openrouter_model(),) if mode == "provider" else ())
    return app


def initialize(ui_dir):
    """Create a fresh pair of private local configs; never overwrite existing files."""
    ui_dir = Path(ui_dir).resolve()
    if not (ui_dir / "package.json").is_file():
        raise ValueError("Choose the UI directory containing package.json.")
    service_env, ui_env = STATE / "reference.env", ui_dir / ".env.local"
    if service_env.exists() or ui_env.exists():
        raise ValueError("Configuration already exists. Reuse it; inspect private files to configure another UI manually.")
    ignore = ui_dir / ".gitignore"
    with ignore.open("a") as stream:
        stream.write("\n# Private local FieldCare bridge configuration\n.env.local\n")
    STATE.mkdir(parents=True, exist_ok=True)
    key = secrets.token_urlsafe(32)
    for target, body in (
        (service_env, f"FIELDCARE_REFERENCE_KEY={key}\n"),
        (ui_env, f"FIELDCARE_SERVICE_URL=http://127.0.0.1:8001\nFIELDCARE_CALLER_KEY={key}\n"),
    ):
        descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as stream:
            stream.write(body)
    print("Created private service and UI configuration. No keys printed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--ui-dir", required=True)
    serve = commands.add_parser("serve")
    serve.add_argument("--mode", choices=("fixture", "provider"), default="fixture")
    show = commands.add_parser("show-log")
    show.add_argument("--mode", choices=("fixture", "provider"), required=True)
    show.add_argument("--request-id", required=True)
    args = parser.parse_args()
    if args.command == "init":
        initialize(args.ui_dir)
    elif args.command == "serve":
        import uvicorn
        load_dotenv(STATE / "reference.env", override=False)
        if not os.getenv("FIELDCARE_REFERENCE_KEY"):
            parser.error("Run init first; reference caller configuration is missing.")
        # Keep framework access/exception output out of the teaching evidence.
        uvicorn.run(create_app(args.mode), host="127.0.0.1", port=8001,
                    access_log=False, log_level="critical")
    else:
        request_id = str(uuid.UUID(args.request_id))
        path = STATE / f"{args.mode}-events.jsonl"
        records = [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
        matches = [record for record in records if record["request_id"] == request_id]
        print(json.dumps({"mode": args.mode, "records": matches}, indent=2))
        if not matches:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
