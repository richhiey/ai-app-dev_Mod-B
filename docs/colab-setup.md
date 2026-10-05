# Use the Sprint 1 checkpoint notebook

Campus coding happens in the local VS Code project. Use the [Sprint 1 notebook](../notebooks/sprint_1/sprint_1_service_foundations.ipynb) only for the service scaffold checkpoint at the end of Sprint 1.

Before opening Colab, complete the service work locally and export a source checkpoint from the course repository root. Record the repository base revision before export. The notebook also prints a SHA-256 fingerprint for the exact source ZIP you upload:

```text
git rev-parse HEAD
python -m tools.checkpoint artifacts/sprint-1-checkpoint.zip
```

Review the source archive for accidental credentials, then download it. Open the checkpoint notebook and choose **File → Save a copy in Drive**. Run setup to clone this repository's `main` branch and install its pinned dependencies. Upload the checkpoint ZIP when prompted. The notebook restores only allowed source files into a new folder; it does not create or modify your service code for you.

The assessment notebook runs your submitted service source in an isolated Colab process so it can make the checkpoint requests. It prints the source archive SHA-256, asks for the repository base revision, the POST /v2/diagnose route and matching request bodies, and your provider key through a hidden password prompt. Choose an approved model; the notebook sets OPENROUTER_MODEL for the temporary service. Sprint 1 does not yet add caller authentication. Never place a credential in a code cell, output, screenshot, notebook text, or source export. Colab cannot reach a server running on your laptop, so it runs the uploaded checkpoint source itself.

Supported generated requests and document-index preparation use provider quota. Invalid and missing-context requests may stop before model generation. Preserve the actual result, request ID, repository base revision, source archive SHA-256, and any provider error in your handoff. The notebook does not supply the endpoint or answer for you, and a `200` alone does not establish that your contract or generated answer is correct.
