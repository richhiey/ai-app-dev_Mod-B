# Sprint 4: one Streamlit chat, from connection to handoff

HelioDesk's dispatcher should be able to ask a question, watch the answer arrive and report enough information for a teammate to investigate a problem. Keep the same `app.py` throughout Sprint 4. Build the chat, connect it to your cumulative service, test what it actually does and document how another person can reproduce it.

| Stage | Your work | Keep for the next stage |
|---|---|---|
| Build | Use ChatGPT to help write a small Streamlit chat using supplied clients; inspect and improve it. | `app.py`, design brief and guided reference evidence. |
| Connect | Choose the correct private target/caller and compare your actual service contract. | The same app plus one matching project request/record pair. |
| Test | Predict and run UI → service cases; investigate actual mismatches. | [Test notes](../examples/streamlit/test-notes-template.md), corrections and honest limits. |
| Handoff | Explain setup and API behavior from your source and observations; ask a reader to try it. | Service/UI READMEs and API reference with an observed reader check. |

Streamlit is the UI. FieldCare handles authentication, allowance, retrieval, OpenRouter requests and safe observation. ChatGPT is only the code-writing helper. The optional Lovable mock exploration contributes no required account, source file or service dependency.

## Connect the existing project without rebuilding it

Use the [teaching kit](../examples/streamlit/README.md) for the initial UI installation and generated `app.py`. The steps here assume your cumulative service has its streaming route, security and safe observation from earlier work. Preserve those implementations. If your own UI is not ready, `app_reference.py` can isolate connection problems; label it as worked support and return to your own app afterward.

### 1. Check which process you intend to reach

| Process | Run from | Typical URL | Meaning |
|---|---|---|---|
| Your cumulative FieldCare service | Repository root; existing service `.venv` | `http://127.0.0.1:8000` | The project you are connecting now. |
| Guided reference, when rehearsing | Separate reference checkout; its service `.venv` | `http://127.0.0.1:8001` | Fixture or provider reference, not your cumulative service. |
| Streamlit | `examples/streamlit`; UI `.venv` | `http://127.0.0.1:8501` | The browser interface. It is not the FieldCare API. |

In service terminal A at **your project root**, activate the existing service environment.

macOS:

```sh
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

With the environment active, start FieldCare:

```text
python -m uvicorn fieldcare.main:app --host 127.0.0.1 --port 8000
```

Keep it running. If that port is occupied, identify your earlier terminal; do not kill an unknown process. Open `http://127.0.0.1:8000/health` and `/docs`. Health confirms process/preparation state, not a model answer. Confirm `POST /v1/diagnose-stream` appears in the API docs. If absent, inspect your earlier route registration rather than replacing `main.py` with the starter. If security/observation is missing, restore the work you completed before claiming a secured, traceable integration.

### 2. Point the UI at that service privately

In VS Code open `examples/streamlit/.env.local`. Create it if absent, using `.env.example` as a names-only reference. If it already targets the guided reference, preserve your previous private settings so you can return to them; do not run reference initialization over existing files.

Set `FIELDCARE_SERVICE_URL` to your actual project origin, normally `http://127.0.0.1:8000`. Set `FIELDCARE_CALLER_KEY` to the actual value for a caller registered in **your current** `service/fieldcare/security_settings.py`. The public `CALLER_ENV` mapping contains environment-variable names, not secret values: follow your selected name to its value in the service’s private `.env` or runtime environment. Copy that value locally in the editor, never into chat or a visible UI field. If your checkpoint uses `weekend_partner`, use its existing `FIELDCARE_WEEKEND_PARTNER_KEY`; do not restore the starter's `partner` mapping or change the allowance. The public caller label and the private key value are different things.

Run this from the project root:

```text
git check-ignore examples/streamlit/.env.local
```

Expect that path. The UI folder's `.gitignore` already includes it; if your app is elsewhere, check the equivalent path there. `OPENROUTER_API_KEY` stays in the service `.env`; the UI needs no model key. Existing shell environment values for the two `FIELDCARE_` names override `.env.local`, so resolve stale terminal overrides locally if the target does not change. Do not print an environment dump.

### 3. Start the saved chat and prove a cheap request first

In UI terminal B, enter `examples/streamlit` and activate the UI environment you installed from the teaching kit.

macOS:

```sh
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

With the UI environment active, run the saved app:

```text
streamlit run app.py --server.address 127.0.0.1
```

Restart the UI if its process environment changed. Open its printed URL, select `Local service`, and check the configured target is your project port. Opening the page or changing the selector must not make a diagnostic request.

Leave equipment blank and send `Which filter and airflow checks are documented?`. This should produce a deterministic clarification through the real HTTP path, without an OpenRouter generation call. In that reply's `Sources & request details`, find its actual request ID. In a third terminal at the **project root**, activate the service environment as in step 1, then run:

```text
python -m clients.logs UUID_FROM_SCREEN
```

Replace the final token with that reply's actual ID. Look for the record in your configured work directory (`var/requests.jsonl` by default). If no ID/record appears, investigate observation attachment before claiming the log join works. A clarification can carry mode `live` because it came from the live route; this does not mean a model was called.

### 4. Observe generation with the same app

Set equipment to `EQ-FC-1002` and send the full supported question again. Use your existing OpenRouter configuration and prepared index. Do not rebuild the index on every UI start; prepare it with the established service command only when needed. Generation and index preparation use the service's OpenRouter allowance.

Expect real text chunks and terminal completion if the request succeeds. Open that reply's details and match its new ID using `clients.logs`. A completed generated stream should have service source `live_provider` and outcome `completed`. Verify a claim against a cited document. A fixed fixture, clarification or incomplete stream cannot substitute for this evidence; if access fails, record the blocker.

## Read the service through one reply

The worked chat keeps technical detail in an expander so the dispatcher can read the answer first. The observations make existing service behavior inspectable; they do not require another dashboard or new backend endpoints.

| What you can inspect | What it shows | What it does not prove |
|---|---|---|
| Actual target and source mode | Which local endpoint this turn used; mock, fixture or live response mode. | A selector alone does not prove a model call. |
| Event order and text chunks | Metadata, progressive text, optional usage and terminal state; JSON clarification follows a different path. | Chunk count is not token count. HTTP success alone is not stream completion. |
| Citations | Evidence identifiers returned for this answer. | A cited answer can still be wrong; inspect a source. |
| Reported model and total tokens | Values from the optional `usage` event. Missing values say `Not reported`. | Configured model is not necessarily reported model; no inferred cost or token count. |
| UI elapsed and first-text time | Time measured around the UI client operation. | Not the same boundary as server log timings; not a benchmark. |
| HTTP rejection and safe message | A returned `401`, `422`, `429` or `503`; retry guidance when supplied. | No rejection recorded is not proof all guards work. A connection failure may have no HTTP status. |
| Request ID and service record | Correlation with the safe observation from that attempt. | A log is not an answer-quality score or an evaluation result. |

The supplied client handles transport. Keep your generated UI's mapping explicit and inspectable. Preserve per-turn results and original input snapshots; rerendering history, opening help and `New chat` must not send another request. Displayed history is not sent as model memory.

## Diagnose the first failing boundary

| Symptom | Inspect next |
|---|---|
| `404` or wrong target | API docs and route registration; UI must target the service port, not `8501`. |
| `401` | Current caller mapping and private value; keep the policy intact. |
| `422` | Your actual request schema and submitted fields. A blank UI input should usually be stopped before HTTP. |
| `429` | Displayed retry duration; wait with the same service running. Avoid rapid provider calls just to hit the limit. |
| `503` | Existing OpenRouter configuration and index readiness; do not fall back silently to mock. |
| No HTTP status/ID | Connection, timeout or pre-request configuration failure; distinguish it from a service rejection. |
| Partial text | Require a terminal `complete`; keep interruption visible, then retry deliberately. |
| Help triggers a second record | Move the client call behind submission/retry; history rendering is not a request. |

For a cheap controlled caller/allowance check, use a valid question with **no equipment**, which follows the deterministic clarification path. Change only your private UI test configuration if testing an invalid caller, restore it afterward, and keep the service policy unchanged. Record what you actually ran; do not assume a demo error proves authentication or rate limiting.

## Carry observations into the handoff

Use the [test-notes template](../examples/streamlit/test-notes-template.md) as a small evidence record. The [annotated handoff example](sprint-4-handoff-example.md) shows how a command and an observation become a useful instruction without writing your project documentation for you. Keep service/UI startup, contract reference and result interpretation consistent across the documents.
