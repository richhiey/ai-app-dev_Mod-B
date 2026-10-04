# Use the course Colabs

Sprint 1 Campus uses Colab to explore service foundations. Campus Sprints 2–3 use [VS Code and local terminals](local-development.md). Live sessions have separate instructor notebooks. Sprint 4 uses API-client notebooks for a course-hosted service.

## Sprint 1 Campus

Open the [Campus notebook](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_service_foundations.ipynb) and choose **File → Save a copy in Drive**. Setup clones repository `main`, installs its dependencies and creates a fresh instructor workspace. Run the section named in your lesson from top to bottom.

`DEMO` contains the instructor example; `PROJECT` contains your editable service. Use Colab's Files panel to inspect and edit actual project files. The notebook's optional project runner tests your changes. Save notes in your personal notebook and use the final source/data export to retain your project. An unchanged starter is not a completed assessment.

Setup reads `OPENROUTER_API_KEY` from Colab Secrets or a hidden prompt. The initial document embeddings and supported generated answers use provider quota. Keep the key out of cells, source, screenshots and notes. Invalid or missing-context requests stop before generation.

To receive an updated setup in an existing personal copy, reopen the canonical notebook and copy its setup cell, preserving your project/checkpoint choices. Save a source export before replacing a runtime. Never delete a project folder to recover a demonstration.

For an earlier source ZIP, set `CHECKPOINT` and choose a new `PROJECT` directory. Clear `CHECKPOINT` after restoring when you want to reuse that directory. The export excludes runtime credentials and databases; inspect permitted source and notes for accidentally pasted secrets before sharing.

## Live sessions

Use the sprint's Live notebook and named workshop section. Keep its Drive copy separate. For Sprints 2–3, follow the [local project handoff](live-handoff.md): local Campus ZIPs are not Live checkpoints, and Colab's localhost is not your computer.

## Sprint 4 API clients

Obtain the course service URL and caller credential from your instructor. Add them as `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY` in Colab Secrets and enable notebook access. The provider key stays on the service. These notebooks make requests to an existing HTTPS endpoint; they do not start a local server. Save the sanitized API-evidence export and your notebook separately.

## Recovery

Keep the actual failing operation and message. A healthy process, an open document index, and a successful provider call are different checks. If Sprint 1's demo database cannot open, current setup creates a new demo directory without replacing your project. For your own project, inspect the database path and permissions. Preserve the failure if it repeats; it is not a successful demonstration.
