# Sprint 3 — Campus and Live notebooks

There are exactly two notebooks for the sprint:

- [Campus source](sprint_3_observable_service.ipynb) is reused across C14–C19.
- [Live source](sprint_3_live_workshops.ipynb) is reused across LS09–LS12.

Each has one setup and one final checkpoint export. Campus imports the secured Sprint 2 project when available. Live uses a separate workspace; apply a chosen improvement back to Campus explicitly.

Supported requests use the real OpenRouter stream, ChromaDB retrieval, and LangGraph orchestration. The observation exercise uses a synthetic marker locally, and the evaluation cell calls the preserved Module A evaluator. They are distinct computations with distinct evidence.

The source notebooks are ready for local review. Add Colab launch links only after the Module B repository has a reviewed release revision containing these files. See [setup](../../docs/colab-setup.md).
