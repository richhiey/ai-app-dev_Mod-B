# Understand the supplied code

You own the application under `service/fieldcare/` and the experiments under `clients/`. These helpers supply reusable mechanics so the lessons can focus on service behavior.

| Module | Supplied responsibility | Your visible decision |
|---|---|---|
| `security` | Constant-time caller comparison, static POST inventory, fixed-window counting | Caller mapping, guard placement, allowance and request sequence |
| `streaming` | Parse OpenRouter SSE and forward validated events | Route registration, client delivery choice and completion handling |
| `observability` | Correlate attempts and retain allowlisted metadata | Attachment order, useful fields and evidence interpretation |
| `openrouter`, `retrieval` | Provider HTTP calls and Chroma indexing/querying | Explicit preparation, route prompt and supported request |
| `evaluation`, `_module_a` | Preserve original Module A cases and evaluator | Concern, selected cases, design change and bounded conclusion |

Read the function's docstring and call site together. The local application uses ordinary Uvicorn commands; it does not use `ServiceProcess`.

`runtime`, `campus`, `campus_bootstrap`, `workspace` and checkpoint utilities remain for Sprint 1/Live Colab compatibility and safe source transfer. They do not implement the local student workflow. Test-only time controls and provider doubles live under `tests/`; they do not establish real provider success.
