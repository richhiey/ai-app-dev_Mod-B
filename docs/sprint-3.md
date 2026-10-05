# Sprint 3: follow an answer from request to evidence

Your secured FieldCare service is ready for its next step. Continue the local project you built in Sprint 2: let technicians follow an answer as it arrives while keeping the buffered response another application uses. Then trace a request into its safe log and use an existing evaluation case to investigate a concern.

## Register the streaming route

Read `service/fieldcare/stream_routes.py` before attaching it. The route uses `DiagnosticRequest`, checks deterministic clarification, retrieves relevant documents, and forwards real provider events through an async generator. `yield` passes one event to the response without waiting for the whole answer.

Add this registration in `service/fieldcare/main.py` **before** the existing security attachment:

```python
from fieldcare.stream_routes import router as stream_router
app.include_router(stream_router)
```

Do not attach another guard. `protected_post_paths(app)` must now include the streaming path as well as your earlier paths. Save and restart. A missing key on `/v1/diagnose-stream` must receive `401`. A recognized caller sending an empty body receives `422` if it has remaining allowance. A valid question without equipment receives clarification JSON.

## Read a real stream

Prepare the index and provider key if you have not already done so. Open `clients/stream.py`: set `CALLER` to a recognized label in your current `clients/common.py` mapping, such as `operations` after the weekend checkpoint. Keep your existing caller configuration and allowance. Then inspect `httpx.stream`, the `response.iter_lines()` loop and the terminal-event check.

```text
python -m clients.stream
```

A successful supported run displays `metadata`, actual `delta` events and `complete`. `usage` may be absent; keep unknown usage unknown. A provider interruption may produce `error`, a transport exception or an incomplete connection. Partial text is not a completed answer. NDJSON means one JSON event per line; no fixed chunk count or wording is promised.

Change `clients/request.py` to send the same supported question to the buffered endpoint using a caller with allowance. Compare when useful information appears and how completion is represented. These are two separate provider calls, not a benchmark.

## Attach safe request observation

Add this **after** the security attachment. In FastAPI the last middleware added is the outermost wrapper, so this placement includes authentication and limit rejections.

```python
from module_b.observability import ObservationMiddleware
from module_b.security import protected_post_paths
from fieldcare.config import openrouter_model, work_dir

app.add_middleware(
    ObservationMiddleware,
    path=work_dir() / "requests.jsonl",
    routes=protected_post_paths(app),
    approved_models=(openrouter_model(),),
)
```

Restart, then rerun one supported stream and one buffered request with an admitted caller. Keep both new `Request ID` values: attempts made before observation was attached have no saved record. Look up each new ID in turn:

```text
python -m clients.logs YOUR_REQUEST_ID
```

Replace `YOUR_REQUEST_ID` with that actual UUID. You should find one terminal record in `var/requests.jsonl` with the same ID. Compare HTTP status, terminal outcome, model, tokens and timing for the two records. Also send a missing-key request and find its record to check that rejected attempts are observed. Buffered generation may report no usage; do not infer token counts from answer length.

## Check the privacy boundary

Create `clients/privacy_check.py` using this supplied pattern. The marker is synthetic and never sent to the service. It tests minimization, not every possible logging surface.

```python
import json
import uuid
from module_b.observability import safe_record

candidate = {
    "request_id": str(uuid.uuid4()),
    "route": "/v1/diagnose-stream",
    "status_code": 200,
    "outcome": "completed",
    "error_category": "none",
    "prompt": "SYNTHETIC-PRIVATE-MARKER",
    "headers": {"X-API-Key": "SYNTHETIC-PRIVATE-MARKER"},
}
minimized = safe_record(candidate, routes=("/v1/diagnose-stream",))
assert "SYNTHETIC-PRIVATE-MARKER" not in json.dumps(minimized)
assert minimized["request_id"] == candidate["request_id"]
assert minimized["outcome"] == "completed"
print(minimized)
```

Run `python -m clients.privacy_check`. Explain both what was removed and what useful information remains. An empty dictionary would hide the marker but fail the usefulness check. Review actual service logs separately; filtering a copy never removes an earlier unsafe record.

## Investigate with the existing evaluator

Choose a concern from an actual request. Inspect the original cases in `src/module_b/_module_a/data/eval_cases.jsonl`, then select a relevant case and companion case. For example, the original missing-context and equipment-evidence cases can be run with:

```text
python -m clients.evaluate EVAL-FC-005 EVAL-FC-003
```

The command prints original case definitions, actual deterministic evaluation results and a design hash. It uses the unchanged Module A evaluator with `service/data/pipeline_design.json`. That file configures the reference pipeline, not the live OpenRouter graph. These results do not grade the streamed wording or prove production behavior. The operational record motivates the evaluation choice; it is not replayed as a private prompt.

For your checkpoint, choose your own justified case pair and preserve the original criteria. Submit one traceable request, its selected safe record, your privacy check and the evaluation reasoning. Follow the [evidence template](../evidence/README.md).
