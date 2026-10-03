# Shared code used by the lessons

The notebooks keep requests, service changes, and observed results visible. Shared code is limited to reusable provider, process, security, streaming, and evaluation mechanics.

## Imported by notebook cells

| Module | Student-facing responsibility |
|---|---|
| `openrouter` | Read `OPENROUTER_API_KEY` safely and configure the course model. |
| `runtime` | Start and stop the local Uvicorn process used for actual HTTP requests in Sprint 2 and Sprint 3. |
| `security` | Authenticate configured callers and apply per-key request limits. |
| `observability` | Retain allowlisted request metadata and redact content. |
| `evaluation` and `_module_a` | Run the preserved Module A evaluator against its original data and criteria. |
| `secret_workshop` | Create disposable synthetic inputs for the secrets workshop; it does not read student or private repositories. |

## Called by the FieldCare service

| Module | Service responsibility |
|---|---|
| `retrieval` | Build and query the ChromaDB store using provider embeddings. |
| `streaming` | Forward actual OpenRouter stream events to the streaming route. |
| `security` | Apply the middleware attached to protected routes. |

Notebook cells call the application and inspect its HTTP responses. Test-only controlled-clock and failure-injection probes are under `tests/support`; they are not installed with `module_b` or imported by learner notebooks. Their outputs are not model responses or learner HTTP evidence.

## Internal checkpoint utilities

`workspace`, `checkpoints`, `edits`, and `data` support safe file/checkpoint handling and are not imported directly by the six current learner notebooks. Keep those utilities small and update this page if a notebook begins to use them. The unused `notebook` source-writing/display wrapper and its `live_sessions` recorder were removed; learner-facing route edits and observations belong in the actual app and notebook cells.

## Notebook rule

Show the real operation where it happens. Keep HTTP method, path, request body, and observed response beside each request. Open source files in Colab’s Files panel; do not print copied source as a substitute for reading it.
