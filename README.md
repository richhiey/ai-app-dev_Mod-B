# AI App Development — Module B

This repository contains the shared examples and Colab notebooks for Module B. Sprint 1 teaches the basic FastAPI service scaffold through one Campus notebook and one Live notebook. Later sprint materials are organized under their matching folders.

## Sprint 1 notebooks

- [Campus source](notebooks/sprint_1/sprint_1_service_foundations.ipynb) · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_service_foundations.ipynb) follows actual requests through the supplied FastAPI service, then guides route extension, contract validation, endpoint versioning, and an independent endpoint assessment.
- [Live source](notebooks/sprint_1/sprint_1_live_workshops.ipynb) · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_live_workshops.ipynb) contains four focused request/response workshops.
- [Colab setup and saving work](docs/colab-setup.md) explains the single setup step and one final source/data checkpoint export.

## Later sprint notebooks

- Sprint 2: [Campus Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_2/sprint_2_secure_service.ipynb) · [Live Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_2/sprint_2_live_workshops.ipynb) · [Sources](notebooks/sprint_2/README.md)
- Sprint 3: [Campus Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_observable_service.ipynb) · [Live Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_live_workshops.ipynb) · [Sources](notebooks/sprint_3/README.md)
- Sprint 4: [Campus Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_4/sprint_4_fieldcare_campus.ipynb) · [Live Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_4/sprint_4_fieldcare_live.ipynb) · [Sources](notebooks/sprint_4/README.md)

Sprints 1–3 run the actual FastAPI application in Colab. Supported requests use the Module A stack: OpenRouter embeddings index the current service documents in ChromaDB, LangGraph coordinates retrieval and generation, and OpenRouter supplies the model response. Those project notebooks load `OPENROUTER_API_KEY` from Secrets or a hidden prompt; model wording varies.

Sprint 4 notebooks call the course-provisioned reachable service as a separate HTTP caller. They use Colab Secrets for `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY`, not the OpenRouter key. They inspect real API/stream responses; they do not impersonate the Lovable UI. Validate the UI path from the actual Lovable preview and correlated service request ID. Provider, validation, authentication, quota and clarification outcomes are reported as observed.

## Repository layout

```text
src/module_b/          Shared mechanics used by later sprint notebooks
examples/fieldcare/    Editable FastAPI service and synthetic data
examples/patterns/     Worked source examples
notebooks/sprint_1/    Sprint 1 Campus and Live notebooks
notebooks/sprint_2/    Sprint 2 Campus and Live notebooks
notebooks/sprint_3/    Sprint 3 Campus and Live notebooks
notebooks/sprint_4/    Sprint 4 Campus and Live API integration notebooks
instructor/            Facilitator reference material
scripts/               Notebook and source maintenance utilities
```

Shared code supports provider access, process lifecycle, security, safe checkpoint handling, observability, and reuse of the Module A evaluator. Route behavior, schemas, prompts, provider settings, and caller requests remain in the application or notebook cells where learners can inspect them. See [which lesson uses each helper](docs/helpers.md).

## Local development

Use Python 3.11+ on Linux or macOS. Install the package and development dependencies from `pyproject.toml`; use the notebook guidance when opening a notebook locally. Structural changes to notebooks should retain readable markdown, actual executable examples, and a single setup/export path.

Sprint 1–3 source links open the reviewed delivery revision; those setup cells shallow-clone the current Module B `main` branch for shared code. Sprint 4 uses one setup cell for the course-provisioned API secrets and Colab’s existing `requests` package. A local static check does not claim that a new hosted Colab run, live provider response, or instructor rehearsal has taken place.
