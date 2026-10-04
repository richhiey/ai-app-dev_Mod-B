# Sprint 3 source reference

Campus students use [the local streaming and observation guide](sprint-3.md) with `service/fieldcare/` and `clients/`. The rules below describe the supplied mechanics; any notebook-specific verification describes the separate Live workflow or historical evidence.


The single Campus notebook adds a real stream route to the learner’s secured Sprint 2 service. The single Live notebook supports four separate sessions in its own workspace. Both use the same Module B OpenRouter client, ChromaDB retrieval, and LangGraph orchestration.

## Delivery path

`POST /v1/diagnose` keeps its complete JSON response for machine callers. `POST /v1/diagnose-stream` emits newline-delimited JSON events from an actual OpenRouter stream for clients that benefit from progressive reading. It does not split a completed answer into artificial chunks. A successful stream ends with `complete`; a provider/network issue may end with `error`, and partial text is not a completed answer. Usage appears only when the provider reports it.

Validation, authentication and rate limiting happen before generation. The deterministic clarification branch also stops before the provider call. The local HTTP timings describe a particular run; they are not a latency promise. Disconnecting a client does not prove that upstream generation or billing stopped at the same instant.

## Retained metadata

Observation middleware retains an explicit allowlist such as request ID, route, status, outcome, source, model, provider-reported usage, latency and safe error category. It excludes request/response text, credentials, headers, and exception details. The notebook’s synthetic marker computation checks that the allowlist excludes a marker; it is a local privacy exercise and not model output.

A runtime request ID correlates one client attempt with its terminal metadata. Equipment and evaluation IDs have different roles and do not identify a unique execution.

## Original Module A evaluation

The bundled Module A functions run against the saved pipeline design and original data. The notebook shows actual returned evaluation results for selected cases. These criteria concern retrieved documents, tool calls and response flags; they do not grade the generated answer’s prose or streaming performance. Keep evaluation evidence separate from provider response review and delivery observations.

## Delivery and verification boundary

The six Campus and Live notebooks are published in the Module B GitHub repository. Each setup cell shallow-clones `main`; Colab launch links open the reviewed notebook source revision. Static checks and local HTTP/provider-contract checks do not claim that a fresh hosted Colab run or a live provider request was performed. Review current provider availability in Colab when preparing a delivery.
