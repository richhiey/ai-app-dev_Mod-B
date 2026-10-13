# Sprint 2 Live — detailed reference

Use the [Live notebook](sprint_2_live_workshops.ipynb) during class. These notes expand its short instructions and provide recovery steps.

<a id="markdown-00"></a>

# Sprint 2 Live — Authentication, rate limits and secrets

Use this notebook with LS05–LS08. Save one personal copy and continue in it across all four sessions. Each session teaches a concept, demonstrates it in a small API example, then gives you a changed condition to predict and test. No Campus project, business-case preparation or provider account is required for the core exercises. Names such as `concept API`, `reader` and `editor` are identifiers in the supplied example; `reader` and `editor` represent two different callers.

## Session map and learning outcomes

| Session | Current Live outcome | Notebook route |
|---|---|---|
| LS05 | Use the Colab service example to explain API key authentication and safe runtime handling of credentials. | `ls05-source` → `code-05` → `code-06` → `ls05-startup`; independent request variation |
| LS06 | Use a Colab service example to apply a per-key rate limit and explain its behavior under burst traffic. | `ls06-source` → `code-08` → `code-09` → `ls06-renewal`; independent changed-order experiment |
| LS07 | Walk through the most common ways secrets leak (logs, prompts, repos) and apply patterns to prevent each. | `live-ls07-workspace` → before check → log/prompt edits → Git check → fresh-marker attempt |
| LS08 | Use the Colab service examples to explain how caller authentication, per-key limits, and safe secret handling work together. | Explain the earlier notebook examples, predict a peer's changed condition, then test one independently |

These current Live outcomes are practised with a separate Colab example API, rather than by building the Campus project. Use the notebook's table of contents or search for a named cell/section; the cell names in code comments match the session guides. Run only the current session's sequence, rather than **Run all**: some cells deliberately wait for your edits, predictions or a real time window.

**Your starting state:** setup creates a separate Live workspace. Temporary caller credentials stay in memory. A helper owns one loopback HTTP server process and stops only that process when you start another. `127.0.0.1` belongs to the Colab runtime, not your laptop; no public tunnel is needed. Reusable helpers handle workspace/process housekeeping while the authentication attachment, policy, requests and source edits remain visible.

**Your finished state:** keep your own predictions, observed outputs and short explanations in text cells in this notebook. Export the Live ZIP after a session and download it alongside your saved notebook. An output or a reference result is not a substitute for your explanation.


---

<a id="markdown-01"></a>

## 1. Set up once, or restore your own work

1. In a new personal copy, leave `LIVE_ARCHIVE` empty and run `setup`, then `code-03`. Setup clones current `main` and installs the locked dependencies. It prints the source revision, workspace path and model names; it makes no provider request.
2. Keep the same `LIVE_FOLDER` within a runtime. Setup preserves an existing marked Live folder, including edits, but regenerates temporary caller values and stops the previous owned server. Start the relevant service again after setup. **Do not rerun setup or a start cell during a rate-limit renewal experiment.**
3. To continue after a runtime reset, upload your own exported Live ZIP through Colab's Files panel (or use its path in local Jupyter). Set `LIVE_ARCHIVE`, choose a `LIVE_FOLDER` that does not yet exist, and fill both `RESTORED_MODELS` from the saved `evidence/live-models.json` record or your notebook notes. The ZIP contains source/evidence, not Python variables; review the restored source, then run the current session's cells. Clear `LIVE_ARCHIVE` after a successful restore before rerunning setup in that runtime.

**Check:** only caller labels, model names and paths are displayed. A refused existing/unmarked folder or incompatible ZIP protects your work: choose a new empty destination and your own Live ZIP; do not delete or overwrite another workspace. A Campus checkpoint is not a Live ZIP. On install/import failure, retain the error and source revision, rerun setup once, and ask the instructor if it repeats. Credentials and runtime-only state are excluded from exports; provider access is an explicit opt-in.


---

<a id="markdown-04"></a>

## LS05 — Caller keys, provider keys and runtime values

A **caller key** is a value the client sends to this API; the guard checks whether that caller is recognised. A **provider key** belongs to the API's separate request to a model provider. Passing the first check does not require the API to call a model: this example can validate input or return a clarification first.

### Read the mechanism, then make a prediction

Read `ls05-source`. Read `CALLER_ENV` as a mapping from caller labels to configuration **names**, not secret values. In `live_auth.py`, router registration happens before the protected POST-path inventory; `policy=None` means no rate limit in this session. The guard loads actual values when the service is constructed, checks the request header, then allows input validation and the handler to run.

Run `code-05` to start that authentication-only example. **Expected:** an owned loopback URL. Read each condition in `code-06` and write a status prediction before running it. Missing/wrong caller credentials should be rejected; a recognised caller can still send an invalid body or receive a clarification. The matrix displays statuses without displaying keys. Its OpenAPI inventory includes schema-visible POST routes; compare the source registrations too rather than treating documentation as a complete security audit.

### Compare names with loaded values

Run `ls05-startup`: it stops the demo, removes one required caller value from a child environment, attempts startup, then restores a fresh service. **Expected:** startup refusal followed by a `200` clarification after restoration. Explain why a variable name in source does not supply its private runtime value. The notebook passes temporary caller values into a child process; it does not read them from a source file.

**Check:** connect each HTTP observation to the guard → validation → handler order. A `200` clarification is not evidence of model generation. The notebook does not measure an adapter-call counter. If calls refuse connection, run `code-05` again and repeat the observation; if a recognised caller suddenly gets `401` after setup, the caller values changed and the service needs restarting.

### Independent application — 14 minutes

Add a text cell for your prediction and a code cell copied from one familiar request in `code-06`. Change one caller condition or body condition, keeping the taught route and deterministic inputs. Predict before execution, run it, and explain the stopping point from source. Ask a peer to change one condition in your explanation. Keep the prediction, actual status and revised explanation; no completed variation is supplied. Use labels instead of credential values when sharing.


---

<a id="provider-note"></a>

### Optional provider comparison — separate from the core checks

The access, validation, clarification, rate-limit and secret-fixture exercises need no provider account. If you want to see a generated response, set `RUN_PROVIDER = True` in the next cell and provide an OpenRouter key through Colab Secrets or the hidden prompt. The generic sample sends the supplied question and context directly; no document index is prepared. A successful service startup or accepted caller alone proves neither provider access nor answer quality. If generation fails, keep the comparison pending and continue the provider-free work. Restore the switch to `False` afterward. Never paste a key into a cell or display the environment.

---

<a id="markdown-07"></a>

## LS06 — Identity, shared allowances and renewal

A **rate limit** decides whether an authenticated caller has an admission available. This example allows **two admitted attempts per caller in a 60-second window**, shared across its protected routes. The window starts with that caller's first admission; it is not aligned to a wall-clock minute. Caller A is `reader`; caller B is `editor`. Their labels identify separate allowances, not different tasks.

1. Read `ls06-source` and locate `LimitPolicy(allowance=2, window_seconds=60)` and its middleware attachment. Explain why admission happens before body validation: an admitted invalid body consumes an attempt too.
2. Run `code-08` **once** for a fresh guided experiment. It starts the rate-limited service and clears any earlier renewal observation. Predict the five results in `code-09`, then run that cell once. **Expected categories:** authentication refusal, admitted invalid input, admitted clarification, exhausted caller, and another caller with its own allowance. The printed statuses and `Retry-After` support those distinctions. `401` and `429` do not consume an additional admission; admitted `422` does.
3. Keep the same process alive. Run `ls06-renewal` before expiry to see the remaining wait; after that delay rerun only that cell. **Expected:** the same worker accepts caller A again after expiry. Neither starting a new process nor seeing caller B succeed establishes A's renewal.

**Check:** changing from `/v1/answer` to `/v2/answer` must not give caller A a separate allowance. This experiment sends malformed or missing-context bodies, so no model call is needed. If you rerun `code-09`, its extra requests alter the buckets: save that observation, run `code-08` once for a clearly labelled new experiment, then repeat the sequence and wait. A stopped/replaced worker requires a new experiment; the renewal cell refuses to label it same-process evidence.

### Independent changed-order experiment — 14 minutes

Copy `code-09` into a new cell. Start `editor` first and choose a different ordering that includes both answer routes, a recognized malformed body, reader exhaustion and another caller retaining capacity. Write the predictions before running. Start `code-08` once for this clearly labelled new experiment, then run your copied sequence and keep that worker through renewal.

The supplied `ls06-renewal` always sends `reader`. Arrange for reader's `429` to be the final rejection in your sequence so `retry_at` describes the reader wait, then use the renewal cell after that delay. Do not use editor exhaustion followed by reader success as evidence of renewal. Save your ordered statuses, elapsed times, worker PID and explanation. A route change, caller change and process restart have different effects.


---

<a id="ls06-task"></a>

### Independent changed-order experiment — 14 minutes

Add a text cell with your sequence and predicted results, then duplicate and edit `code-09` in this notebook. Start caller B first, include an admitted invalid body and two paths, and demonstrate renewal. Choose the ordering yourself. Run `code-08` once to begin your new experiment, then keep that worker alive through exhaustion, the other caller's request and expiry. Record times, labels and statuses; leave key values out.

Explain which observation establishes caller isolation, which establishes renewal, and why changing routes cannot reset a caller's allowance. Compare the actual trace with your prediction and explain any mismatch. Keep your own earlier output/notes before a rerun overwrites the latest safe timeline file. A passing guided sequence is not the completed independent attempt.


---

<a id="markdown-10"></a>

## LS07 — Secrets can be copied into logs, prompts and Git

Keeping a value out of a source file is only one protection. A logger can serialize headers or exception text; a prompt builder can copy runtime configuration into an outbound payload; Git can retain a committed value after the working file is ignored. Prevention happens at each copying boundary.

This workshop uses only a visibly synthetic, nonfunctional marker. It sends no HTTP or provider request. Run `live-ls07-workspace` to make a disposable local fixture, then inspect the intentionally unsafe before-state. You will edit two policy files and apply a Git prevention, inspect actual local artifacts, then repeat with a fresh marker independently.

**Editing in Colab:** use the folder path printed by the fixture cell in the Files panel, refresh the panel if needed, double-click the named `.py` file, edit and save it before running its check cell. In local Jupyter, open that same absolute path in your file editor. Edit files under `FIXTURE`, not the downloaded reference files under `REPO`. Each check uses `runpy` to reload your saved policy, so no service restart is needed.

**Fixture reruns:** reusing `RUN_NAME` preserves existing files; it does not reset them to the unsafe starter. Use a new name containing letters, digits or underscores for a fresh fixture. Do not delete an earlier attempt to obtain a desired result.


---

<a id="live-ls07-before-note"></a>

### Observe the deliberately unsafe before-state

Run `live-ls07-before`. It calls the starter `log_policy.py` and `prompt_policy.py` with synthetic values, writes actual local files and displays them. **Expected in a fresh fixture:** the marker appears in both ordinary/error log output and the assembled prompt payload. The local exception is a Python input to the logger, not an HTTP or provider failure.

Identify the copied field that introduced each marker before changing the policy. A previously edited fixture may already exclude it; choose a fresh `RUN_NAME` if you need the initial unsafe comparison. The prompt payload is assembled locally and is never sent to a model.


---

<a id="live-ls07-log-note"></a>

### Prevent disclosure before log serialization

Open the [safe log pattern](https://github.com/richhiey/ai-app-dev_Mod-B/blob/main/examples/patterns/secret_workshop/log_safe.py) as the guided reference. In the Files panel, adapt that field selection in `FIXTURE/log_policy.py` and save. Retain request ID, route, outcome and a bounded error code; exclude request headers and raw exception text. The aim is useful diagnostics without copying credential-bearing inputs. The retention check requires the original request IDs, route and outcomes, plus `error_code: null` for the ordinary record and `error_code: "operation_failed"` for the failed record.

Run `live-ls07-log` and inspect `observed.log`. **Expected:** the marker is absent from both ordinary and error records, while request ID, route, outcome and an error code still explain the event. If a check fails, inspect the saved file and your policy's exception branch; removing only the ordinary header path is incomplete. Do not simply suppress the whole log record.


---

<a id="live-ls07-prompt-note"></a>

### Keep runtime configuration outside the prompt

Open the [safe prompt pattern](https://github.com/richhiey/ai-app-dev_Mod-B/blob/main/examples/patterns/secret_workshop/prompt_safe.py), adapt its input selection in `FIXTURE/prompt_policy.py`, and save. A prompt needs the question and useful task context. Provider credentials configure the client that sends it; they are not part of its text.

Run `live-ls07-prompt` and inspect `outbound-payload.json`. **Expected:** no marker, with the question and useful context retained. A clean answer would not prove a clean outbound payload, so check the assembled request here. If context disappears too, repair the allowed inputs and rerun this cell. No request is sent to a model.


---

<a id="live-ls07-repository-note"></a>

### Distinguish ignore rules, the current index and old commits

The disposable fixture has a synthetic `.env` in its initial commit and an untracked `local.key`. Read `live-ls07-repository` before running it: it adds both names to `.gitignore`, then `git rm --cached` removes `.env` from the current index while leaving the local file. The Git index is the set of files staged/tracked for the next commit; ignore rules alone do not remove an already tracked file.

**Expected after the cell:** both names ignored, `.env` untracked, and the marker still present in the initial commit. The cell applies ignore and untrack together; it does not observe an intermediate state with only ignore rules. Explain why an old exposed credential would also need invalidation/rotation: ignoring or untracking does not revoke it or erase history. Here every value is nonfunctional and only the marked fixture repository is changed.


---

<a id="live-ls07-record-note"></a>

### Independent fresh-marker attempt — 14 minutes

Choose a new `RUN_NAME`, predict where its marker will appear, then repeat the before check, both source edits and the Git prevention in that fresh fixture. Reuse the taught principles, but write your own explanation of what each rule excludes and what useful information it retains. Keep the before/after observations and explain why the old commit is a separate issue. No completed policy is inserted into this learner notebook.

Run `live-ls07-record` after all three checks. **Expected:** every named prevention/retention check is present and passes; a `REVIEW` or missing check means that condition is unresolved. Inspect the actual artifact and repair one rule before rerunning. This summary concerns this local synthetic fixture, not a scan of a personal project.

The summary retains your two edited policy files and selected synthetic results under `evidence/`. Rerun it after final edits, export and download the ZIP, and save your notebook notes. The disposable Git history, `.env`, `local.key` and raw fixture directory are excluded. An export preserves an incomplete attempt too; it does not certify completion.


---

<a id="markdown-22"></a>

## LS08 — Connect the controls in Colab

Use your own LS05 request matrix, continuous LS06 timeline and LS07 synthetic checks. Three questions guide the review: **is the caller recognised; is an admission available; where might a secret be copied?** Source explains the mechanism; an HTTP or fixture observation establishes the condition actually tested.

### Shared guided trace

The instructor starts one new experiment using `ls06-source`, `code-08` and `code-09`. Predict the five requests before the run, then annotate which control produced each result and which two requests used reader's allowance. Keep this worker alive while the first review round runs. At the first whole-class pause, run `ls06-renewal` after its real wait to complete the same-process trace.

Inspect the earlier LS07 ordinary/error log and prompt payload alongside the request sequence. These are separate synthetic fixture outputs, not logs emitted by these HTTP requests. Explain why correct authentication and limiting cannot, by themselves, prevent the fixture from copying a secret.

### Three review rounds

Use three 8-minute rounds, rotating the explaining learner. Allow four minutes to explain the controls, two for a peer to change a condition, one to inspect the relevant source and one to save the revised explanation. Every explainer accounts for an authentication result, caller counting and a secret-copy example. Everyone also writes their own prediction and correction.

- Round one: follow authentication, admission and validation through the retained continuous trace. Distinguish runtime configuration from a missing request header.
- Round two: change caller, path, body category or elapsed time. Predict the boundary reached. Distinguish caller isolation from renewal in the same process.
- Round three: explain all three secret destinations, inspecting one in detail. Correct an unsupported claim based on a clean screenshot, clean answer or new ignore rule.

Use the taught 2/60 rule. Different callers test isolation; renewal requires expiry in the same worker. Avoid unplanned extra requests that alter the trace being discussed.

### Independent changed condition — 12 minutes

Choose one taught condition to change. Write a prediction, then run a copied request or fresh synthetic fixture and explain the result. For an authentication/body variation start `code-05`; for a quota variation start a fresh `code-08` experiment and preserve that worker through any renewal check. The supplied renewal cell sends reader, so keep reader's exhaustion as the final `429` before testing renewal. A secret variation uses a fresh `RUN_NAME` and the local prevention/retention checks. Keep an unexecuted check explicitly pending.

After a fresh restore, `evidence/ls05-auth.json`, `evidence/ls06-timeline.json`, `evidence/ls07-<RUN_NAME>.json` and `evidence/ls07-policies/<RUN_NAME>/` retain earlier attempts. They are not new observations from the restored runtime. Regenerated caller values and a new worker require a new rate-limit timeline. Keep predictions and explanations in notebook text cells.

### Save your work

Run `save-checkpoint` only after finishing the active experiment: it stops the owned service, records the nonsecret model choices and creates a new ZIP. Download the printed ZIP through the Files panel and save your notebook. **Expected:** a unique ZIP path plus model names, with no credential values. If you need another HTTP observation after export, restart the relevant service; that new process does not continue the earlier renewal experiment.


---

<a id="markdown-24"></a>

## Summary

You can now distinguish caller and provider credentials, explain runtime configuration and the authentication/validation order, test a caller's shared allowance and real-time renewal, and prevent three secret-copy paths while retaining useful information. Your saved notebook connects a prediction, an observed result and the rule that explains it.

Keep this Live copy and its ZIP for review. Sprint 3 Live uses a separate notebook and workspace to practise streaming, logging and evaluation concepts.

## Quick recovery reference

| Symptom | Check and recovery |
|---|---|
| `PROJECT` or `service` is undefined | Run setup, then the current session's source/start cells. |
| Connection refused after export or runtime reset | Start the relevant owned service and make a new observation. |
| Statuses differ on a repeated burst | Earlier requests changed the allowance. Record them; start one new labelled experiment, then keep that worker alive. |
| Renewal cell reports no matching worker | The original process stopped or changed. Restart the experiment, not just the final request. |
| Synthetic marker still appears | Save the correct fixture policy and inspect ordinary/error logs or the outbound payload before rerunning. |
| Before-state is already safe | The named fixture preserved edits. Choose a fresh `RUN_NAME`; retain earlier work. |
| Restore refuses the folder/ZIP | Use your own Live ZIP and a destination that does not exist; fill the recorded model choices. |
| Optional provider work is unavailable | Keep both switches `False`; complete the provider-free core and mark the comparison pending. |


---
