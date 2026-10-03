# Source provenance

- Module A reference inspected read-only: https://github.com/richhiey/ai-app-dev_Mod-A at `05cc0663701dc71dc53cc495a3e5bf853abd3a43`. Reused its source/notebook/test organization as a design precedent; no dependencies or entire Module A package were copied.
- FieldCare baseline imported from local `sprint-1-start`, revision `9ee0eeff4fa439e94a423c72eaebba1172586eb6`. All `app/`, `data/`, `fixtures/` and `tests/` files initially retain identical bytes.
- Module B schedule: user-supplied Campus and Live PDF exports; all 23 Campus and 16 live outcomes were previously verified against the stored curriculum snapshot. `curriculum.json` omits private local source paths.
- Request-trace visual: existing Masterschool bilingual SVG/PNG from B-C03, reused unchanged.
- Shared provider, runtime, retrieval, security, streaming, observability, evaluation, and checkpoint helpers are newly authored. Learners now trace routes and prompts directly in the service source; unused notebook source-writing and HTML-display wrappers were removed.

The original local FieldCare repository is retained unchanged for provenance. Module B notebook/service development is canonical here. Source checks do not claim a fresh hosted Colab run or provider response.
