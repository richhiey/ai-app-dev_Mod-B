# AI App Development — Module B

Two Colab notebooks per sprint: one Campus notebook for all Campus lessons and one Live notebook for all four live sessions. Six notebooks cover Sprints 1–3, using the same shared Python helpers and FieldCare service. Keep a personal copy of each notebook and use its table of contents throughout the sprint.

## Start here

- [Sprint 1 Campus — service foundations](notebooks/sprint_1/sprint_1_service_foundations.ipynb): HTTP, FastAPI tracing, prompts, contracts, independent versions and the supervisor assessment.
- [Sprint 2 Campus — secure the service](notebooks/sprint_2/sprint_2_secure_service.ipynb): authentication, secret boundaries, rate limits, independent practice and the weekend assessment.
- [Sprint 3 Campus — observable service](notebooks/sprint_3/sprint_3_observable_service.ipynb): streaming, safe logging, minimization and original Module A evaluation.
- [Sprint 1 Live — four workshops](notebooks/sprint_1/sprint_1_live_workshops.ipynb).
- [Sprint 2 Live — four workshops](notebooks/sprint_2/sprint_2_live_workshops.ipynb).
- [Sprint 3 Live — four workshops](notebooks/sprint_3/sprint_3_live_workshops.ipynb).
- [Colab/local setup and saving progress](docs/colab-setup.md).
- [Curriculum](docs/curriculum.md), [helper API](docs/helpers.md), [control policy](docs/sprint-2-control-policy.md) and [verification evidence](docs/local-verification.json).

Each notebook has one setup, a table of contents, complete worked examples, blank independent decisions, checks, troubleshooting and one final export. Run all executes demonstrations but leaves untouched exercises pending. Source, evidence and notebook notes are separate: save the notebook and download its one final checkpoint ZIP. The Campus notebook owns the cumulative project: Sprint 2 accepts its Sprint 1 checkpoint, and Sprint 3 accepts its Sprint 2 checkpoint. Live notebooks import into separate workspaces and export formative evidence. Apply chosen Live changes back to Campus deliberately and rerun its checks before the next Campus export.

## Repository layout

```text
src/module_b/          Shared setup, process, observation, preservation and export helpers
examples/fieldcare/    Editable teaching service, synthetic data, fixtures and tests
examples/patterns/     Analogous worked source patterns
notebooks/sprint_1/    One Campus and one Live Colab notebook
notebooks/sprint_2/    One Campus and one Live Colab notebook
notebooks/sprint_3/    One Campus and one Live Colab notebook
notebooks/sprint_4/    Future Campus/Live notebook plan
instructor/           Formative reference source only
scripts/              Fresh-environment execution and packaging
work/                 Ignored student stages; preparation preserves edits
artifacts/            Student checkpoint exports; no course source ZIP or executed notebooks
```

## Local review

Use Python 3.11+ on Linux/macOS. Colab uses Linux. The owned-server runtime uses POSIX sockets; native Windows execution is not supported.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]' -c requirements.lock
python -m pytest
python scripts/verify_notebooks.py
```

The verifier creates a fresh isolated checkout/environment, runs shared and service tests, and executes all six untouched notebooks twice in new kernels while retaining stage files between runs. It saves JSON evidence, never extra notebooks. `--reference-config` accepts private cell edits for author review; the author's combined reference runner lives outside this repository and tests completed Sprint 1-to-2-to-3 transfer. Private assessment implementations are kept outside the learner repository.

## Shared helpers, visible learning

Routes, schemas, prompt/model choices, caller mappings, guard registration, policies and HTTP requests remain visible in cells or in the student's editable source. Helpers own repeated mechanics: process lifecycle, files, isolated probes, source/data fingerprints and checkpoint export.

Actual loopback HTTP, separate in-process observations, mocked provider bindings and actual real-provider output are labelled distinctly. Sprint 1 generated-answer comparison is required for C04/C07 completion but off by default and requests a key through hidden input only when explicitly enabled. Sprint 2 requires no provider calls. Structural checks never establish generated-answer quality or award a grade.

## Preserve student work

Worked writes refuse unexpected changes. Student dictionaries apply the source the student explicitly supplies; keep them synchronized with file-editor changes. Registration blocks append once. Each stage records its incoming state once and checks inherited source/data/route preservation. Evidence freshness includes current source and chosen requests/experiments. Existing stage directories are retained; change `RUN_NAME` only for a deliberate new attempt.

The exporter includes allowed source/data/fixtures and excludes environment files. Review outgoing files: a secret pasted into allowed Python or JSON would still be exported. A notebook saved to Drive does not preserve edited service files; download the final ZIP too.

## Version and release status

Current local source version is `0.8.1`. Earlier Git checkpoints remain historical; the final notebooks load shared source from a configured GitHub release tag or full commit SHA. The six Colab notebooks load reviewed helpers from the pinned commit. This repository is published for review. Hosted Colab checks and human review are tracked separately in the review index. The fresh local execution report records tested behavior; hosted Colab and human walkthrough review remain separate checks.

The original FieldCare repository remains historical provenance; see [provenance](docs/provenance.md). New work uses this module repository. Future capabilities, including companion-UI integration, remain governed by the exact curriculum and their actual dependencies.
