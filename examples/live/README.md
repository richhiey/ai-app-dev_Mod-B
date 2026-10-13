# Live lesson example services

The active domain-neutral Live example for Sprints 1–3 is [`sprint1_concept_api/`](sprint1_concept_api/). Each Sprint 1–3 Live Colab copies this package into its isolated `service/concept_api/` workspace. It provides the FastAPI routes and contracts used to teach request handling, endpoint extension, versioning, authentication, rate limits, streaming, and structured observations. Provider calls are explicit opt-ins; deterministic route and contract checks work without a provider key.

| Lessons | Active files in `sprint1_concept_api/` | Concept |
|---|---|---|
| LS01–04 | `main.py`, `routes.py`, `schemas.py`, `service.py`, `brief_routes.py`, `live_extension.py`, `pilot_routes.py`, `live_versions.py` | Application/service boundary, endpoint registration, request/response contracts, and versioned prompt/model behavior |
| LS05–08 | `security_settings.py`, `live_auth.py`, `live_limits.py` with the base service | API-key checks, safe secret configuration, per-key limits, and secured-service review |
| LS09–12 | `stream_routes.py`, `live_stream.py`, `live_observed.py`, `live_logging.py` with the secured service | Streaming, safe structured observations, and the evaluation feedback connection |

The older modules directly under `examples/live/` import the Campus `fieldcare` application. Treat them and the corresponding `service/fieldcare/` compositions as historical maintainer references, not the student path for Sprints 1–3. New Live lessons use the neutral package above. Keep the Campus application itself unchanged by these concept exercises.

Each active composition is started as its own service process. The notebook helpers own setup, composition, and shutdown; learners should not import multiple compositions into one running app. Caller credentials stay in private runtime configuration, never in source or logs.

## LS13–LS14 local interaction lab

Use [`streamlit/README.md`](streamlit/README.md) for the neutral Streamlit starter, reference, explicit Demo scenarios and local HTTP fixture. The optional provider mode uses the same concept service and approved OpenRouter integration. The Sprint 4 notebook is a planning/evidence aid; application execution stays local.
