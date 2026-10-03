# Shared notebook support

Keep reusable mechanics small and keep the computation being taught visible in the service or notebook.

## Helpers used by current notebooks

| Module | Responsibility |
|---|---|
| `openrouter` | Read the OpenRouter key safely, apply the course model default, and make provider requests. |
| `retrieval` | Build and query the ChromaDB store using provider embeddings. |
| `runtime` | Start and stop the local Uvicorn service used for genuine HTTP client observations. |
| `security` | Authenticate callers and apply per-key request limits. |
| `observability` | Retain allowlisted request metadata and redact content. |
| `streaming` | Forward OpenRouter stream events to the application. |
| `evaluation` and `_module_a` | Reuse the preserved Module A evaluation implementation and data for its original evidence/tool/flag checks. |
| `workspace`, `checkpoints`, `edits`, `data`, `notebook`, `live_sessions` | Provide explicit workspace/checkpoint and evidence-file mechanics used across notebook stages. |
| `secret_workshop` | Create disposable synthetic examples for the secrets workshop; it never reads a learner’s private repositories. |

The current Campus and Live notebooks attach middleware, make HTTP requests, inspect returned events, and call evaluation functions directly. Test-only controlled-clock and failure-injection probes live under `tests/support`; they are not installed with `module_b` or imported by learner notebooks. Their mock/provider-spy observations must not be presented as model or learner HTTP evidence.

## Notebook rule

Show the real operation at the point it happens. Keep HTTP method, path, request body, and observed response beside each request. Do not print copied source files or present helper summaries as service behavior.
