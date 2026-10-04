# Follow one request

The local application lives in `service/fieldcare/`. Its server runs in terminal A; a client in terminal B sends an HTTP request to it.

```text
clients/request.py or clients/stream.py
    → observation middleware (once attached)
    → authentication and caller allowance (once attached)
    → FastAPI input validation
    → route and deterministic clarification
    → prepared Chroma index + LangGraph + OpenRouter, when needed
    → JSON response or incremental NDJSON events
    → one minimized terminal record, when observation is attached
```

`main.py` owns registration. Routers are registered before the guard inventories their paths. Observation is attached last so it surrounds authentication rejections as well as admitted requests.

Startup creates a resource manager, not embeddings. `python -m fieldcare.prepare_index` performs the explicit embedding preparation. A supported request opens the prepared index and calls the provider; deterministic clarification does neither. `/health` exposes preparation/configuration state without claiming that generation has succeeded.

`var/` contains generated local state and is ignored by Git. `service/data/` contains supplied synthetic evidence. `evidence/` contains your selected, reviewed observations. These three folders serve different purposes.

The Module A evaluator uses its original reference pipeline and the saved evaluation design. It is a separate source of behavioral evidence, not a scorer for a streamed paragraph.

The separate application in `examples/fieldcare/` supports the existing Sprint 1 and Live notebooks. It is not the local Campus editing location.
