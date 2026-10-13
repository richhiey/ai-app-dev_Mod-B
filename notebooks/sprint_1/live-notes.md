# Sprint 1 Live — detailed reference

Use the [Live notebook](sprint_1_live_workshops.ipynb) during class. These notes expand its short instructions and provide recovery steps.

<a id="markdown-00"></a>

# Sprint 1 Live — Understand and extend an AI service

An **application** guides a person's interaction; a **service** exposes behavior another program can call. Across these four workshops, inspect and extend a small, domain-neutral FastAPI example. Colab is the client; the example accepts a question and optional reference context. The learning is about routes, contracts, versioning and model calls—not a business project.

## Outcomes and navigation

| Session | Learning outcome | Start here |
|---|---|---|
| LS01 | Distinguish an AI application from an AI service; tour the provided FastAPI scaffold and identify routes, inputs, outputs, and model call. | [Predict, call, locate](#markdown-02) |
| LS02 | Extend the provided scaffold with a new endpoint, define its input/output contract, and version the route. | [Extend the scaffold](#markdown-05) |
| LS03 | Define clear input/output contracts for service endpoints and apply /v1, /v2 versioning to model and prompt changes. | [Compare versions](#markdown-08) |
| LS04 | Demo a new endpoint added to the scaffold with a clean contract and a versioned route. | [Demonstrate and review](#markdown-11) |

### Start a working copy

1. Save an editable copy of this notebook in Colab. Connect a standard Python CPU runtime; no GPU is needed. Run [setup](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_live_workshops.ipynb#scrollTo=setup) and wait for the printed workspace path.
2. Run the current session's cells in order. **Do not use Run all:** the notebook pauses for source edits and a model choice.
3. Add predictions and explanations in your own text cells. Save the notebook **and** download the Live source ZIP after each session. Colab does not save runtime files with the notebook; see the [Colab FAQ](https://research.google.com/colaboratory/faq.html).

Setup installs the course lock from a fresh clone of `main`. It creates or reuses a marked Live workspace without replacing files. `REPO` is the read-only reference source; edit `PROJECT`. The standalone example lives under `service/concept_api/`. Its deterministic checks need no provider key. Provider calls stay off until you deliberately opt in.

**Expected after setup:** a workspace path, source revision and two non-secret model choices. Setup does not start a service or call a provider.

### Resume safely

| Situation | What to do |
|---|---|
| Same runtime, same work | Keep `LIVE_ARCHIVE` empty and the same `LIVE_FOLDER`; run setup, then the current session's start cell. Source edits remain. |
| Fresh runtime, saved work | Upload your Live ZIP, set `LIVE_ARCHIVE`, select the saved model names in `RESTORED_MODELS`, then run setup. Choose a new `LIVE_FOLDER`. |
| Fresh work | Leave `LIVE_ARCHIVE` empty and choose a new folder name if the default already exists. |

The service binds to loopback inside the notebook runtime. Use the HTTP cells to call it; opening its printed address in your laptop browser will not reach Colab.


---

<a id="markdown-02"></a>

## LS01 — Predict, call, locate

An **endpoint** is an operation selected by an HTTP method and path. A **schema** declares fields, types and constraints. JSON carries those fields between client and service. The HTTP status describes request handling; the response body's `status` describes the example's result.

**Trace the source.** Read `ls01-source`. In `main.py`, find router registration; in `routes.py`, find `POST /v1/answer`; in `schemas.py`, locate `AnswerRequest` and `AnswerResponse`. In `service.py`, find the early return and possible model call. Follow the request through these pieces rather than trying to memorize every line.

Before running `code-03`, predict which steps each request reaches. Run `ls01-start`; its printed URL means the owned service passed its startup check. Then call the service. No provider key is needed.


---

<a id="markdown-04"></a>

**Compare with your prediction.** A question without context returns HTTP `200` and `needs_context`; `{}` returns `422` with validation details. Read `status_code` and the response body separately. The first request is accepted but returns before model work; the second fails the input contract before the handler.

Trace the early return before the `OpenRouterClient` call. An application can use these distinctions to request missing context or display a validation message. The example context is ordinary text supplied by the caller; the lesson does not depend on a business domain.

**Your independent check.** Choose an incomplete or invalid request, write your prediction, then change one input and run it in a new code cell using the demonstrated HTTP pattern. Record the method/path, input and output schemas, possible model-call location, actual status/body and a justified client action. Mark the reached and skipped steps. A copied source listing alone does not complete the task.

If a call reports connection refused, rerun `ls01-start` and retry the same request. A `422` is an observed validation response, not a notebook execution error or model refusal. Keep source unchanged in this session.

---

<a id="provider-note"></a>

### Optional provider preparation — after the deterministic checks

You can complete the core source/contract exercises without a provider. Opt in only to observe generated behavior: run the next cell to enter the provider key privately. Keep it out of code cells, outputs and archives.

After preparation succeeds, set `RUN_PROVIDER = True` in `ls01-provider`. Expect an actual response or an explicit error: `200`/`ready` with an answer is different from `200`/`needs_context` or `502` for a provider failure. Exact wording varies. The generated answer uses only the supplied context; inspect whether it is supported. A healthy process does not establish answer quality.

If the call fails, leave generation pending and return to deterministic checks by rerunning the relevant start cell. Reset the switch to `False` after the deliberate provider run to avoid accidental repeat calls. The saved ZIP contains neither credentials nor provider state.

---

<a id="markdown-05"></a>

## LS02 — Extend the scaffold

A function inside a codebase is not yet an operation another program can call. The route exposes it; schemas describe the exchange; the handler connects that promise to behavior. A prompt changes model instructions, not input validation.

**Guided example.** Read `ls02-source`. In `brief_routes.py`, locate the request/response models, route, and route-specific prompt. In `live_extension.py`, find where the router is registered. Run `ls02-start`, then `code-06` with `/v1/answer-brief`. Expect an accepted question without context to return `needs_context` and `{}` to return `422` on both the example and original route.

### Make a second operation

Add a separate `/v1/answer-structured` operation with named request and response schemas. Its request keeps the base question/context rules and adds `format`, limited to `bullets` or `question_list`, defaulting to `bullets` when omitted. Its response includes the selected `format` alongside `answer`, `status` and `references`, including when the service asks for context. Connect the route to the shared answer behavior with its own model instructions, register it once, and keep both supplied routes working. A provider call is optional; deterministic contract responses can be checked without one.

Write a contract card with method/path, required and optional fields, constraints, output fields and response states. Let someone use it to predict a request and interpret its response. Keep the work in `PROJECT/service/concept_api/`; the linked GitHub source is a read-only reference. After saved source changes, restart with `ls02-start` before testing.


---

<a id="markdown-07"></a>

**Check what the evidence supports.** Compare the registered input/output declarations and each response with your contract card. These calls test validation, clarification and preservation of the original operation; they do not exercise generated wording. Source inspection establishes which prompt is configured. A separately opted-in provider call is needed to observe its effect, and one answer does not establish general quality.

| Symptom | Check and recovery |
|---|---|
| Startup/import error | Check the saved filename, import, indentation and router name. Repair that source, then restart. |
| New path missing or `404` | Check the exact method/path and `include_router`; save and restart. |
| Expected clarification becomes `422` | Compare the optional context declaration and its constraints. |
| Original route changes too | Inspect edits to shared files. Undo only an unintended change and retest both routes. |

Save the notebook and Live ZIP now if the session is ending. After export stops the service, rerun the relevant start cell before another request.

---

<a id="markdown-08"></a>

## LS03 — Compare contracts and change one version

A **contract** is the caller/service agreement about accepted inputs and returned outputs. A version lets a caller deliberately select an agreement. A new path alone does not protect existing callers if both handlers use a changed shared schema, prompt or model setting.

The example keeps `/v1/answer` at a 2000-character question limit and adds `/v2/answer` with a 600-character limit. V1 uses `OPENROUTER_MODEL`; v2 selects `OPENROUTER_MODEL_V2` explicitly. The LS02 route remains registered through `live_extension.py`.

1. Read `ls03-source`. Locate each version's schema, prompt and model binding. Predict what a 700-character question without context will do on each path.
2. Run `ls03-model-before` to record both selected model names and source digests. A digest is a fingerprint used here to detect file changes.
3. Choose a different approved v2 model in `ls03-model-change`. Run it **before editing source**: it checks that v1 and the source bindings stayed unchanged.
4. Run `ls03-start`, then `code-09`. V1 should accept the long input and clarify; v2 should reject it. Inspect the actual results before concluding the expected boundary held.

Selecting a model and checking source does not call that model. Keep claims about configuration separate from generated behavior. If you repeat the experiment, first restore the intended comparison state and save the before record.

---

<a id="markdown-10"></a>

**Your independent version change.** Keep the model-only before/after record first. Then change only the instruction appended to `PILOT_PROMPT` in `pilot_routes.py`; choose a different response style while preserving the shared instruction to use only supplied context. Restart `ls03-start` and repeat `code-09`. Do not change the v1 schema, prompt, model or your LS02 operation.

Record which source/configuration changed, which original-caller agreement stayed fixed, and what the calls actually tested. If you opt into provider calls, compare the same supported request on both routes to observe generated behavior. Otherwise say the prompt effect remains unobserved; an accepted request without context does not use the prompt.

Write a migration condition: name a caller, the input/output adaptation it needs, and an observation that would justify retiring its old route. Deprecation announces migration; it does not remove or redirect the route. Keep v1 callable while callers still depend on it.

---

<a id="markdown-11"></a>

## LS04 — Demonstrate and review your extension

Demonstrate the operation you added in Colab, explain its named input/output contract and versioned path, and use a request to test that explanation. The supplied brief and pilot examples are patterns; they do not replace your own extension.

Before the review, confirm that your LS02 source and registration are saved. In a fresh runtime, restore your saved ZIP and read `ls03-source`, then run `ls03-start` and `code-09` to recreate the version comparison. Run `code-12` for a focused contract check. An incomplete accepted request should return `needs_context`, an empty body should return `422`, and the original version should accept the long question.

The review can use a live call, source trace, request/response record, peer question, or another format that helps make the contract visible. Every learner should be able to explain their own extension. Keep claims tied to evidence: a contract check does not verify generated answer quality, and one passing request does not cover every possible input.

---

<a id="markdown-13"></a>

**Independent verification.** Choose one mismatch or missing check raised by the review. Save the starting observation, predict the result that would resolve it, then make one justified repair or test the existing behavior. Restart only if source/configuration changed. Repeat the request and relevant original-route check. A justified no-change decision needs an observation too.

In your own notebook text cell, record the method/path and schema names, observed request/response, code that explains it, the peer's challenge, the repair or confirming check, and one remaining limitation. Keep the v1/v2 comparison and separate model/prompt evidence alongside it. Label replays as replays; for a blocked run, name the pending check.

---

<a id="markdown-14"></a>

## Save your Live practice

Run `save-checkpoint` after any session. It stops the owned service, saves the two non-secret model selections, and exports your current Python source plus selected `.md`/`.json` evidence. It does not grade completion; unfinished work is still worth saving.

1. Save your notebook text cells and outputs. The ZIP does not contain this notebook; predictions, contract notes and reviewer observations remain there unless you also save them under `PROJECT/evidence/`.
2. Run the export cell, keep the printed model choices with your notebook, and download the exact ZIP path it prints. Save it before disconnecting.
3. In a fresh runtime, upload the ZIP and use the restore instructions at the top. Archives exclude credentials and runtime state. Never paste keys into evidence files.

To continue immediately after saving, rerun the current session's start cell before making another request. The Live practice remains separate from the Campus project.

---
