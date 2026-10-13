# Sprint 4 Live notebook — UI integration and optional API observation

Open [the Live notebook](sprint_4_fieldcare_live.ipynb) for LS13–LS14. It contains the exact outcomes, a local UI/integration sequence, a learner evidence card, and a separate optional API observer. Use one saved copy for both sessions.

The required UI work uses the local Streamlit project described in the [Sprint 4 guide](../../docs/sprint-4.md) and [Streamlit teaching kit](../../examples/streamlit/README.md). The [Lovable exploration](../../docs/lovable-student-guide.md) is optional: a small mock preview and useful notes are enough. A sketch or skipping it is valid; no paid features, export, publication, Cloud setup or generated artifact is required. The core project does not depend on Lovable.

## Delivery sequence

| Session | Notebook sections | Evidence |
|---|---|---|
| LS13 — companion UI | Introduction and `ls13-ui` | One input form, actual response state, same-run safe request record; one independently chosen improvement. |
| LS14 — integration and documentation | `ls14-integration` and evidence card | Normal path, controlled service failure, README/API/UI instruction changes and reader retry. |
| Optional API diagnosis | `setup`, `s4-boundaries`, `s4-supported`, `s4-observations`, `save-checkpoint` | Direct API metadata only; distinct from local browser/connector evidence. |

The observer starts disabled. Setup clones `main` and installs the course lock; it prints the runtime revision. Enable hosted observation only with a facilitator-provided HTTPS origin and caller credential in Colab Secrets (or private environment variables for local Jupyter). Never put a provider credential in this notebook. Supported generation has a second explicit opt-in. Redirects are not followed. Rate-limited responses preserve `Retry-After`; wait before repeating a single request.

The JSON export excludes keys, bodies, generated text, citations and raw headers. It records skipped work as `not_executed`, keeps failures, reports fixture/live mode, and never treats HTTP 200 or visible text as proof of generation. Local Jupyter saves the file without importing Colab-only APIs. Save the notebook and UI source separately.

## Instructor preparation and recovery

Rehearse the local UI through its matching safe log, including a controlled stopped-service failure and recovery. For optional hosted calls, verify origin, assigned caller policy and provider readiness beforehand; missing settings or unavailable hosting mean skip the optional section. A fixture checks protocol/control behavior only. Check one cited claim after an actual provider-backed answer.

Module B supports the Sprint 1 Campus checkpoint runner plus four separate Live notebooks. This notebook covers the supplied LS13–LS14 plan; it adds no LS15–LS16 requirement.
