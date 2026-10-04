# Module B curriculum map

Current delivery: Sprint 1 Campus uses Colab; Sprint 2–3 Campus use VS Code and local terminals on Windows/macOS. Live sessions retain their own notebooks. The course outcomes and lesson types below are unchanged. See [local setup](local-development.md), [Sprint 2](sprint-2.md), and [Sprint 3](sprint-3.md) for current instructions.

## Sprint 1 — From Application to Service

Service/process lifecycle, fixtures, source inspection and trace probes are implemented. The handover extension now has a learner task and separate verified reference; versioning now has guided and reduced-support states, and the Sprint 1 assessment has a blank learner notebook with reserved validation outside the shared source.

| ID | Lesson/session | Type/format | Learning outcome |
|---|---|---|---|
| B-C01 | Application vs service | Concept Note | Distinguish an AI application (used directly) from an AI service (called by other systems) and explain why the difference matters for design choices. |
| B-C02 | REST in plain language | Concept Note | Explain REST endpoints, HTTP methods, and status codes at the level needed to understand and configure an AI service — not to design an API from scratch. |
| B-C03 | Touring the provided FastAPI service | Practical Walkthrough | Tour the provided FastAPI scaffold that wraps a Module A-style application; identify the routes, inputs, outputs, and where the model is called. |
| B-C04 | Extending the scaffold for a new use case | Independent Practice | Extend the provided scaffold by adding a new endpoint that calls the model with a different prompt — focused on configuration, not authoring from scratch. |
| B-C05 | Why contracts matter for AI services | Concept Note | Explain why downstream systems need predictable inputs and outputs and how validation prevents whole categories of failure. |
| B-C06 | Why and how to version AI endpoints | Concept Note | Apply endpoint versioning (/v1, /v2) so model and prompt changes can be deployed and deprecated independently. |
| B-C07 | Service scaffold checkpoint | Assessment Lesson | Extend the provided service scaffold with one new endpoint, define its input/output contract, and version the route. |
| B-LS01 | LS 1 — Application vs service and REST orientation | 60 min: framing + scaffold walkthrough | Distinguish an AI application from an AI service; tour the provided FastAPI scaffold and identify routes, inputs, outputs, and model call. |
| B-LS02 | LS 2 — Extending the scaffold | 60 min: extension workshop | Extend the provided scaffold with a new endpoint, define its input/output contract, and version the route. |
| B-LS03 | LS 3 — Input/output contracts and versioning | 60 min: contract and versioning workshop | Define clear input/output contracts for service endpoints and apply /v1, /v2 versioning to model and prompt changes. |
| B-LS04 | LS 4 — Sprint 1 checkpoint | 60 min: scaffold review | Demo a new endpoint added to the scaffold with a clean contract and a versioned route. |

## Sprint 2 — Securing and Limiting an AI Service

Learners configure private local caller values, attach the guard, design two-caller request timelines and inspect rejection boundaries. Authentication and limit attachment remain visible in their source.

| ID | Lesson/session | Type/format | Learning outcome |
|---|---|---|---|
| B-C08 | API keys in plain language | Concept Note | Explain what API key authentication does, why AI services need it, and where the keys live. |
| B-C09 | Adding API key auth to the scaffold | Practical Walkthrough | Apply API key authentication to the provided service scaffold using a provided pattern. |
| B-C10 | What is a secret and where it should live | Concept Note | Define which values count as secrets, where they should and should not live, and the most common ways they get leaked — including logs, prompts, and version control. |
| B-C11 | Why AI services need rate limits | Concept Note | Explain why AI services need rate limits — cost, abuse, fairness — and the common patterns (per-key, per-endpoint, per-IP). |
| B-C12 | Applying per-key rate limits | Independent Practice | Apply per-key rate limiting on the service scaffold and observe behavior under burst traffic. |
| B-C13 | Secured service checkpoint | Assessment Lesson | Apply API key auth, environment-based secrets, and per-key rate limiting to the project service. |
| B-LS05 | LS 5 — API key auth and secrets management | 60 min: auth and secrets workshop | Apply API key authentication and safe secret handling to the project service. |
| B-LS06 | LS 6 — Rate limiting AI endpoints | 60 min: rate limit workshop | Apply per-key rate limiting to the project service and observe behavior under burst traffic. |
| B-LS07 | LS 7 — Secrets safety in practice | 60 min: secret-leak workshop | Walk through the most common ways secrets leak (logs, prompts, repos) and apply patterns to prevent each. |
| B-LS08 | LS 8 — Sprint 2 checkpoint | 60 min: secured service review | Demo the project service with API key auth, secret handling, and per-key rate limiting in place. |

## Sprint 3 — Streaming and Observability

Learners attach streaming and safe observation, inspect terminal events, and select original Module A cases to investigate a service concern. The evaluator runs the saved reference design; it does not score live generated prose.

| ID | Lesson/session | Type/format | Learning outcome |
|---|---|---|---|
| B-C14 | When streaming helps | Concept Note | Explain when streaming improves user experience for AI endpoints and when it is unnecessary complexity. |
| B-C15 | Enabling streaming on the scaffold | Practical Walkthrough | Enable streaming on the provided service scaffold and observe the difference from the client side. |
| B-C16 | What to log and why | Concept Note | Identify the signals worth logging — request IDs, model used, tokens, latency, errors — and why each matters for debugging and cost tracking. |
| B-C17 | What NOT to log | Concept Note | Identify content that should not be logged (personal data, sensitive prompts, full secrets) and apply provided redaction patterns. |
| B-C18 | Closing the loop with existing evaluation | Concept Note | Use service logs as a feedback signal into the evaluation framework introduced in Module A — extending existing eval work rather than building a new framework. |
| B-C19 | Observable streaming service checkpoint | Assessment Lesson | Enable streaming, add structured logging with redaction, and connect logs back into the existing evaluation framework from Module A. |
| B-LS09 | LS 9 — Enabling streaming on the scaffold | 60 min: streaming workshop | Enable streaming on the project service and observe the difference from the client side. |
| B-LS10 | LS 10 — Structured logging for AI services | 60 min: logging workshop | Add structured logging that captures request ID, model, tokens, latency, and errors — with redaction for personal data and sensitive prompts. |
| B-LS11 | LS 11 — Logs feeding back into evaluation | 60 min: eval feedback loop | Connect service logs back into the evaluation framework from Module A — no new eval framework built. |
| B-LS12 | LS 12 — Sprint 3 checkpoint | 60 min: observability review | Demo the streaming service with structured logging, redaction, and the eval feedback hook. |

## Sprint 4 — Project: AI Service with Companion UI

Planned: trusted connector, diagnostic stream renderer, correlated interaction evidence, contract mapping and reproducible end-to-end checks. External UI hosting still needs verification.

| ID | Lesson/session | Type/format | Learning outcome |
|---|---|---|---|
| B-C20 | Scoped companion UI using Lovable + Supabase | Practical Walkthrough | Use a vibe coding tool (Lovable or Bolt.new) to build a minimal companion UI on top of the project service. Lovable uses Supabase as its built-in backend — no separate Supabase setup required. Required scope: one input form, one response display, one logged interaction. Auth and streaming use provided patterns; richer dashboards are explicit extension tasks, not required for credit. |
| B-C21 | Connecting the UI to the service | Independent Practice | Wire the scoped vibe-coded UI to the project service endpoints using provided auth and streaming patterns. |
| B-C22 | Manual end-to-end tests | Independent Practice | Run manual end-to-end tests across the UI → service → model path and document integration failures. |
| B-C23 | README and API docs | Independent Practice | Write a README and basic API documentation so another team member could call and understand the service. |
| B-LS13 | LS 13 — Scoped vibe-coded companion UI with Lovable | 60 min: companion UI build (scoped) | Build a scoped companion UI using Lovable (Supabase backend built in — no separate setup): one input form, one response display, one logged interaction. Richer dashboards are extension tasks, not required for credit. |
| B-LS14 | LS 14 — End-to-end integration and documentation | 60 min: integration and docs | Run end-to-end tests across UI → service → model and write the README and API documentation. |
| B-LS15 | LS 15 — Presentation Day | 60 min: project demos | Present the AI service and companion UI; defend auth, observability, streaming, and integration decisions. |
| B-LS16 | LS 16 — Code Clinic | 60 min: group review | Group review focused on contracts, auth/secrets, observability, streaming, and UI integration across learner projects. |

## Release dependencies

- B-C03 is a guided execution tour; C04 receives the separate analogous fixed-schema route rehearsal. Do not include the assessed dispatcher solution in helpers.
- C18/C19 and LS11/12 preserve authentic `evaluate_case`, `evaluate_fieldcare_pipeline` and `run_eval_case` semantics. Evaluation runs the saved reference design, which is distinct from the served OpenRouter graph; learners must explain that boundary.
- Runtime request IDs, fixture request IDs and evaluation IDs remain separate. Select a case and relevant companion case using sanitized metadata; logging does not prove answer quality.
- C20–21/LS13–14 use a human-facing diagnostic stream while retaining the buffered machine handover. Supply a trusted credential boundary and reachable service; do not expose service keys in browser code.
- Supplied source is shared, but lesson-type differences remain: worked steps for walkthroughs, constrained tasks/hints for practice, unseen variants for assessment, and diagnosis/comparison for live sessions.
