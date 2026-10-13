"""Incremental answer route for the domain-neutral Live concept API."""

import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from module_b.streaming import StreamFailure, encode_event, provider_events

from .schemas import AnswerRequest
from .service import BASE_PROMPT, selected_model

router = APIRouter()


@router.post("/v1/answer-stream")
async def answer_stream(payload: AnswerRequest, request: Request):
    if payload.context is None or not payload.context.strip():
        return JSONResponse({"answer": None, "status": "needs_context", "references": []})
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    observation = getattr(request.state, "observation", None)
    if observation is None:
        observation = request.state.observation = {}
    started = time.perf_counter()
    model = selected_model()
    observation.update(source="live_provider", configured_model=model,
                       model=None, tokens=None, error_category="none")

    async def events():
        first_content = True
        try:
            yield encode_event({"type": "metadata", "status": "ready",
                                "references": ["provided_context"], "mode": "live",
                                "request_id": request_id})
            async for event in provider_events(
                {"question": payload.question, "context": payload.context},
                model=model, system_prompt=BASE_PROMPT,
            ):
                if event["type"] == "model":
                    observation["model"] = event["model"]
                    continue
                if event["type"] == "delta" and first_content:
                    observation["first_content_ms"] = (time.perf_counter() - started) * 1000
                    first_content = False
                elif event["type"] == "usage":
                    observation.update(model=event["model"], tokens=event["tokens"])
                yield encode_event(event)
            yield encode_event({"type": "complete", "request_id": request_id})
        except StreamFailure as error:
            observation["error_category"] = str(error)
            yield encode_event({"type": "error", "category": str(error),
                                "request_id": request_id})

    return StreamingResponse(events(), media_type="application/x-ndjson",
                             headers={"Cache-Control": "no-store", "X-Request-ID": request_id})
