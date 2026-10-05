# Follow one FieldCare request

FieldCare is a FastAPI application that exposes AI-assisted equipment guidance through HTTP. You develop it in `service/fieldcare/` and call it from small Python programs in `clients/` or the interface you build in Lovable.

```text
Caller
  → service authentication and allowance
  → FastAPI request validation
  → deterministic clarification when context is missing
  → ChromaDB retrieval → LangGraph orchestration → OpenRouter generation
  → JSON response or NDJSON stream
  → minimized request record
```

Not every request follows every step. Invalid input stops at validation. An unrecognized key stops at authentication. A valid question without required context can receive a clarification before retrieval or generation. A supported question with a prepared index can use the model path.

## Where each part lives

- `service/fieldcare/main.py` creates the app and registers routes and middleware.
- `service/fieldcare/routes.py` and `schemas.py` define the buffered operation and its contract.
- `service/fieldcare/stream_routes.py` defines the streamed operation added in Sprint 3.
- `service/fieldcare/service.py`, `orchestration.py`, and `model.py` connect rules, retrieval, and generation.
- `service/fieldcare/security_settings.py` names callers and the allowance policy; key values live in the ignored local `.env` file.
- `service/fieldcare/resources.py` opens prepared resources only when a supported request needs them.
- `service/data/` contains supplied synthetic equipment records and service documents.
- `src/module_b/` contains shared mechanics used by the FieldCare application.
- `clients/` contains readable HTTP callers and investigation tools.
- `var/` contains local generated indexes and safe runtime records. It is ignored by Git.
- `evidence/` contains selected, reviewed observations; do not copy `.env`, raw logs, or private request content there.

Run `python -m fieldcare.prepare_index` only when a lesson calls for real retrieval. Indexing sends supplied documents to the embedding provider and uses quota. A healthy `/health` response means the process started; it does not prove the provider, retrieval, answer quality, or interface integration works.

The deterministic Module A evaluator and the live OpenRouter service are separate systems. Evaluation results describe the selected reference cases, not the wording of a live streamed answer.
