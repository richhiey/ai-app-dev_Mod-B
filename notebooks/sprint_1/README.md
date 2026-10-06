# Sprint 1 notebooks

- [Campus checkpoint](sprint_1_service_foundations.ipynb): run the local source export after completing the VS Code lessons and checkpoint implementation. It verifies the archive digest and records the supplied source revision, starts the submitted service, makes visible HTTP requests, and saves selected observations. It supplies no assessment implementation.
- [Live workshops](sprint_1_live_workshops.ipynb): learner and instructor Colab practice for application/service responsibilities, scaffold extension, contracts/versioning and an individual demonstration. No Campus project is required; local Campus exports are not Live workspaces.

Campus uses VS Code from the start. Follow [local development](../../docs/local-development.md) and the [checkpoint transfer guide](../../docs/colab-setup.md). The checkpoint notebook clones main and restores into a fresh runtime copy; keep the original local project and ZIP. Contract checks do not call the provider. Set `CHECKPOINT_MODEL` and `CHECKPOINT_MODEL_V2` to the approved V1 and V2 model settings used locally, even if they are equal. Optional indexing and generation use provider quota and a hidden key prompt; a skipped generated-answer check remains outstanding. The contract comparison includes 1000 accepted and 1001 rejected by v2.

## Using the Live notebook

Save an editable notebook copy and connect a Python CPU runtime. Run `setup` once, then follow the current session's section; do not use Run all, because the extension and model-choice cells require a learner attempt. The opening table gives all four exact session outcomes and navigation links.

| Session | Notebook sequence | Individual result |
|---|---|---|
| LS01 | `ls01-source` → `ls01-start` → `code-03` | A request/response and a map of route, input, output and possible model call |
| LS02 | `ls02-source` → `ls02-start` → `code-06`; edit, restart and repeat | Your added endpoint, named contract, prompt binding, registration and original-route check |
| LS03 | `ls03-source` → `ls03-model-before` → choose a model in `ls03-model-change` → `ls03-start` → `code-09` | Separate model/prompt comparisons, preserved old contract and migration condition |
| LS04 | Restore if needed, then `ls03-start` → `code-09` → `code-12` | Your extension demonstration, peer challenge and verified repair or confirming check |

Edit Python files in the printed `PROJECT/service/fieldcare` folder through Colab Files; the downloaded `REPO` and printed source outputs are not the working editor. Save source changes and rerun the session's start cell before retesting. The notebook describes file creation/upload, source inspection, expected responses and recovery for common failures. A Colab loopback URL is reached by the notebook's HTTP cells, not a laptop browser tab.

Provider preparation and calls are explicit opt-ins. Core validation and clarification checks require neither a provider key nor an index. A selected model or a `200` clarification does not prove generation. Keep provider-dependent observations pending when they have not run.

Run `save-checkpoint` and download the Live ZIP after every session. Save the notebook separately: the ZIP carries edited source and selected evidence, while notebook explanations and outputs remain in the notebook. It excludes credentials, indexes and raw logs. To resume, follow the notebook's fresh-runtime restore instructions using your own ZIP and recorded model choices; choose a new destination and review restored source before running it. See [Live handoff](../../docs/live-handoff.md).
