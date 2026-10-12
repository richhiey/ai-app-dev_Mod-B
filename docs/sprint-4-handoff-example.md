# A small annotated handoff example

Use this example to decide what your own handoff needs. It illustrates the supplied **reference fixture**, not a finished learner project README or a claim that you ran it. Your project uses its current source, service port and caller mapping.

## Give the setup reader a runnable instruction

Weak instruction: “Start the frontend and ask a question.” It leaves the folder, interpreter, file and service target unstated.

A more useful reference instruction:

> From `examples/streamlit`, activate the UI environment with `source .venv/bin/activate` on macOS or `.\.venv\Scripts\Activate.ps1` in PowerShell, then run `streamlit run app.py --server.address 127.0.0.1`. Keep the reference service running separately on port `8001`, as described in the Streamlit kit. Select `Local service`. Its private `.env.local` must target that reference, using the paired caller key. Send the supported synthetic question and `EQ-FC-1002`. In fixture mode expect labelled fixed text and a request ID, not model output.

Why it helps: the reader knows the working directory, interpreter, process dependency, configuration owner, action and expected state. It also explains the limit of the evidence. Your handoff should use the equivalent **project** target, normally `8000`, and link to the configuration/setup you verified.

## Give the API caller a contract, not a screenshot alone

For the supplied streaming route, this compact entry is grounded in `service/fieldcare/schemas.py` and `stream_routes.py`. Compare it with your own code before using it:

| Contract fact | What a reader needs to know |
|---|---|
| Request | `POST /v1/diagnose-stream`, JSON body; caller credential added server-side as `X-API-Key`. |
| Fields | `question`: trimmed, required, 1–2000 characters. `equipment_id`: optional; when provided as a string, 1–64 characters. Omit the blank UI value. Extra fields are rejected. |
| Clarification | An ordinary JSON response with `status=needs_clarification` is a valid outcome, not necessarily a connection error or model generation. |
| Stream | NDJSON: one JSON event per line. Handle `metadata`, `delta`, optional `usage`, and terminal `complete`/`error`. |
| Usage | The public event can report model and total token count, with missing/null values. No usage report means unknown, not zero. |
| Failure | Separate caller/schema/allowance rejection from connection failure or a stream that ends without completion. Show only statuses you have checked and label untested ones. |

Do not paste real keys into an example. A conceptual example can say “configured server-side credential” without inventing a valid secret. Document your buffered/versioned routes separately if present; the chat exercises the streaming route rather than proving every endpoint works.

## Turn an observation into a bounded claim

Unsupported: “The model works because the UI says live.”

Supported claim structure, to fill only after your own successful run:

> This UI request reached the documented project target. The reply received a terminal `complete`; its request ID matched a safe service record with source `live_provider` and outcome `completed`. I checked one claim against a cited document. Reported tokens were [actual count / not reported]. This single case does not establish overall answer quality or performance under load.

A clarification can have mode `live` with no generation. A fixture verifies HTTP mechanics without OpenRouter. UI elapsed/first-text measurements start at the client boundary and may differ from server log timings. An operational request ID is also not an evaluation-case ID.

## Trial the document and repair one hidden assumption

Example reader obstacle, **illustrative rather than an observed student result**: a reader runs `python -m streamlit` in the service environment and receives an import error. The useful documentation change names the UI directory and its interpreter; it does not tell the reader to reinstall every service dependency. The reader then repeats that exact startup path.

For your own trial, let a peer follow the instructions or label your clean-terminal trial as a self-check. Record the first actual obstacle and retest after correcting it. Use the [test-note record](../examples/streamlit/test-notes-template.md) for this evidence. Keep the decisions and final wording your own.
