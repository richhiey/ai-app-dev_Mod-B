# Shared helper API

| Import | Purpose | Evidence boundary |
|---|---|---|
| `module_b.workspace.prepare_example` | Copy an example once; preserve marked workspace edits on rerun | Does not reset or silently upgrade learner files. |
| `module_b.workspace.export_workspace` | Write a new source checkpoint ZIP | Allowlisted files; not a scanner for secrets embedded in source. |
| `module_b.workspace.restore_workspace` | Validate checkpoint and restore into a new folder | Refuses unknown paths, links and existing destinations. |
| `module_b.runtime.ServiceProcess` | Own/start/check/stop any supplied ASGI app/factory with explicit env/readiness settings | Real TCP service; not hosting and not provider readiness. |
| `module_b.source.source_excerpt` | Read Python source/definitions under configurable roots, including decorators | Reads actual working files without importing them. |
| `module_b.data.load_fixture` | Read a named JSON fixture from a selected directory; any JSON shape | Caller sees and sends the body explicitly. |
| `module_b.display.show_response` | Print status and body | Does not print request headers/URLs; response content is still real content. |
| `module_b.fieldcare.trace_paths` | Count real function boundaries in separate demo TestClient requests | Not counters from an earlier running-server request. |
| `module_b.fieldcare.verify_prompt_binding` | Inspect distinct route bindings with mocked provider HTTP | Not generated-wording/provider-connectivity evidence. |

Additional public APIs:

- `module_b.fieldcare.demo_service`: explicit FieldCare demo configuration for the generic runner.
- `module_b.workspace.WorkspacePolicy`: immutable, caller-owned checkpoint directory/extension policy, passed to both export and restore.
- `module_b.source.source_text`: display complete non-Python source under explicitly allowed roots/extensions.
- `module_b.data.load_json` and `load_jsonl`: read arbitrary JSON values and JSON Lines records within the selected project.

See [extension examples and migration notes](extending-the-core.md).

## Small explicit cells

```python
payload = load_fixture(project, 'valid-request')
response = httpx.post(f'{service.base_url}/v1/diagnose', json=payload)
show_response(response)
assert response.status_code == 200
```

Keep method, route, body and checks visible. Helper reuse should reduce setup, not remove the operation a learner is meant to understand.

## Future additions

Caller-control observations are implemented for Sprint 2 below. Future work may add stream observation alongside streaming and event inspection/fixture selection alongside logging/evaluation. Auth guards, quota settings, yields, log fields and the original evaluator call remain visible teaching code. No future helper here is claimed implemented until it has a real consumer and behavioural tests.

## Configurable FieldCare extension checks

`inspect_route_bindings(project, routes)` accepts a mapping of POST path to route-module import path. It runs fresh in-process test requests with blocked network access and a mocked provider. Reports distinguish registration, fixed request/response schemas, route-owned prompt binding, distinct prompts and valid/invalid/incomplete call counts. A failed result reports safe diagnostic codes, not prompt text or credentials. It never assesses generated-answer quality or supplies a completed route.

## Contract boundary observations

`module_b.contracts.inspect_contract` observes declared input limits, accepted/invalid/clarification behaviour, and an intentionally malformed output injected after the service function returns. Route/module/field/adapter settings are explicit; the default seam follows the supplied FieldCare service. This is a no-network, demo-only process that never edits the selected workspace. Adapter invocations are not external model calls. Optional authored output examples are checked for shape only, never scored for factual quality. See section 4 of the Sprint 1 notebook and `docs/contract-note-verification.json`.

The optional `expected_input_model` names a reference request model. The check compares generated validation schemas and model configuration, ignoring schema annotations such as titles/descriptions and allowing the specified input field's maximum length to differ. Actual property names and values inside defaults/enums remain significant. This supports a bounded contract change while retaining the other declared rules, including trimming. It is not a proof that arbitrary custom validators are equivalent.


## Guarded source edits and independent version bindings

`module_b.edits.write_source(project, relative, source, expected=None)` creates a Python file or replaces exactly the reviewed prior text. An identical rerun is a no-op. Unexpected content, traversal and symlink paths are refused; the notebook keeps the route/schema/diff visible.

`module_b.edits.source_fingerprint(project)` hashes the Python source under `app` with stable file ordering. C06 records it during checks and compares it again before saving completion evidence. Changed source requires new observations; the digest is a freshness check, not proof of correctness or a fingerprint of external dependencies and data.

`module_b.versioning.inspect_version_bindings(project, versions=..., changed_route=..., accepted_payload=...)` accepts a mapping from POST paths to `{module, model_env}`. It supports FieldCare-compatible modules exposing `SYSTEM_PROMPT` and `MODEL_NAME` and using the shared provider adapter. A fresh, credential-cleared process injects different synthetic model values, calls both routes through FastAPI, then changes only the chosen module's constants in memory and calls again. The report contains statuses, prompt hashes, synthetic model names and binding booleans. External sockets are blocked; provider HTTP is mocked. Unexpected model strings and learner exceptions are not returned. No files are changed. This is reusable across compatible route pairs, not a generic evaluator for arbitrary service architectures.

These observations prove local configuration wiring, not actual TCP connectivity, deployed isolation, provider support for a model, or generated-answer quality. C06 records actual local HTTP separately.


## Cumulative assessment workspaces and evidence freshness

`module_b.checkpoints.prepare_checkpoint(destination, checkpoint=..., recovery_files=...)` copies a selected source folder or exported ZIP without changing the original. Recovery overlays are used only when explicitly supplied without a checkpoint; a missing selected checkpoint raises an error. Rerunning preserves the workspace and its saved baseline. The baseline records inherited Python source and JSON evidence hashes before editing. It is a teaching record, not a tamper-proof grading record.

`module_b.edits.content_fingerprint(project, directories=('app', 'data'), suffixes=('.py', '.json'))` extends source freshness checks to selected data. The assessment records this digest and a copy of the chosen route, model settings and request payloads when observations run. Changed source, evidence or choices requires rerunning the observations before saving readiness.

`module_b.edits.preserves_statements(original, current)` checks that original top-level Python statements remain in order while permitting additions such as route registration. It does not prove that added code has no side effects; use it alongside actual inherited-route and binding observations.

The public assessment section supplies orchestration and evidence recording. Its supervisor implementation and held-out authoring checks live outside this repository and are kept outside the published learner repository. Structural readiness never substitutes for real generated-answer review or a grade.

## Consolidated notebook workflow (0.7.0)

- `module_b.notebook.table` renders selected observations as escaped HTML. Never give it secrets or environment dictionaries.
- `apply_student_edits` validates all paths/syntax before applying explicit student source; empty input is a no-op. `register_source` appends a visible registration once.
- `baseline` retains a stage's incoming source/data once. `preserved` checks inherited files and additive-only main registration.
- `revision` fingerprints application Python and data JSON. `fresh` also compares request/experiment selection snapshots where supplied.
- `observe_change` combines real demo HTTP, independent contract/binding probes and inherited-source checks for a learner-defined new versioned operation. It uses a baseline-compatible request for inherited operations, since the new route may accept inputs outside an older route's limit. It creates no solution and judges no generated wording.
- `provider_service` is explicit opt-in, requests a hidden key, owns the live child process and clears retained runtime configuration on exit.
- `export_progress` saves current source, evidence, notes and distinct readiness states to one checkpoint ZIP, never a notebook copy.
- `module_b.security_lab.review_security` checks the learner's chosen timeline against admission accounting and probes all inherited routes, missing runtime configuration, source preservation and public GET behavior. It requires same-caller cross-route pooling and staggered caller-window renewal, and explicitly observes accepted recovery after each missing-variable refusal. Its actual HTTP burst also requires admission for a second caller after another has exhausted its allowance. It snapshots selections and rejects stale observations. It is evidence checking, not an instructor grade.

Both final notebooks retain their own visible HTTP requests, configuration and decisions. Verification executes in memory and writes JSON. There are no executed/reference `.ipynb` deliverables.

`module_b.security_lab.configuration_template_ok` checks that a submitted template contains exactly the required caller variable names with nonfunctional `<set-in-runtime>` values. It does not validate actual credentials or replace a human review for secrets embedded in source and notes.

## Sprint 3 helpers (0.8.0)

- `streaming`: labelled delayed fixture; genuine provider SSE parser with multiline/comment framing, safe errors, usage and clean-stop validation.
- `observability`: one terminal ASGI record per request; metadata/value allowlists; guard failures and cancellation; never raw payload logging.
- `evaluation`: authentic frozen Module A pipeline and evaluator using the service's saved design; provenance in `_module_a/provenance.json`.
- `observability_lab`: preserve/import workspaces, register routes before static guards, collect actual HTTP events, review source/configuration freshness, and run bounded safe probes.

The notebook keeps routes, yields, HTTP calls, log fields and the original evaluator call visible. FieldCare-specific teaching probes are not a production monitoring system.

### Sprint 3 refinement (0.8.1)

`observability_lab.registered_routes` inventories registered static POST operations in a credential-isolated import process, including hidden routes. `probe_checkpoint` labels its uninterrupted quota/isolation run separately from the fresh buffered/cancellation/recovery run. Readiness now requires actual client progress, buffered equivalence, invalid-input handling and correlated terminal outcomes. See [the full evidence boundaries](sprint-3-observability.md#checkpoint-evidence-boundaries).

## Live-session evidence and synthetic secret fixtures

`module_b.live_sessions` saves individual public practice observations and written reasoning into the student service’s `fixtures/live-session-records.json`. It retains other session records, declares source provenance and revision, and never assigns a grade. `ready_for_discussion` means the record has observations and nonblank reasoning; it is not a correctness verdict.

`module_b.secret_workshop` creates and probes only marked disposable synthetic repositories for the three live secret-prevention cycles. Learners visibly apply separate log selection, prompt construction and Git exclusion/untracking patterns. The probe inspects actual saved ordinary/error logs, a local outbound payload and the Git index/history. It preserves useful content and distinguishes future inclusion from prior exposure. It is not a general secret scanner or a sandbox for untrusted Python.
