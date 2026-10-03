# Repository architecture

## Student-facing material

- `examples/fieldcare` is the editable FastAPI service and its synthetic data.
- `notebooks/sprint_1` contains one Campus notebook and one Live notebook. Their code cells make direct `TestClient` requests and show the returned status and body.
- `notebooks/sprint_2` and `notebooks/sprint_3` contain later-sprint notebooks. They use shared utilities for repeated setup, workspace, and checkpoint mechanics.
- `examples/patterns` contains small worked source examples. Assessment reference implementations live in instructor-only material.

Students inspect and edit service code in their workspace. Notebook helpers may support file handling and repeated operations, but must not substitute printed source or a generated summary for the real computation being taught.

## Shared package

`src/module_b` supports multiple sprints. `workspace`, `runtime`, `data`, and `edits` provide reusable file/process mechanics. The notebook, security, secret-workshop, streaming, observability, and evaluation modules serve active Sprint 2/3 workflows. The copied `_module_a` package supports the Sprint 3 evaluation exercise. See [helper responsibilities](helpers.md) for active use.

Sprint 1 does not depend on helper functions to display source or synthesize route observations. The Campus and Live notebooks call the supplied FastAPI app directly. Their `TestClient` calls execute in-process; they do not claim a TCP server or provider response.

## Authoring rule

Keep methods, paths, request bodies, schemas, prompts, route registration, and learner decisions in the visible service source or notebook cells. Reuse a helper only when it removes repeated setup or file mechanics without hiding the concept under instruction.
