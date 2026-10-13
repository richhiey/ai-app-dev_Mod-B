# Live concept chat for LS13–LS14

Use an independent teaching checkout of the course repository. This lab uses the same neutral `question`/`context` API as the Live Colabs. It needs no Campus project, equipment record or assessment work. The service reuses the course's authentication, two-admission/60-second allowance, observation and OpenRouter implementation.

The path is browser → Streamlit Python server → the course FieldCare service's neutral Live API → OpenRouter. ChatGPT writes or explains Python code. The UI sends its own caller key to the service; only the service loads `OPENROUTER_API_KEY`.

## Prepare before class

Install the course Python 3.12 environment using [local setup](../../../docs/local-development.md) from the repository root. Keep that service environment separate from the UI environment. The service needs the installed `module_b` package. It does not need a document index for this supplied-context example.

In the **service terminal**, from the repository root with the service environment active:

```text
python examples/live/streamlit/server.py init
python examples/live/streamlit/server.py serve --mode fixture
```

Initialization creates private settings once without printing values or replacing files. The fixture service listens at `http://127.0.0.1:8013`. Its responses say `FIXTURE ONLY`; it makes no model call. The service's safe records remain in the ignored `examples/live/streamlit/.private/var/requests.jsonl`.

In a separate **UI terminal**, enter the repository root. Reuse the course's pinned Streamlit dependencies in a separate environment:

macOS:

```sh
python3.12 -m venv .venv-live-ui
source .venv-live-ui/bin/activate
python -m pip install -r examples/streamlit/requirements.txt
cd examples/live/streamlit
python -m streamlit run app_starter.py --server.address 127.0.0.1 --server.port 8513
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv-live-ui
.\.venv-live-ui\Scripts\Activate.ps1
python -m pip install -r examples/streamlit/requirements.txt
cd examples/live/streamlit
python -m streamlit run app_starter.py --server.address 127.0.0.1 --server.port 8513
```

Open `http://127.0.0.1:8513`. The starter displays controls and a composer. Submitting shows a starting-state message and makes no request. Save a copy as `app.py`, complete the guided build, then stop that UI command and run `python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8513`. The separate service terminal stays running. Later starts need no installation.

The instructor rehearses `app_reference.py` with the same command before class. It is a finished public demonstration, not a learner's independent UI change. If a learner needs recovery, they may copy it to a new filename and identify that origin.

## Guided build

Read `client.py` with `app_starter.py`. The client contract is:

| Function | Input and effect |
|---|---|
| `make_input(question, context)` | Strips outer whitespace, rejects an empty or oversized question, returns a body with `question` and optional nonblank `context`. No request. |
| `new_turn(body, origin)` | Creates fresh text, state, references and request ID for this attempt. No request. |
| `demo_events(body, scenario)` | Yields authored Success or Interrupted events. No HTTP or model call. |
| `service_events(body)` | Sends one authenticated `POST /v1/answer-stream` to the private loopback target; yields JSON or NDJSON and safe failures. |
| `apply_event(turn, event)` | Updates only this turn. Text means Receiving; `complete` means Completed; error after text means Incomplete. |

Use `build-prompt.txt` with the two source files, or write the same guarded branch with the instructor. Inspect the returned code before saving it. The reference's bottom submission block shows one implementation. Do not paste private settings into a coding assistant. No specific generated code or paid account is necessary.

Use the synthetic question **“What belongs in a useful meeting note?”** and the supplied context: **“A useful meeting note states the decision, names its owner, and records the next action.”**

1. Run Demo Success, then toggle reply details. The same turn should remain and no new turn should appear.
2. Run Demo Interrupted. Partial text must stay Incomplete. Its references and state belong to that turn.
3. Stay in Demo, clear the context and submit a fresh question. Expect the authored Needs context result; no HTTP request is made. The corresponding service JSON shape is `answer: null`, `status: needs_context`, and `references: []`.
4. Restore the context, select Local service, and submit once to the fixture. Expect its labelled fixed text, `complete`, an actual request ID and a safe record.

Only two admitted service requests fit each caller's 60-second window. Authentication runs before allowance; allowance runs before input validation. For `429`, wait for the displayed `Retry-After` before a new explicit submit. A restart resets counters and must not be presented as renewal.

## Match one request to one record

Copy only the request ID from that reply's details. In a third terminal with the service environment active, from the repository root:

```text
python examples/live/streamlit/server.py record --request-id UUID_FROM_REPLY
```

Replace `UUID_FROM_REPLY` with the actual UUID. A fixture record has `source: none`; a genuine provider attempt can have `source: live_provider`. Source metadata alone does not prove success: inspect the terminal event, error category and outcome together. Missing model or usage stays unknown. The `provided_context` reference means the supplied text; check a claim against that text.

## Optional real generation after private provider preparation

For a real model demonstration, the instructor supplies the already approved OpenRouter settings in the service's private environment or ignored repository `.env`. Do not change the approved model. Stop only the fixture process, and start:

```text
python examples/live/streamlit/server.py serve --mode provider
```

This changes the service mode and resets its in-memory counters; record that new starting state. Submit the same synthetic question and context from the UI. Actual deltas and a `complete` event are the successful-path observations. Match the response ID to the safe record and inspect one claim against the supplied context. Provider failures remain actual failed observations; fixture output cannot stand in for a real generated result.

## LS14 testing and documentation

Start from the same saved `app.py`. Predict and record: supported input, no context, whitespace-only input, sidebar rerun, success followed by Demo Interrupted, and Local service while only the identified service terminal is stopped. A stopped connection has no new record from that process. Restore the service with the same explicit mode and retest as a new attempt. Never stop an unrelated process.

Keep a service README, a UI README and an API reference beside your copied app, using the lesson's documentation starter. Each instruction needs a directory/environment, action, expected observation and recovery where relevant. A reader tries a bounded documented path without spoken rescue. This verifies that path on the prepared environment; a fresh installation is a different check.

## Recovery

| Symptom | Check and action |
|---|---|
| `private_settings_unavailable` | Run `server.py init` once; confirm the loopback target names, without printing the caller value. |
| `401` | Check that UI settings and service settings are the matching pair from this lab. Do not use the OpenRouter key as a caller key. |
| `422` | Compare the exact request fields with `AnswerRequest`; omission differs from an empty context string. |
| `429` | Wait for the shown interval while the same service keeps running. |
| `connection_or_protocol_error` | Check the owned service terminal and target `8013`; retain partial text as incomplete. |
| `provider_not_configured` or another provider category | Check private preparation in the service. Continue labelled fixture reasoning while recording the pending model check. |
| Duplicate request on a sidebar change | Put the client invocation inside the submission branch; repeat the toggle and compare attempt count/IDs. |
| Prior answer appears on a failed turn | Call `new_turn` for every submission and update that turn only. |

## Summary

One guarded input, an honest response state and a matching service record are enough to study a complete interaction. Keep your bounded UI change and test notes; they support a reproducible handoff without a Campus business scenario.
