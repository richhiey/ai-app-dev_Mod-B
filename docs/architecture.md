# Repository architecture

## Student-facing material

- `examples/fieldcare` is the editable FastAPI service and its synthetic data.
- `notebooks/sprint_1` contains one Campus notebook and one Live notebook. Their code cells make direct `TestClient` requests and show the returned status and body.
- `notebooks/sprint_2` and `notebooks/sprint_3` contain later-sprint notebooks. They keep service changes, requests, and observations in visible cells and import only reusable runtime/security/observability/evaluation mechanics.
- `examples/patterns` contains small worked source examples. Assessment reference implementations live in instructor-only material.

Students inspect and edit service code in their workspace. Helpers must not substitute printed source or a generated summary for the real computation being taught.

## Shared package

`src/module_b` supports the three authored sprints. `openrouter` provides provider setup; `runtime` manages the local service process; `security`, `observability`, and `evaluation` support explicit student operations; `retrieval` and `streaming` are called by FieldCare. The copied `_module_a` package preserves the Sprint 3 evaluation exercise. Small `workspace`, `checkpoints`, `edits`, and `data` utilities support safe checkpoint handling but are not imported directly by the six notebooks. See [helper responsibilities](helpers.md) for the map.

Sprint 1 does not depend on helper functions to display source or synthesize route observations. The Campus and Live notebooks call the supplied FastAPI app directly. Their `TestClient` calls execute in-process; they do not claim a TCP server or provider response.

## Authoring rule

Keep methods, paths, request bodies, schemas, prompts, route registration, and learner decisions in the visible service source or notebook cells. Reuse a helper only when it removes repeated setup or file mechanics without hiding the concept under instruction.
