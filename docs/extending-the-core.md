# Keep the shared core small

Shared package code should remove repeated infrastructure work without hiding a concept the learner needs to see. The current notebooks own their HTTP calls, service edits, checkpoint import/export, and evidence records in visible cells.

## Before adding a helper

Add code under `src/module_b` only when at least two current course paths need the same stable behavior and keeping it inline would obscure the lesson. Keep case-specific rules in `examples/fieldcare` or `examples/patterns`. Do not add a general workspace, data, or notebook framework without a concrete course use.

## Process lifecycle

`module_b.runtime.ServiceProcess` is shared because the Sprint 2 and 3 notebooks need the same non-blocking local service lifecycle. Call it around the actual HTTP requests and keep the request method, path, body, and observed result in notebook cells:

```python
import requests
from module_b.runtime import ServiceProcess

with ServiceProcess("app.main:app", project_dir=project) as service:
    response = requests.get(f"{service.base_url}/health", timeout=(5, 10))
```

The helper owns process startup/readiness and cleanup; it does not create lesson responses or stand in for the service.

## Keep evidence honest

- Use a real OpenRouter request when a lesson claims model output.
- Keep deterministic validation and clarification behavior in the service.
- Keep predictions, request bodies, status codes, and output inspection beside the operation in the notebook.
- Add focused tests only when a new shared helper is requested and its behavior needs verification; do not duplicate notebook workflows as library code.
