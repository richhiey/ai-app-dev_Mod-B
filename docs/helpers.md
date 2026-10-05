# Follow the shared helper code

Your application lives under `service/fieldcare/`; your repeatable command-line experiments live under `clients/`. Shared modules in `src/module_b/` handle mechanics that you apply in the lessons.

| Module | Supplied responsibility | Your visible decision |
|---|---|---|
| `security` | Constant-time caller comparison, static POST inventory, fixed-window counting | Caller mapping, guard placement, allowance and request sequence |
| `streaming` | Parse OpenRouter SSE and forward validated events | Route registration, client delivery choice and completion handling |
| `observability` | Correlate attempts and retain allowlisted metadata | Attachment order, useful fields and evidence interpretation |
| `openrouter`, `retrieval` | Provider HTTP calls and Chroma indexing/querying | Explicit preparation, route prompt and supported request |
| `evaluation`, `_module_a` | Preserve original Module A cases and evaluator | Concern, selected cases, design change and bounded conclusion |

Read a helper's docstring with the code that calls it. The service runs with Uvicorn using the commands in the [local setup guide](local-development.md). When something fails, compare the request in your client with the corresponding server response and safe observation; a helper or health check does not prove that a provider-backed answer succeeded.
