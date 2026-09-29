# Architecture and notebook authoring contract

## One module repository

The module owns a shared installable package (`module_b`), teaching examples, notebooks, fixtures and tests. FieldCare is the first cumulative example. Generic helpers accept a workspace, file policy, or ASGI app/factory path and can support another case; case-specific probes live in `module_b.fieldcare` rather than in every notebook.

The earlier FieldCare-only repository remains untouched for provenance. Its baseline application files are imported into `examples/fieldcare`. This new module repository is the canonical source for notebook development; changes are made here, not independently maintained in two services.

## What belongs where

| Layer | Contents | Rule |
|---|---|---|
| `src/module_b` | Process lifecycle, workspace preservation, source inspection, reusable data/display operations, probes | All shared helpers belong here. No copied helper function bodies in notebooks. |
| `examples/fieldcare/app` | Route/schema/application/model implementation | Visible teaching source; learners edit prepared working copies. |
| `examples/patterns` | Supplied analogous patterns | Small enough to inspect; separate from assessments and the clean baseline. |
| `notebooks` | Case, LO, explanatory Markdown, actual calls/configuration, expected observations and checks | Exactly one Campus and one Live notebook per sprint; sections preserve lesson types and outcomes. Target Colab and execute locally. |
| `scripts` | Author verification | Not learner cells or runtime application logic. |
| `tests` | Failure and boundary checks | Test behaviour, ownership, preservation and true HTTP execution. |

A small initial bootstrap cell is necessary before the shared package can be imported. It locates a local checkout or clones the configured GitHub release and installs it; it is folded in Colab. All subsequent repeated logic is imported. The notebooks do not embed a second copy of the service.

## Lifecycle

Prepare a workspace → start one owned Uvicorn process → perform explicit HTTP calls → inspect exact workspace source → save work → stop that owned process. Startup uses a pre-bound loopback socket and readiness checks; it cannot claim an unrelated listener is its server. Rerunning the same startup cell reuses its process. Selecting another workspace stops/replaces the old process before serving the new one.

Local source inspection never imports or executes the inspected file. FieldCare probes run a fresh subprocess so stale `app` imports cannot redirect them to another workspace. Their internal TestClient requests are labelled separately from the notebook's TCP requests.

## Progression over four sprints

1. Service scaffold, fixed schemas, route-local prompt configuration and later endpoint versioning.
2. Auth/secret handling and per-key limiting, with caller-isolation and recovery evidence.
3. Diagnostic streaming, structured redacted events and authentic existing-evaluator integration.
4. Minimal companion UI through a trusted connector: one form, one response, one correlated event; manual tests and documentation.

The [curriculum map](curriculum.md) includes every Campus/live row. Later capabilities are planned additions, not fake empty APIs or completed assessment solutions. Add shared utilities at the point of first verified use. Preserve prior notebook checks when extending a service snapshot.

## Scope and external dependencies

The supplied service is a bounded synthetic HX equipment/document slice. It has no full Module A tool pipeline, decision flags or evaluator. Sprint 3 adds explicit replay/evidence routes for the frozen original Module A application and binds its unchanged evaluator to the same saved design loaded by those routes. The original bounded diagnostic route remains unchanged. An unrelated scorer is not an acceptable substitute.

Sprint 4 needs actual service reachability, a trusted server-side connector, credential handling and verified stream rendering. Colab is the interactive programming environment; it is not a permanent public hosting plan. The buffered machine handover and human-facing diagnostic stream are different contracts.

TypeSafe was considered under the standing preference. This foundation adds deterministic infrastructure and retains the existing service; it needs no additional semantic model call. Later semantic routing/verification can be assessed when authored, without replacing deterministic auth, quotas or execution rules.

## Core generalization review — 28 September 2026

The process runner no longer injects FieldCare/OpenRouter rules. `module_b.fieldcare.demo_service` owns that case policy. Readiness status/path/headers, environment inheritance/removal and ASGI factories are explicit configuration. Source inspection supports alternate roots and non-Python components; data readers handle arbitrary JSON shapes and JSONL. Checkpoint policies support future source/UI/event layouts without letting an archive broaden its own permissions. A second independent ASGI example and alternate-layout round trips test reuse.

Current notebooks use the new case-specific factory while preserving visible teaching operations. Shared helpers remain in `src/module_b`. The package is `0.2.0`; the earlier foundation tag remains unchanged. [Extension contract](extending-the-core.md) documents how to add future components without editing unrelated core helpers.

## Current consolidated delivery

Version 0.7.0 supplies one output-free notebook each for Sprint 1 and Sprint 2. Future sprints follow the same contract. Setup once; preserve named stages; export once; verify in memory and retain JSON evidence. Earlier version notes in this document are historical.

## Observable service (0.8.0)

One cumulative Sprint 3 notebook adds NDJSON delivery, an outer ASGI metadata logger and the original Module A evaluation bridge. A scripted delayed fixture rehearses transport; a separate incremental provider adapter is optional. The loaded design digest is captured at process startup, so later file edits cannot relabel an old pipeline. The original evaluator remains deterministic and cannot certify live wording. See `sprint-3-observability.md`.
