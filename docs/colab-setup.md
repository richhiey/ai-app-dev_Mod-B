# Use the Colab notebooks

There is one Campus notebook and one Live notebook per sprint. Keep a saved Drive copy of each notebook you use. Campus holds the cumulative student project; Live has a separate workshop workspace.

## Open and set up

Open the notebook from its sprint README and choose **File → Save a copy in Drive**. The first setup cell clones the separate Module B repository from the current `main` branch with a shallow clone and installs it once using `requirements.lock`. It reuses that checkout for the rest of the runtime. The notebook source link is pinned to the reviewed delivery commit; the helper and example code it installs comes from `main`.

For Sprints 1–3, setup reads `OPENROUTER_API_KEY` from Colab Secrets or a hidden prompt. Keep the key out of cells, source files, outputs, screenshots, and notes. The first ChromaDB index build embeds the supplied service documents through OpenRouter. Each admitted supported request can also use provider quota for embeddings and generation. Schema rejection, authentication/rate-limit rejection, safety handling, and missing-context clarification stop before generation.

Sprint 4 is an API-client notebook: add the course-provided HTTPS service origin and caller credential to Colab Secrets as `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY`. It does not need or receive `OPENROUTER_API_KEY`; that secret stays on the FieldCare service. Add each value through Colab’s Secrets panel and enable notebook access. No local server or tunnel is started. The endpoint must be reachable from both the course Lovable project and Colab before this sprint can be delivered.

## Work with the service

Inspect and edit the real files in Colab’s Files panel. Notebook cells show the actual computations, HTTP requests, and results; they do not print source files as a substitute for opening them. Sprints 1–3 Campus and Live notebooks export one source/data checkpoint ZIP each. Sprint 4 exports one sanitized API-evidence JSON file; save the notebook separately because the export does not include notebook notes or the Lovable project.

Sprint 2 can import a Sprint 1 Campus source checkpoint. Sprint 3 can import a secured Sprint 2 checkpoint. Sprint 4’s Campus and Live notebooks keep independent request evidence and require the provisioned course endpoint. When a checkpoint is not supplied, the notebook uses the starter project; it does not claim prior student edits were carried forward. Live stays isolated from Campus. Apply a chosen Live change to Campus deliberately.

## What has and has not been verified

Local source inspection and static notebook checks do not establish a fresh hosted Colab run or current provider availability. Confirm those in Colab when preparing a delivery. A provider error is an observed error; do not replace it with authored answer text.
