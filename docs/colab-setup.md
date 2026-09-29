# Run the sprint notebooks from GitHub

There are two Colab notebooks per sprint: one Campus notebook reused across Campus lessons, and one Live notebook reused across live sessions. The shared course code lives in the same GitHub repository. No supporting source ZIP is needed.

## Shared source and your own work

The six published notebooks already contain the repository URL and a fixed, reviewed helper revision. Leave those setup values unchanged. Setup fetches the course helpers and synthetic service automatically; you only upload a checkpoint when restoring your own work or carrying it forward.

Save a Campus copy and a Live copy once for each sprint. Continue in those saved copies throughout the sprint. A lesson link opens the original template, so use your saved copy when you already have work to keep.

## Colab

1. Open the sprint notebook from the published GitHub repository in Colab, save a personal copy to Drive and select a Python CPU runtime.
2. Run its single setup section. It clones the configured repository, checks out the fixed release revision and installs the shared package with `requirements.lock`. There is no course-source upload prompt.
3. In Campus, Sprint 2 imports your Sprint 1 checkpoint through `SPRINT1_CHECKPOINT`; Sprint 3 imports your Sprint 2 checkpoint through `SPRINT2_CHECKPOINT`. In Live, use `CAMPUS_CHECKPOINT` for the starting state named by the session. Upload your ZIP through Colab’s Files panel, copy its path and set the corresponding field. These files contain your service edits and evidence. The explicitly labelled recovery option is available when your checkpoint is unavailable.
4. Follow the worked examples and complete the independent source/decision cells. Untouched tasks remain pending.
5. Save the notebook and download the one final student checkpoint ZIP printed by its Save section. GitHub provides the course code; it does not automatically save edits made in your temporary runtime.

To resume a notebook, upload its previously exported checkpoint and set `RESUME_ZIP`. For Sprint 2, also set `RESUME_STAGE` to the stage printed at export. Keep earlier Campus checkpoints for demonstrations that need an earlier starting state. Start with a fresh runtime or a deliberately new `RUN_NAME`; existing workspaces are preserved and will not be replaced just because you change a checkpoint path.

Existing checkouts and student stage directories are reused without pulling, resetting or overwriting files. To switch course revisions, preserve your work and use a fresh runtime. Setup clones into a temporary directory first, so a failed download does not leave a partially installed destination.

## Local Jupyter and verification

Clone the course repository and open its notebook in local Jupyter with Python 3.11+ on Linux/macOS. Alternatively set `MODULE_B_REPO` to an existing checkout in the Jupyter process environment. Setup discovers the local source and installs it into the active kernel.

`python scripts/verify_notebooks.py` creates a fresh isolated environment and runs all six notebooks twice. The private author runner additionally checks completed reference work and the cumulative sprint handoff. Reports are JSON; no additional notebooks are created. Clone/checkout behavior can be tested with a disposable local Git fixture without claiming access to an unpublished GitHub repository.

Earlier review revisions of all six notebooks completed hosted Colab starter runs. Further browser checks are skipped at the author’s request; final restore changes are checked locally. [The run record](hosted-colab-verification.json) identifies the exact revisions and remaining review checks. Demonstrations need no provider account. Required Sprint 1 generated-answer comparisons remain pending until you deliberately enable them with approved model access.
