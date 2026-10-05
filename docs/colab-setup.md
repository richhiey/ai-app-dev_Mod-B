# Use the Sprint 1 checkpoint notebook

Campus coding happens in your local VS Code project. Use the [Sprint 1 checkpoint in Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_service_foundations.ipynb) after completing the Campus checkpoint brief. It runs your exported service and records observations; your implementation and reasoning remain yours.

## Export your completed source

From the FieldCare repository root, run:

```text
python -m tools.checkpoint export artifacts/sprint-1-checkpoint.zip
git rev-parse HEAD
python -c "import hashlib; from pathlib import Path; print(hashlib.sha256(Path('artifacts/sprint-1-checkpoint.zip').read_bytes()).hexdigest())"
```

Choose a new archive name for each export, and use that same name in the hash command. Existing archives are preserved. The Git revision identifies the base repository; the SHA-256 fingerprint identifies the exact exported bytes, including uncommitted changes.

The ZIP contains your service, clients, supplied synthetic data, selected evidence, and dependency metadata. It excludes `.env`, indexes, and raw logs. Review the included source and notes for accidentally pasted credentials before uploading. This archive is an overlay for the course clone, not a standalone application.

## Run the checkpoint in Colab

1. Open the notebook and choose **File → Save a copy in Drive**. Upload the ZIP through Colab's **Files** panel.
2. In setup, set `ARCHIVE` to the uploaded path and enter the locally recorded `SOURCE_REVISION` and `ARCHIVE_SHA256`. Set `CHECKPOINT_MODEL` to the same approved `OPENROUTER_MODEL` used locally. The ZIP correctly excludes your private `.env`, so model configuration must be selected explicitly.
3. Run setup. It clones current `main`, installs the locked dependencies, checks the digest and dependency metadata, and restores allowed files into that fresh runtime clone. It prints the runner revision separately. Your laptop source is untouched.
4. Predict and run the contract observations. They test both versioned paths, including accepted `1000`-character and rejected `1001`-character v2 inputs, without calling the provider. Read actual results against the brief; the notebook is not an automatic grader.
5. When ready to use provider quota, set `RUN_GENERATION = True`. Enter the provider key only in the hidden prompt. Index preparation and supported generation use quota; compare an actual generated claim with its cited document. If access is unavailable, keep the generated-answer evidence marked as outstanding.
6. Save your predictions and interpretation in your Drive copy. Review and download the evidence JSON from the Files panel, and retain the original source ZIP.

Colab starts its own temporary HTTP server from your uploaded source; it cannot reach your laptop's `localhost`. Keep source edits in VS Code. To repair a result, edit locally, export a new ZIP and digest, and rerun setup. You do not need to copy code back from Colab.

## Recover without losing work

| Observation | Next check |
|---|---|
| File or digest mismatch | Compare the uploaded path with the locally recorded ZIP and SHA-256. |
| Dependency metadata mismatch | Compare your source revision with the runner revision; resolve the course dependency difference before retrying. Keep your original source. |
| `404` or unexpected validation | Inspect the registered route and model in your local project, then export a corrected version. |
| Provider or index failure | Preserve the actual failure and inspect configuration, quota, connectivity and storage. Do not substitute a sample answer. |
| Evidence file already exists | Keep the earlier file and choose a new name for the new observation set. |

Never include a key in a saved cell, output, screenshot, or source export. A working process and a valid response shape are useful checks; neither establishes answer quality.

[Return to local setup](local-development.md)
