# Run the sprint notebooks from GitHub

There are two Colab notebooks per sprint: one Campus notebook reused across Campus lessons, and one Live notebook reused across live sessions. The shared course code lives in the same GitHub repository. No supporting source ZIP is needed.

## Course release configuration

Before publishing the notebooks, the author sets `GITHUB_REPO` to the actual HTTPS GitHub clone URL and `GITHUB_REF` to a full commit SHA or `refs/tags/<release-tag>` in all three setup cells. The selected revision must contain `src/module_b`, `examples`, and `requirements.lock` at its root. Use the same reviewed revision for all notebooks. Environment overrides `MODULE_B_REPO_URL` and `MODULE_B_REPO_REF` support author verification.

These values remain empty in the local authoring copy because the repository has no configured remote yet. Existing local checkouts still work; a fresh cloud runtime explains the missing publication configuration. No repository has been created or published as part of this change.

## Colab

1. Open the sprint notebook from the published GitHub repository in Colab, save a personal copy to Drive and select a Python CPU runtime.
2. Run its single setup section. It clones the configured repository, checks out the fixed release revision and installs the shared package with `requirements.lock`. There is no course-source upload prompt.
3. For Sprint 2, upload your personal Sprint 1 checkpoint ZIP through Colab's Files panel and set `SPRINT1_CHECKPOINT` to its `/content/...zip` path. This ZIP contains your own service edits and evidence, not the shared course code. The labelled recovery option is available if that checkpoint is unavailable.
4. Follow the worked examples and complete the independent source/decision cells. Untouched tasks remain pending.
5. Save the notebook and download the one final student checkpoint ZIP printed by its Save section. GitHub provides the course code; it does not automatically save edits made in your temporary runtime.

To resume Sprint 1, upload your own checkpoint and set `RESUME_ZIP`. To resume Sprint 2, also set `RESUME_STAGE` to the stage printed at export, and retain the Sprint 1 checkpoint for earlier demonstrations.

Existing checkouts and student stage directories are reused without pulling, resetting or overwriting files. To switch course revisions, preserve your work and use a fresh runtime. Setup clones into a temporary directory first, so a failed download does not leave a partially installed destination.

## Local Jupyter and verification

Clone the course repository and open its notebook in local Jupyter with Python 3.11+ on Linux/macOS. Alternatively set `MODULE_B_REPO` to an existing checkout in the Jupyter process environment. Setup discovers the local source and installs it into the active kernel.

`python scripts/verify_notebooks.py` creates a fresh isolated environment and runs all six notebooks twice. The private author runner additionally checks completed reference work and the cumulative sprint handoff. Reports are JSON; no additional notebooks are created. Clone/checkout behavior can be tested with a disposable local Git fixture without claiming access to an unpublished GitHub repository.

An actual hosted Colab session and remote GitHub release have not been tested yet. No model is required for demonstrations; required Sprint 1 generated-answer comparisons remain pending without provider access.
