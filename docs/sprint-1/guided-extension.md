# Worked example: a concise technician operation

HelioDesk wants an optional compact presentation of the same documented checks. We will add `POST /practice/diagnose-brief`, keeping the original route and contract. This worked example teaches the extension mechanism before you design your own supervisor prompt.

## 1. Add a route module

Create `service/fieldcare/brief_routes.py` in VS Code with this complete module:

```python
from fastapi import APIRouter, HTTPException, Request
from fieldcare.model import ModelUnavailable
from fieldcare.resources import SYSTEM_PROMPT
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse
from fieldcare.service import clarification_for, run_diagnosis
from module_b.openrouter import OpenRouterError

router = APIRouter()
BRIEF_PROMPT = SYSTEM_PROMPT + (
    " Present the documented checks as three concise technician bullets. "
    "Keep source IDs and distinguish documented guidance from observations "
    "that the technician still needs to verify."
)


@router.post("/practice/diagnose-brief", response_model=DiagnosticResponse)
def brief_diagnose(payload: DiagnosticRequest, request: Request):
    clarification = clarification_for(payload)
    if clarification is not None:
        return clarification
    try:
        graph = request.app.state.resources.graph_for(system_prompt=BRIEF_PROMPT)
        return run_diagnosis(payload, graph=graph)
    except (ModelUnavailable, OpenRouterError):
        raise HTTPException(
            502, "The provider could not complete this request. Retry later."
        ) from None
```

The route reuses both models, so it accepts and returns the same structure as the original. `SYSTEM_PROMPT + (...)` keeps the existing instructions and adds the compact presentation request. Assigning the result to `BRIEF_PROMPT` creates a separate string; it does not replace `SYSTEM_PROMPT`.

The important connection is `graph_for(system_prompt=BRIEF_PROMPT)`. Defining a new prompt without passing it to the graph would leave it unused. The early clarification return keeps unsupported inputs out of retrieval and generation. The error handler preserves the original provider-failure behavior.

**Expected:** the new file contains one router, one prompt, and one handler. Merely saving the file does not register it.

## 2. Register it with the app

In `service/fieldcare/main.py`, add this import alongside the existing router import:

```python
from fieldcare.brief_routes import router as brief_router
```

Add this line just after `app.include_router(router)`:

```python
app.include_router(brief_router)
```

The alias `brief_router` avoids confusing the new router with the existing one. Keep the existing registration. Stop and restart Uvicorn, then open `http://127.0.0.1:8000/docs`.

**Expected:** both `POST /v1/diagnose` and `POST /practice/diagnose-brief` appear. The interactive documentation is generated from the app's registered routes and models. If the new route is absent, check the import, registration, saved file, and server restart.

## 3. Verify the shared boundary first

In `clients/request.py`, use:

```python
PATH = "/practice/diagnose-brief"
BODY = {"question": "Which filter checks are documented?"}
```

Run `python -m clients.request`. **Expected:** `200` with `needs_clarification`, because equipment is absent. Temporarily use `BODY = {"question": ""}` and rerun. **Expected:** `422`, because the question violates the reused schema.

Neither result tests the new prompt. Both stop before generation. That is useful: you can establish route registration and input behavior before depending on provider access.

## 4. Compare the two prompts on the same supported input

With the document index and provider configured as described in the walkthrough, use:

```python
BODY = {
    "question": "Which filter and airflow checks are documented?",
    "equipment_id": "EQ-FC-1002",
}
```

Run once with `PATH = "/v1/diagnose"` and once with `PATH = "/practice/diagnose-brief"`. Save the two actual results.

**Expected on successful calls:** both responses contain `answer`, `status`, `citations`, and `mode`. The brief route asks for three technician bullets, but the schema does not enforce bullet count. Inspect the actual answer for that behavior and compare one claim with the cited document. If the wording ignores the instructions, that is a prompt-behavior problem to investigate, not proof that registration failed.

A single pair of different answers cannot prove the prompt caused every difference; generation can vary. The source binding proves which instructions are supplied, while the observed answers show how the model followed them in those calls.

## Final state and recovery

Leave both routes registered and restore `PATH = "/v1/diagnose"` in the client. Keep your code in the local project. A `404` suggests missing registration or a wrong path; a `422` concerns the submitted contract; a `503` asks you to prepare resources; a `502` reports provider failure. Check the relevant boundary before editing the prompt.

You now have a complete example of adding an operation with a different prompt while sharing the existing schemas, rules, and evidence path.
