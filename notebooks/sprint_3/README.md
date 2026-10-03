# Sprint 3 — Campus and Live notebooks

There are exactly two notebooks for the sprint:

- [Campus source](sprint_3_observable_service.ipynb) is reused across C14–C19 · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/6126be6517df89230f20b17cf845f464b1457140/notebooks/sprint_3/sprint_3_observable_service.ipynb).
- [Live source](sprint_3_live_workshops.ipynb) is reused across LS09–LS12 · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/6126be6517df89230f20b17cf845f464b1457140/notebooks/sprint_3/sprint_3_live_workshops.ipynb).

Each has one setup and one final checkpoint export. Campus imports the secured Sprint 2 project when available. Live uses a separate workspace; apply a chosen improvement back to Campus explicitly.

Supported requests use the real OpenRouter stream, ChromaDB retrieval, and LangGraph orchestration. The observation exercise uses a synthetic marker locally, and the evaluation cell calls the preserved Module A evaluator. They are distinct computations with distinct evidence.

See [Colab setup and work-saving guidance](../../docs/colab-setup.md). The notebook links are pinned to the reviewed delivery; each setup cell installs the current Module B `main` branch.
