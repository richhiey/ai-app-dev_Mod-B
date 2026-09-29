# Streaming and observability contract

The single Sprint 3 notebook imports a student Sprint 2 checkpoint without replacing its source. New static routes register before `SecurityMiddleware` captures the protected inventory. `ObservationMiddleware` is added outside it so rejections are visible too. The incoming policy is preserved. Demo recovery uses two callers and four admissions per 60 seconds; the live Sprint 2 workshop export uses two. The bounded probe supports 1–20 admissions and windows of at least 30 seconds; other policies need an appropriately designed separate probe.

## Delivery

`/v1/fieldcare-stream` emits NDJSON `delta`, `complete` or `error` events. `/v1/fieldcare-buffered` collects the same event source and returns a complete JSON object. Both are explicitly added replay routes, not silent changes to `/v1/diagnose` or student handover contracts. A replay selects one of the original synthetic `EVAL-FC-001` through `016` cases; an optional question override is for controlled experiments and invalidates an automatic assumption of case equivalence.

The default delayed fixture exercises incremental HTTP arrival, interruption and cancellation. It does not generate model text or measured model token counts. `FIELDCARE_STREAM_MODE=live` uses the separate OpenRouter adapter, forwarding genuine incremental content and requiring clean stop/termination. Comments and multiline SSE frames are parsed, raw errors are replaced by fixed categories, and provider usage is used only when supplied. The fixture-only fault setting has no effect in live mode. Upstream connection cleanup does not guarantee every provider stops billed generation.

HTTP status precedes the terminal event. A 200 can still end with an error; partial content is not a completed answer. Cancellation can race with a completed response. The owned local runtime disables access logging and discards stdout/stderr. Deployment proxy/platform logs are outside this notebook's verification scope.

## Retained metadata

The explicit field allowlist is `request_id`, `route`, `status_code`, `outcome`, `source`, `model`, `tokens`, `latency_ms`, `first_content_ms`, `error_category`, `case_id`. Values are validated; arbitrary nested objects and unknown fields are excluded. A server-generated UUID correlates one terminal request record with `X-Request-ID`. An approved model name is retained when reported; otherwise it is null. Missing usage is null, never an invented count or cost.

No prompt, response body, full URL query, headers or exception text belongs in the record. Synthetic marker tests exercise normal, rejected, invalid nested input and interrupted requests, with positive metadata checks. These are bounded regression checks, not general personal-data detection.

## Authentic Module A integration

`src/module_b/_module_a/project.py` retains the application/evaluator functions from the local Module A course source. Relative imports and bundled-asset I/O replace notebook environment discovery. Retrieval/tool primitives come from the verified upstream commit recorded in `provenance.json`. The evolving upstream project's current evaluator differs from this course snapshot, so it is not silently substituted.

`/v1/fieldcare-evidence` and `load_pipeline(design_path)` use the same saved design. The service captures its loaded design digest at startup and returns that digest; editing the file does not change a running pipeline. Original `evaluate_case` compares actual documents/tools/flags with original criteria. All 16 baseline cases pass; disabling the missing-context rule produces an actual failure that restoration fixes. Selected and companion cases are rerun for a justified change or retention decision.

The evaluator does not validate live-model wording, streaming performance or privacy. Those remain separate evidence categories. No remote endpoint runs arbitrary evaluation inputs and no new scorer is introduced.

## Checkpoint evidence boundaries

The checkpoint discovers actual registered static POST paths in an isolated import worker, including paths excluded from OpenAPI. It checks missing and invalid credentials on every registered path. One uninterrupted process exercises the configured allowance, pooled exhaustion on all three replay routes, and one admitted request by the other caller. Inherited operations are checked in fresh delivery workers. OpenAPI coverage is cross-checked as a subset of the registered inventory.

Separately labelled fresh workers test buffered/streamed event equivalence, client cancellation and successful delivery in a fresh worker. Their fresh counters are not evidence of timed renewal or recovery within the original worker. Every experiment contributes distinct request IDs and safe terminal records. The readiness check requires these delivery and correlation observations as well as privacy and original-evaluation evidence.

The fixture emits pieces 80 ms apart; a client-observed first-content-to-completion span of at least 40 ms is the local progress check. This tolerance detects accidental buffering in the teaching fixture, not a provider latency SLA. Server `first_content_ms` measures production inside the event engine, including on buffered routes; only client arrival timing establishes visible progress.
