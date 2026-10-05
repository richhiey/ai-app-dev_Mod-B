# Sprint 1 notebooks

- [Campus checkpoint](sprint_1_service_foundations.ipynb): run the local source export after completing the VS Code lessons and checkpoint implementation. It verifies the archive digest and records the supplied source revision, starts the submitted service, makes visible HTTP requests, and saves selected observations. It supplies no assessment implementation.
- [Live workshops](sprint_1_live_workshops.ipynb): separate instructor demonstrations. Preserve their existing workflow and saved copies; local Campus exports are not Live workspaces.

Campus uses VS Code from the start. Follow [local development](../../docs/local-development.md) and the [checkpoint transfer guide](../../docs/colab-setup.md). The checkpoint notebook clones main and restores into a fresh runtime copy; keep the original local project and ZIP. Contract checks do not call the provider. Set `CHECKPOINT_MODEL` to your approved local model setting. Optional indexing and generation use provider quota and a hidden key prompt; a skipped generated-answer check remains outstanding. The contract comparison includes 1000 accepted and 1001 rejected by v2.
