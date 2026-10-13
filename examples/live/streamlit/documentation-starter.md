# Neutral Live lab — three documentation drafts

Copy the sections below into three files beside your copied app, for example `service-README.md`, `API.md` and `UI-README.md`. Supplied facts come from the [lab](README.md); **learner completion** fields deliberately remain unfinished. Fill them from your actual source and observations. Do not claim a test that has not run.

## Draft 1: service-README.md

### Purpose and preparation

This local teaching service answers a question from supplied context. It supports fixture and provider modes, with authentication, caller allowance and safe request records. Use the course Python service environment from the repository root. This example requires no document index.

### Private initialization

Run once: `python examples/live/streamlit/server.py init`. It creates `.private/service.json` and `.private/ui.json` in the lab, without displaying values. Existing settings are preserved. The UI gets its caller key; the service owns approved OpenRouter configuration.

### Start and inspect

Fixture command: `python examples/live/streamlit/server.py serve --mode fixture`. The service listens at `http://127.0.0.1:8013`; fixture replies use fixed labelled text with no model call. Provider mode uses `--mode provider` after private preparation and starts a new process.

**Learner completion:** name your tested environment/directory, chosen mode, actual startup observation and how to stop only that identified process.

### Find one record

From the course root in the service environment use `python examples/live/streamlit/server.py record --request-id UUID_FROM_REPLY` with an actual reply UUID. Safe records are in the ignored `.private/var/requests.jsonl`.

**Learner completion:** link one safe test reference, explain ID/outcome/source together and state a limitation of that observation.

## Draft 2: API.md

### Route and credentials

`POST /v1/answer-stream` accepts a caller credential in `X-API-Key`. The Python UI client attaches its private caller value. Provider credentials belong to the service's separate OpenRouter interaction.

### Request

```json
{
  "question": "What belongs in a useful meeting note?",
  "context": "A useful meeting note states the decision, names its owner, and records the next action."
}
```

The schema requires `question` with 1–2000 characters. `context` is optional and accepts 1–4000 characters when supplied. The UI additionally rejects whitespace-only questions. The UI trims values and omits blank optional context. It sends the current input, not visible conversation history.

**Learner completion:** cite the actual schema/client source and explain the difference between omitted context and an explicitly empty string.

### Response and failure behavior

Without context, valid input receives ordinary JSON with `answer: null`, `status: needs_context` and `references: []`. With context the streaming path uses NDJSON: one JSON event per line. `delta` supplies partial text; `complete` establishes stream completion; `error` or missing terminal event leaves the attempt unfinished.

Authentication runs before allowance and validation. The lab allows two admitted attempts per caller per 60-second first-admission window. `401` rejects missing/wrong credentials; `429` includes `Retry-After`; admitted malformed input can reach `422`.

**Learner completion:** add your observed event sequence, exact response/record relation and one error interpretation. Explain why HTTP `200` or a mode label alone cannot establish successful generation.

## Draft 3: UI-README.md

### Run the screen

The UI uses a separate Python environment with the pinned `examples/streamlit/requirements.txt`. From `examples/live/streamlit`, run:

```text
python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8513
```

Open `http://127.0.0.1:8513`. The Python client reads `.private/ui.json`, including the local service target and caller key. ChatGPT is a coding assistant; the service owns the model call.

**Learner completion:** name the environment you actually used, link preparation instructions and identify your `app.py` origin. Supply the expected visible starting state from your own run.

### Use and interpret

Demo uses authored events without HTTP. Local service calls the lab on `8013`. A fresh turn owns its text, state, references and ID. Sidebar reruns redisplay saved turns without resubmission. Partial text remains Incomplete after interruption; absent context becomes Needs context.

**Learner completion:** describe your selected interaction and a neighboring check. Include the controlled stopped-service action, actual error, restoration command and separate recovery result. State what the reader check verified and what remains pending.

## Deliberately incomplete calibration excerpt

> Start the app, add the key and call the API. If it fails, restart.

This is intentionally inadequate. Record the first missing instruction, replace it with a source-supported action and expected observation, and retry that step. Do not paste a credential or invent success.
