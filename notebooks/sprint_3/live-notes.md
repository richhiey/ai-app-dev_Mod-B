# Sprint 3 Live — detailed reference

Use the [Live notebook](sprint_3_live_workshops.ipynb) during class. These notes expand its short instructions and provide recovery steps.

<a id="markdown-00"></a>

# Sprint 3 Live — Streaming, safe logs and evaluation

Use one personal Colab copy for four 60-minute concept workshops. Explain an idea, predict a result, run the supplied example, then interpret it. The example's names and paths are incidental; no Campus project, ZIP or business-case preparation is required. Project application begins in Sprint 4.

## Learning outcomes and navigation

| Session | Current Live outcome | Notebook section |
|---|---|---|
| LS09 | Use the Colab service example to enable streaming and explain what changes for the client. | [Streaming and client state](#ls09) |
| LS10 | Use the Colab service example to add structured logs for request ID, model, token usage, latency, and errors, while excluding personal data and sensitive prompts. | [Useful safe records](#ls10) |
| LS11 | Connect service logs back into the evaluation framework from Module A — no new eval framework built. | [A signal to an evaluation question](#ls11) |
| LS12 | Use the Colab examples to explain how streaming, structured logging with redaction, and an existing evaluation check answer different questions about an AI service. | [Concept checkpoint](#ls12) |

Start with [setup](#setup-guide). Save the notebook and [download your Live ZIP](#save-work) after each session. Code cells begin with a searchable comment such as `# Cell: code-05`. Use notebook Find to locate that label, or use Colab's table of contents for the session heading.

`PROJECT` is the separate Live practice folder, not a Campus project. Edit only the files under the printed `PROJECT` path. `REPO` is a fresh source checkout. The supplied `live_*.py` composition files make route registration and middleware attachment visible; each service runs in its own owned child process. A Colab `127.0.0.1` address belongs to that runtime, not your laptop. No public tunnel or foreground Uvicorn call is needed.

### Keep your own reasoning

Add a text cell below each application and keep these entries blank until you try it:

| Prediction | Cell or edited source | Actual result | Explanation | Still untested |
|---|---|---|---|---|
| | | | | |

Provider-dependent streaming is optional to execute when access is available, but remains pending evidence for the streaming outcome when unavailable. A written event sequence or a deterministic clarification is not a substitute for an observed provider stream.


---

<a id="markdown-01"></a>

<a id="setup-guide"></a>
## 1. Set up or resume your Live workspace

1. **Save a personal notebook copy.** Run `setup` once. It clones current `main`, installs the reviewed lock and creates a separate marked Live folder. Expected: the folder, source revision and two approved model choices print; no provider call occurs.
2. **Inspect the Files panel.** Open the printed `PROJECT/service/concept_api/` folder. Double-click a `.py` file to edit it, save with Ctrl/Cmd+S, then review your saved edit in the file. A source edit affects a child service only after its start cell runs again.
3. **Resume existing work carefully.** Rerunning setup preserves a marked Live folder, stops our previous service and generates new temporary caller keys. Rerun the relevant start cell and requests afterward. It clears current observation variables so a new run cannot borrow old results, while retaining edited source and saved evidence files. Earlier runtime logs remain on disk; match only fresh request IDs. If the folder exists without the Live marker, choose a new `LIVE_FOLDER`; do not delete unrelated work.

### Continue in a fresh runtime

Upload your own exported Live ZIP through Colab's Files panel (or provide its local path in Jupyter). Set `LIVE_ARCHIVE`, choose a `LIVE_FOLDER` that does not exist, and fill both `RESTORED_MODELS` from the saved model choices printed at export. Setup validates and restores source and selected evidence without executing it. Review restored `.py` files before starting them. Clear `LIVE_ARCHIVE` after successful restoration before rerunning setup in that same runtime.

Credentials, runtime state, `var/requests.jsonl` and Python variables are not restored. Re-enter a provider key only for an intended provider run. Selected safe observations saved under `evidence/` are historical; make fresh requests to test a restored service. A Campus checkpoint is not a Live ZIP.

**Check:** locate `live_stream.py` and `live_logging.py`; keep `RUN_PROVIDER` false until you explicitly choose provider work. If install/import fails, preserve your ZIP and notebook, reconnect a fresh runtime and rerun setup. Do not combine imported helpers from different source revisions in one kernel.


---

<a id="markdown-03"></a>

<a id="ls09"></a>
## LS09 — Streaming and client state

**Outcome:** Use the Colab service example to enable streaming and explain what changes for the client.

A buffered response returns a collected JSON object. A streamed response lets an incremental client consume events before the answer is complete. Here the service exposes NDJSON: one JSON event per line. The provider's internal SSE format is a different boundary. This neutral API passes the supplied context to the provider; no document retrieval is required. Streaming does not promise faster generation.

### Enable the route, then predict the boundary

1. Read `ls09-source`. In `stream_routes.py`, locate the ordinary JSON clarification branch, the async generator, each `yield encode_event(...)` and `StreamingResponse`.
2. Open `live_stream.py` in the Files editor. Enable the supplied router with `app.include_router(stream_router)` **before** `protected_post_paths(app)` and guard attachment. The starter already includes this line: retain exactly one registration. Explain why collecting protected paths before registration would miss the route. Save any edit and review the saved file.
3. Run `code-04` to start that composition. Expected: an owned loopback URL. Run `ls09-boundaries` once and compare your predictions with the status and content type. Missing key gives `401`; admitted invalid input gives `422`; missing context gives `200` with ordinary JSON clarification. None of these generates an answer.

The supplied policy allows each caller two admitted attempts per 60 seconds across protected routes. Invalid admitted input counts. Repeating requests can return `429`; wait for the current window or deliberately begin a new experiment by restarting. A restart is not evidence of quota renewal.

**Check before continuing:** why can a route named “stream” return JSON, and why does HTTP `200` alone not establish answer completion?


---

<a id="provider-note"></a>

### Optional provider comparison — explicit opt-in

The core streaming discussion can use written event traces and deterministic JSON clarification. For an actual generated-answer comparison, leave this section pending until you choose to use OpenRouter. The generic sample sends the supplied question and context directly; no index or embedding preparation is required. Enter the key through Colab Secrets or the hidden prompt only. A running process does not prove provider access or answer quality. After the intended run, edit the provider switch back to `False` **without rerunning `code-05`**. Rerunning that cell clears its current event and timing variables. Export the observations before starting a new comparison.

---

<a id="ls09-observe-note"></a>

### Correlate an event trace with a request record

Read `ls09-observe-source` and read `live_observed.py`. Observation middleware is added last, outside the guard, so it can record rejected attempts too. Run `ls09-observed-start`; this starts the observed composition with the same enabled stream route and a new allowance window. Make fresh requests: observation cannot add records to earlier requests retroactively.

In `code-05`, locate `client.stream`, `iter_lines` and the first nonempty delta timer before running. With `RUN_PROVIDER = False`, expect an explicit pending message and no generated output. With provider access and the switch true, expect actual events or an honest failure. A clarification remains JSON. `metadata` means ready, `delta` means partial text, `complete` confirms the stream's terminal completion, and `error` or transport loss leaves a failed or incomplete response. Optional `usage` may be absent.

Use two caller allowances for the streamed and buffered requests. Compare first text and reader finish with the buffered response time; these are separate calls, not a benchmark. The first nonempty delta measures arrival, not usefulness or quality.


---

<a id="ls09-interruption"></a>

### Independent comparison — 11 minutes, then explain

Choose a consumer and predict whether it needs progressive text or a complete JSON result. With provider access, repeat the same supported input through the two clients in `code-05`, with allowance available. Record the actual IDs, first-text timing, terminal event and buffered outcome. Explain your consumer choice; do not infer better quality or a speed guarantee from two calls. Without access, inspect the two clients and keep the actual comparison pending.

For **written calibration only**, reason about `metadata → delta → error` and `metadata → delta → connection closed`. Neither supports a completed-answer claim. These are not observed runs. A transport failure can occur after partial text; inspect the printed transport status and any received events rather than treating HTTP `200` as completion. No forced provider interruption is promised.

**Peer check:** name which observation supports partial text, which supports completion, and what remains unknown. Save your own explanation in a text cell.


---

<a id="markdown-06"></a>

<a id="ls10"></a>
## LS10 — Useful safe records

**Outcome:** Use the Colab service example to add structured logs for request ID, model, token usage, latency, and errors, while excluding personal data and sensitive prompts.

A structured log stores named fields so requests can be compared without copying their private contents. The request ID is a unique identifier for one invocation; it is different from an evaluation case ID.

| Field | What it can tell you | Interpretation limit |
|---|---|---|
| `request_id`, `route` | Which invocation and approved route | Join by exact ID, not by nearby time |
| `status_code`, `outcome`, `error_category` | HTTP status and terminal handling | A `200` stream can still fail later |
| `configured_model`, `model` | Selected model and approved provider-reported identity | Different claims; early returns make no model call |
| `tokens` | Reported usage when available | `None` means unknown, not zero |
| `latency_ms` | Observation middleware's server handling duration | Not the client's full elapsed time |
| Optional `first_content_ms` | Time from route start to first text delta | Not the client's pre-request-to-first-text timer |

Explain these meanings first. Then configure observation, make fresh deterministic requests and find exactly their terminal rows. Use LS09 provider IDs only when they came from an actual run and were recorded by the observed composition.


---

<a id="ls10-configure-note"></a>

### Attach your own logging configuration
Follow `ls10-configure-source` to open `PROJECT/service/concept_api/live_logging.py` in Colab’s Files editor. It imports the already secured streaming service but does not attach observation. Keep its required `LOG_FIELDS`; decide whether to add `"first_content_ms"` and explain which question it answers. Do not add prompts, headers or raw exceptions.

Add this supplied attachment once at the bottom of that file and save it. If restored source already contains it, retain one attachment rather than duplicating it:

```python
app.add_middleware(
    ObservationMiddleware,
    path=work_dir() / "requests.jsonl",
    routes=protected_post_paths(app),
    fields=LOG_FIELDS,
    approved_models=(selected_model(), selected_model("OPENROUTER_MODEL_V2")),
)
```

This wraps the existing guard, so rejections are observed too. `configured_model` records the selected model when generation runs; `model` records an approved provider-reported identity, independently of optional token usage. These are different claims. Early rejections and clarifications have no model call.

Review the saved edit in Files, then run `ls10-configure-start` to load it in a fresh process. Run `ls10-requests`, then `code-07`. Expected: a `401` rejection and a `200` clarification each have their own response UUID and exactly one matching JSONL row with your selected fields. The clarification finishes without a model call. The check waits briefly for the terminal row to be written.

If the ID is missing, inspect the attachment and restart after saving; an old log file does not prove the new composition is observed. If no current row matches, verify the printed workspace and fresh IDs instead of borrowing an old row. Repeated requests can use the allowance; check `429` before explaining an unexpected result.


---

<a id="markdown-08"></a>

### Minimize before saving, then check usefulness

An allowlist names the fields permitted to leave the request-handling context. `safe_record` also validates their values: approved routes/models, bounded categories, numeric measurements and a valid UUID. This is minimization for a fixed schema, not a universal personal-data detector or a filter applied only to displayed output.

Run `code-09`. Its synthetic marker goes only into a local candidate dictionary, never to the HTTP service or provider. Expected: the marker is absent from the minimized result while the request ID and outcome remain. The original candidate still exists in memory. Separately inspect the actual JSONL rows from `code-07`; neither this local marker example nor one saved file proves all logging destinations are safe.

### Independent field choice and marker check — 11 minutes

Choose a debugging question and explain whether `first_content_ms` helps answer it. Keep the required fields; save your configuration, restart if changed, and make fresh requests before rerunning `code-07`. Change the local synthetic marker in `code-09`, predict what is excluded and which useful values survive, then run it. Do not use real personal data or credentials.

Record one actual row's identity, model/usage/timing/error meaning, one retained useful value, and the limit of your minimization claim. **Peer check:** could an empty file also pass a marker search, and what additional observation establishes useful logging?


---

<a id="markdown-10"></a>

<a id="ls11"></a>
## LS11 — A signal to an evaluation question

**Outcome:** Connect service logs back into the evaluation framework from Module A — no new eval framework built.

A log describes request handling. A quality hypothesis asks whether behavior met a requirement. For example, a clarification observation can motivate “Does missing required context cause a request for details before guidance?” Latency or a `completed` record cannot answer that question.

1. Choose a safe observation from your Colab run and write a hypothesis before running evaluation. Keep its runtime request ID separate from an `eval_id`.
2. Run `ls11-cases` to read the original criteria through neutral display aliases before selecting cases. Then run `code-11` for results. The guided pair demonstrates missing-context behavior and relevant-evidence selection. Document and tool labels are display mappings; original criteria and evaluator behavior stay unchanged.
3. Read the actual evaluator rows against those printed requirements and retain the design hash. Expected: results for the selected original cases, with the original document/tool/response-flag criteria unchanged. Accept an honest pass; no forced defect is required.

The evaluator reads `service/data/pipeline_design.json`, a deterministic reference design. The live OpenRouter graph does not use that design. A shared case or source revision does not make the evaluator a scorer of live generated wording or streaming. Use the same original framework; do not create a replacement score.

**Check:** state which criterion answers the hypothesis and one additional observation needed before claiming live-answer quality.


---

<a id="ls11-task"></a>

### Independent investigation — 11 minutes

Write your safe signal and hypothesis in a text cell. Inspect `ls11-cases`, choose two distinct case aliases (at least one beyond the guided pair) from the printed list and justify both before editing `CASE_ALIASES`. The notebook maps those aliases to the original cases internally. Preserve their original inputs and criteria, then rerun `code-11`.

Record the actual result, original requirement, design hash and a bounded conclusion. Never replay a private log body into evaluation. If a case alias is unknown, choose from the printed list; if the reference design is unavailable, keep the check pending rather than inventing a replacement. An honest pass does not require changing a design.

| Safe signal / request ID | Hypothesis | Chosen cases and reasons | Original criteria | Actual result / design hash | Untested live claim |
|---|---|---|---|---|---|
| | | | | | |

**Peer check:** explain why the selected requirement answers your question and why the reference result does not certify every live answer.


---

<a id="markdown-12"></a>

<a id="ls12"></a>
## LS12 — Concept checkpoint

**Outcome:** Use the Colab examples to explain how streaming, structured logging with redaction, and an existing evaluation check answer different questions about an AI service.

For a fresh runtime, restore your Live ZIP, confirm the logging attachment once, and run `ls10-configure-start` → `ls10-requests` → `code-07` → `code-09` → `ls11-cases` → `code-11`. These checks need no provider key. Saved snapshots describe earlier runs. To correlate a new provider attempt, run `code-05` only after private provider preparation and a service restart; reload `records` with `code-07`, then use the exact-ID lookup in the notebook’s LS12 section.

Explain the Colab concepts to a peer, using actual observations when available. Keep unavailable provider checks pending and label written or recorded examples. This is a formative concept checkpoint; no Campus project milestone is submitted.

| Minutes | Activity | What to explain |
|---|---|---|
| 00–12 | Orient and calibrate | Written `HTTP 200 → metadata → delta → error`; distinguish partial output from completion |
| 12–20 | Round 1: events and states | Stream/buffered observation, terminal state and exact response-to-log ID |
| 20–22 | Check | Can a reference-evaluator pass establish streamed wording quality? |
| 22–30 | Round 2: observation to test | Signal → hypothesis → original criterion → bounded result |
| 30–32 | Check | What did the local marker test establish, and what did saved-log inspection establish? |
| 32–40 | Round 3: useful safe logs | Exclusion, useful retained fields and limitations |
| 40–44 | Resolve an identity mismatch | A different request's row cannot establish this request's outcome |
| 44–56 | Apply feedback in Colab | Choose one peer question; repeat or adjust the relevant check and improve your explanation |
| 56–60 | Connect and save | Explain a use in another application, then save notebook and ZIP |

In each round use 4 minutes to explain, 2 for peer questions, 1 for feedback and 1 to record an unresolved question. Rotate presenter, questioning peer and recorder. Explain all three ideas through the round's focus.

For the independent 12-minute application, name the peer question and relevant LS09–11 cell. Repeat a check or narrow an unsupported conclusion. Record what changed in your explanation and what is still unknown. Do not fill gaps with invented events or another invocation's log.

<a id="save-work"></a>
### Save your work after each session

Save your notebook with your predictions and explanations. Run `save-checkpoint`, then download the printed ZIP from the Files panel. Expected: source edits, model choices and selected safe observation summaries are preserved under `evidence/`. Each observation snapshot has a new timestamped filename, so exporting after restore preserves earlier snapshots even before you make a fresh request. The runtime JSONL file, raw response bodies and credentials are excluded. A saved summary is evidence from its original run, not proof that a restored runtime has executed it.


---

<a id="markdown-14"></a>

## Watch out for

| Symptom | Check and recovery |
|---|---|
| Setup refuses an existing folder | Use a marked Live folder or a new destination; preserve unrelated work |
| Source edit has no effect | Save the file under the printed `PROJECT`, inspect it again, then run its start cell |
| `401`, `422` or `429` instead of stream events | Check the caller key, input and available allowance; these are response branches, not deltas |
| Provider comparison is pending | Keep it pending or explicitly configure provider access and opt in; never substitute generated-looking output |
| Missing request ID or current log row | Attach observation once outside the guard, restart, make fresh requests and match exact UUIDs |
| Transport failure or no terminal event | Keep partial events and the error; completion is unproved |
| Restore has no live log or credentials | Inspect the saved historical evidence; start the restored source and make fresh requests |

## Quick reference

| Cell | Purpose |
|---|---|
| `ls09-source`, `code-04`, `ls09-boundaries` | Enable and inspect the stream route; test JSON branches |
| `prepare-provider`, `ls09-observed-start`, `code-05` | Explicit provider opt-in and client observation |
| `ls10-configure-source`, `ls10-configure-start`, `ls10-requests`, `code-07` | Edit logging, restart and correlate fresh records |
| `code-09` | Local minimization and separate saved-log inspection |
| `ls11-cases`, `code-11` | Select criteria, then reuse the original Module A evaluator and criteria |
| `save-checkpoint` | Preserve edited source and selected safe summaries |

## Summary

You can explain incremental delivery and terminal state, retain useful operational fields without copying private inputs, and turn a log signal into a question for existing evaluation criteria. Keep your personal Colab explanations beside the observations that support them. Transfer these ideas to another application; keep any unexecuted check explicit.


---
