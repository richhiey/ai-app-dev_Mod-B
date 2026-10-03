# Use the Colab notebooks

Each sprint has exactly one Campus notebook and one Live notebook. Keep one saved copy of each for that sprint. Campus is the cumulative student project; Live is a separate workshop workspace.

## Setup and model access

The first notebook cell loads this separate Module B repository and installs its pinned requirements. Use the repository revision selected for the course release. The current local revision has not been published, so the old GitHub notebook links and pins do not represent these changes yet.

Colab reads `OPENROUTER_API_KEY` from Secrets when present and otherwise uses a hidden prompt. Keep the key out of cells, source files, outputs, and notes. The first ChromaDB index build embeds the supplied service documents, and each admitted supported request can use OpenRouter quota for question embeddings and generation. Deterministic validation, authentication/rate-limit rejection, safety handling, and missing-context clarification stop before generation.

## Read and work with the service

Inspect source files in Colab’s Files panel and use the notebook cells to run the actual computations and HTTP requests. The cells keep request code and observed responses visible; they do not print source files as a substitute for opening them. Campus and Live each have one final checkpoint export. Save the notebook separately because its notes are not included in the ZIP.

Sprint 2 imports an optional Sprint 1 source checkpoint. Sprint 3 imports an optional secured Sprint 2 checkpoint. When a checkpoint is absent, the notebook labels the supplied starter as recovery and does not claim earlier student changes were carried over. Live remains isolated; apply a chosen change back to Campus deliberately.

## Verification boundary

Local source inspection and static notebook checks do not establish fresh Colab execution or provider availability. Those checks remain release steps after the current Module B source is published at an approved revision.
