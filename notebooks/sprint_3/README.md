# Sprint 3 — Campus and Live notebooks

There are exactly two notebooks for the sprint:

- [Campus source](sprint_3_observable_service.ipynb) is reused across C14–C19 · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_observable_service.ipynb).
- [Live source](sprint_3_live_workshops.ipynb) is reused across LS09–LS12 · [Open in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_live_workshops.ipynb).

Each has one setup and one final checkpoint export. Campus imports the secured Sprint 2 project when available. Live uses a separate workspace; apply a chosen improvement back to Campus explicitly.

Supported requests use the real OpenRouter stream, ChromaDB retrieval, and LangGraph orchestration. The observation exercise uses a synthetic marker locally, and the evaluation cell calls the preserved Module A evaluator. They are distinct computations with distinct evidence.

See [Colab setup and work-saving guidance](../../docs/colab-setup.md). The same canonical links load the current `main` notebooks; setup installs the current `main` source.

Campus uses a supplied `DEMO` and a separate learner `PROJECT`. Run the default demonstrations without first completing exercises. Apply source changes in `PROJECT` when the lesson asks; enable the optional project runner to test your work. No cell generates Python source. Save one Drive copy for notes and export your project at the end. See the notebook’s lesson map for exact section names.
