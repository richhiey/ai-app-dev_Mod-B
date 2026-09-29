# Facilitator reference — dispatch handover

Keep this separate from the independent learner task. `handover_routes.py` contains one acceptable prompt and the supplied handler pattern. `main.py` preserves the baseline application and adds only the router import and registration. To prepare a reference workspace, use `prepare_example` in a fresh destination, then copy these two files to its `app/` directory.

The new handler reuses `run_diagnosis`, `DiagnosticRequest`, `DiagnosticResponse`, `MODEL_NAME` and the original safe provider-error response. It changes audience and prompt, not evidence or validation. The three-bullet format is an example; an equally concise alternative can meet the brief.

Run the demo HTTP checks and `inspect_route_bindings` for `/v1/diagnose: app.routes` and `/v1/dispatch-handover: app.handover_routes`. `python scripts/verify_notebooks.py` executes the untouched starters. The author workspace's private reference runner passes cell edits through `--reference-config` to execute completed variants in memory. Learner notebook files stay blank and output-free.

Generated wording is not supplied or invented. A course-approved OpenRouter model and provider access are required for the notebook's live comparison. Automated checks use no external provider, and cannot establish output quality. Reference tests also cover unsupported context and restoration of a completed source checkpoint.
