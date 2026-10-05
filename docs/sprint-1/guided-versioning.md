# Guided local pattern: preserve v1 while adding a stricter pilot

Work in your existing VS Code project. This practice creates `POST /v2/diagnose` with a `600`-character question limit while preserving v1's `2000`-character limit. Its short technician prompt is an analogous example; you will later adapt the pilot for a different caller brief.

The input checks below need no model call. A supported generated-answer comparison needs the prepared index and provider configuration from the local setup.

## 1. Give the pilot its own models

Create `service/fieldcare/pilot_schemas.py`:

```python
from pydantic import Field
from fieldcare.schemas import DiagnosticRequest, DiagnosticResponse


class PilotRequest(DiagnosticRequest):
    question: str = Field(min_length=1, max_length=600)


class PilotResponse(DiagnosticResponse):
    pass
```

**Inheritance** lets a Python class reuse another class's declarations. `PilotRequest` keeps the equipment field and model configuration, then overrides only the question constraint. It does not edit `DiagnosticRequest`. `PilotResponse` currently retains all four response fields; naming the pilot model separately makes the route's output agreement explicit without inventing a new output requirement.

**Check:** the original model still says `max_length=2000`; the new model says `600`. Do not change the original to make the pilot work.

## 2. Bind the new route to those models and its own prompt

Create `service/fieldcare/pilot_routes.py`:

```python
from fastapi import APIRouter, HTTPException, Request
from fieldcare.model import ModelUnavailable
from fieldcare.pilot_schemas import PilotRequest, PilotResponse
from fieldcare.resources import SYSTEM_PROMPT
from fieldcare.service import clarification_for, run_diagnosis
from module_b.openrouter import OpenRouterError

router = APIRouter()
PILOT_PROMPT = SYSTEM_PROMPT + (
    " For this pilot, present the documented checks in two short paragraphs: "
    "first the checks, then what the technician still needs to verify."
)


@router.post("/v2/diagnose", response_model=PilotResponse)
def pilot_diagnose(payload: PilotRequest, request: Request):
    clarification = clarification_for(payload)
    if clarification is not None:
        return PilotResponse.model_validate(clarification.model_dump())
    try:
        graph = request.app.state.resources.graph_for(system_prompt=PILOT_PROMPT)
        result = run_diagnosis(payload, graph=graph)
        return PilotResponse.model_validate(result.model_dump())
    except (ModelUnavailable, OpenRouterError):
        raise HTTPException(
            502, "The provider could not complete this request. Retry later."
        ) from None
```

Read the three bindings: `/v2/diagnose` chooses the path; `PilotRequest` chooses the input rule; `system_prompt=PILOT_PROMPT` chooses the instructions. `PilotResponse.model_validate(...)` checks the shared service result against the pilot's output model. `model_dump()` turns a Pydantic object into a dictionary for that check.

The original route still uses its original model and default prompt. Both share deterministic checks, the evidence store, and the configured provider model.

## 3. Register and restart

In `service/fieldcare/main.py`, add:

```python
from fieldcare.pilot_routes import router as pilot_router
```

After the existing route registrations, add:

```python
app.include_router(pilot_router)
```

Keep the existing registrations. Stop and restart the server:

```text
python -m uvicorn fieldcare.main:app --host 127.0.0.1 --port 8000
```

**Expected:** `/docs` lists both diagnosis versions. If you already experimented with `/v2/diagnose`, keep exactly one registration for that method and path. Two competing handlers do not make a clear version contract.

## 4. Test the input that separates the agreements

In `clients/request.py`, set:

```python
BODY = {"question": "filter " + "x" * 693}
```

The question contains `700` characters: `7` from `"filter "` plus `693` repeated characters. Equipment is deliberately absent. Run `python -m clients.request` once for each `PATH`:

| `PATH` | Expected status | Explanation |
|---|---|---|
| `/v1/diagnose` | `200`, `needs_clarification` | `700` fits v1; missing equipment causes clarification |
| `/v2/diagnose` | `422` | `700` exceeds the pilot's `600`-character limit |

Repeat with `BODY = {"question": "Which filter checks?"}`. Both should return clarification. Repeat with `BODY = {"question": ""}`. Both should return `422`.

**Check:** record the six actual outcomes. If both routes reject the long question, inspect whether you modified the original model. If both accept it, inspect the new handler's input annotation and restart the service after any repair.

## 5. Verify behavior separately from structure

When provider setup is ready, send this body through both routes:

```python
BODY = {
    "question": "Which filter and airflow checks are documented?",
    "equipment_id": "EQ-FC-1002",
}
```

**Expected when generation succeeds:** each returns the four declared response fields. The pilot asks for two paragraphs, while v1 keeps its original instructions. Compare an actual answer with the prompt and one cited document. The length-boundary tests do not establish either prompt adherence or factual support.

Restore the client's original route after the comparison. Keep the pilot source in your project for adaptation.

## Apply the pattern to your supervisor operation

Use your supervisor practice prompt to adapt the pilot while keeping v1 intact. Choose and document the new question limit from the caller's stated requirement; do not silently carry the example's `600` into a brief that specifies another limit. Keep the four output fields, the optional equipment context, and shared deterministic checks unless the brief explicitly changes them.

Before the checkpoint, you should be able to explain which line binds the route, which declaration controls the input limit, which argument selects the prompt, and which request demonstrates that v1 still honors its agreement. The checkpoint supplies a fresh request and its own limit; it does not introduce a new implementation mechanism.
