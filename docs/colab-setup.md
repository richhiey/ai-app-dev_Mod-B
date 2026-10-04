# Use the Colab notebooks

There is one Campus notebook and one Live notebook per sprint. Keep a saved Drive copy of each notebook you use. Campus holds the cumulative student project; Live has a separate workshop workspace.

## Open and set up

Open the notebook from its sprint README and choose **File → Save a copy in Drive**. Every Campus setup clones the latest `main` into a fresh source folder and installs its dependencies with `requirements.lock`. There is no commit pin. A small repository helper closes earlier demo resources, refreshes stale imports, and prepares a fresh instructor workspace and document index. Your existing `PROJECT` files are retained.

Run setup and wait for **Ready**. Its three progress messages show downloading, workspace preparation and startup. Then run the section named by your lesson from top to bottom. Leave optional project checks off until you have made the lesson’s source changes.

A personal Drive copy is independent. To receive an updated setup, reopen the canonical link and copy its **Set up once** code into your personal notebook, preserving any `PROJECT` and `CHECKPOINT` choices. Rerun setup, then the demonstration sections. Save your observations separately from the source export.

If Chroma cannot open its database, rerun the current setup. It creates a fresh demo/database folder without deleting previous folders or your project. Database paths are resolved to absolute paths before Chroma opens them, so changing notebook folders cannot select another workspace’s cached relative-path database. For a learner project with filesystem problems, check its `.chroma` directory permissions. Setup failure does not count as a successful demonstration.

For Sprints 1–3, setup reads `OPENROUTER_API_KEY` from Colab Secrets or a hidden prompt. Keep the key out of cells, source files, outputs, screenshots, and notes. The first ChromaDB index build embeds the supplied service documents through OpenRouter. Each admitted supported request can also use provider quota for embeddings and generation. Schema rejection, authentication/rate-limit rejection, safety handling, and missing-context clarification stop before generation.

Sprint 4 is an API-client notebook: add the course-provided HTTPS service origin and caller credential to Colab Secrets as `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY`. It does not need or receive `OPENROUTER_API_KEY`; that secret stays on the FieldCare service. Add each value through Colab’s Secrets panel and enable notebook access. No local server or tunnel is started. The endpoint must be reachable from both the course Lovable project and Colab before this sprint can be delivered.

## Work with the service

Inspect and edit the real files in Colab’s Files panel. Notebook cells show the actual computations, HTTP requests, and results; they do not print source files as a substitute for opening them. Sprints 1–3 Campus and Live notebooks export one source/data checkpoint ZIP each. Sprint 4 exports one sanitized API-evidence JSON file; save the notebook separately because the export does not include notebook notes or the Lovable project.

Sprint 2 can import a Sprint 1 Campus source checkpoint. Sprint 3 can import a secured Sprint 2 checkpoint. Sprint 4’s Campus and Live notebooks keep independent request evidence and require the provisioned course endpoint. When a checkpoint is not supplied, the notebook uses the starter project; it does not claim prior student edits were carried forward. Live stays isolated from Campus. Apply a chosen Live change to Campus deliberately.

## What has and has not been verified

Local source inspection and static notebook checks do not establish a fresh hosted Colab run or current provider availability. Confirm those in Colab when preparing a delivery. A provider error is an observed error; do not replace it with authored answer text.

## Campus sprints 1–3: demo, project, and checkpoint

Each Campus notebook has a lesson-to-section map. Run one demonstration at a time: predict, execute, inspect, explain. `DEMO` holds supplied instructor source; `PROJECT` holds your own editable service. The default Run all path requires no completed learner route and does not complete an assessment. Optional project switches start `PROJECT/app/main.py`; the demonstrations start the supplied `app.campus_demo` factory (Sprint 1 uses TestClient).

Source files and `data/pipeline_design.json` are already in the repository. Edit your project files in the Files panel when the lesson asks you to apply a pattern. The notebook never writes Python code from strings. The server's operational log is an intentional Sprint 3 teaching artifact, not a source-generation step.

For a previous source ZIP, set `CHECKPOINT` and select a new `PROJECT` destination. Existing destinations are preserved, including on a mistaken restore. Clear `CHECKPOINT` to reuse a restored folder. Legacy app/data Campus ZIPs are supported; new exports carry a workspace marker. The final export saves only permitted project source/data/fixtures and optional `trace-record.md`; logs and runtime credentials are excluded. Save displayed safe records, predictions and observations in your personal notebook. An unchanged starter export is not assessment completion.

After a course update, a stale runtime may still contain old code or cached imports. Preserve your project export, disconnect and delete the runtime, then reopen the canonical notebook and run setup. Do not reset a folder that contains your work.
