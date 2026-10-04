"""Stream real provider output for supported FieldCare requests."""

import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool
from fieldcare.config import openrouter_model
from fieldcare.resources import SYSTEM_PROMPT

from fieldcare.evidence import get_equipment_record
from fieldcare.schemas import DiagnosticRequest
from fieldcare.service import clarification_for
from module_b.streaming import StreamFailure, encode_event, provider_events

router = APIRouter()


@router.post("/v1/diagnose-stream")
async def diagnose_stream(payload: DiagnosticRequest, request: Request):
    """Retrieve evidence with LangGraph, then forward OpenRouter's SSE deltas."""
    clarification = clarification_for(payload)
    if clarification is not None:
        return JSONResponse(clarification.model_dump())

    equipment = get_equipment_record(payload.equipment_id)
    resources = await run_in_threadpool(request.app.state.resources.ready)
    retrieval = await run_in_threadpool(
        resources.retrieval_graph.invoke,
        {"question": payload.question, "equipment": equipment},
    )
    documents = retrieval["retrieved"]
    if not documents:
        return JSONResponse(
            {
                "answer": "No current service document matched this equipment model and question.",
                "status": "needs_clarification",
                "citations": [],
                "mode": "live",
            }
        )

    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    observation = getattr(request.state, "observation", None)
    if observation is None:
        observation = request.state.observation = {}
    started = time.perf_counter()
    observation.update(
        source="live_provider", model=None, tokens=None, error_category="none"
    )
    context = {
        "question": payload.question,
        "equipment": equipment,
        "documents": documents,
    }

    async def events():
        first_content = True
        try:
            yield encode_event(
                {
                    "type": "metadata",
                    "status": "ready",
                    "citations": [document["doc_id"] for document in documents],
                    "mode": "live",
                    "request_id": request_id,
                }
            )
            async for event in provider_events(
                context,
                model=openrouter_model(),
                system_prompt=SYSTEM_PROMPT,
            ):
                if event["type"] == "delta" and first_content:
                    observation["first_content_ms"] = (
                        time.perf_counter() - started
                    ) * 1000
                    first_content = False
                elif event["type"] == "usage":
                    observation.update(model=event["model"], tokens=event["tokens"])
                yield encode_event(event)
            yield encode_event({"type": "complete", "request_id": request_id})
        except StreamFailure as error:
            observation["error_category"] = str(error)
            yield encode_event(
                {"type": "error", "category": str(error), "request_id": request_id}
            )

    return StreamingResponse(
        events(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-store", "X-Request-ID": request_id},
    )
