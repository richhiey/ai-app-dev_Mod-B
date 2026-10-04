# Sprint 2 control policy

This record owns the teaching semantics for B-C08–B-C13 and their asynchronous support. It describes the executable `module_b.security` pattern, not every API/limiter. All caller labels and FieldCare data are synthetic; credential values are generated per local session and are never printed.

| Boundary | Frozen rule |
|---|---|
| Caller authentication | One `X-API-Key` header matched against distinct runtime values; safe caller labels are the identities. Missing/wrong/duplicate headers return `401`, generic detail, no handler/adapter work. |
| Required configuration | Every configured caller environment value must be present, nonblank, ASCII and non-placeholder; values must be distinct. Middleware construction refuses startup on failure. Runtime changes require restart. |
| Route scope | All registered static POST paths, including old versions, project extensions and paths hidden from schema. Register before `protected_post_paths(app)` and attach before startup. Parameterized paths are refused; mounts/other methods require a separately designed inventory. |
| Public paths | Existing GET `/health`, `/docs`, `/docs/oauth2-redirect`, `/redoc`, `/openapi.json`; unknown paths retain routing behavior. |
| Grouping | One bucket per authenticated caller label, pooled across all protected versions/routes. Wrong key strings never create buckets. |
| Algorithm | Fixed window anchored to first admitted attempt per caller. At elapsed time greater than or equal to window, next admitted attempt starts a new window. |
| Counting order | Authenticate → limit → route validation → handler → possible adapter. Authenticated admitted attempts count even for `422`, clarification, provider `502`, and other downstream failure. `401` and `429` do not consume more allowance. |
| Exhaustion | `429`, safe detail, `Retry-After` integer seconds rounded upward (minimum 1). No handler or adapter work. |
| Reset | Restart clears ALL in-memory buckets. No HTTP reset endpoint. In-process observations use an injected clock and a clean process per probe. Never join separate probes as one uninterrupted sequence. |
| Limitations | One process, not distributed; burst possible around boundaries; request-count cap is not token/spend cap or capacity reservation. Loopback demo HTTP only; deployment/HTTPS and live provider are separate. |

| Lesson context | Caller mapping | Allowance/window |
|---|---|---|
| Authentication | dispatch → FIELDCARE_DISPATCH_KEY; partner → FIELDCARE_PARTNER_KEY | No limiter (`POLICY=None`) |
| Concept worked example / guided rehearsal | Same | 2 / 60 seconds |
| Independent practice | Same | 3 / 60 seconds |
| Assessment | operations → FIELDCARE_OPERATIONS_KEY; weekend_partner → FIELDCARE_WEEKEND_PARTNER_KEY | 4 / 60 seconds |

## Reproducible evidence

Campus learners start Uvicorn directly in a terminal and send visible requests from `clients/`. The local service lives in `service/fieldcare/`. Configuration is loaded from a private local `.env`; the app must restart after edits. The setup guide explains Windows/macOS environments and safe checkpoint transfer. Live notebooks retain their separate `ServiceProcess` runner.

Students predict their own sequence, run it against one process, inspect actual statuses and `Retry-After`, and demonstrate renewal without a restart. Deterministic clarification/validation experiments do not need provider calls; generated-answer evidence requires explicit index preparation and a real provider response.

Internal tests use controlled clocks and provider doubles where stated. Those checks establish mechanics, not hosted execution, throughput or live-provider success.

## Source grounding

Framework request-boundary semantics: [FastAPI middleware](https://fastapi.tiangolo.com/tutorial/middleware/). The provided helper uses Python's [constant-time comparison function](https://docs.python.org/3/library/hmac.html#hmac.compare_digest). Ignore/tracking distinction: [Git ignore rules](https://git-scm.com/docs/gitignore). Exact statuses, counting, renewal and scope above are course implementation choices verified locally, not inferred from those documents.
