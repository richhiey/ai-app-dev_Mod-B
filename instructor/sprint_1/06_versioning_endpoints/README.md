# Endpoint versioning — facilitator reference

This is the separate solved reference for the formative Campus support package. It does not contain the reserved supervisor assessment endpoint.

## Starting state and setup

Use the current shared source with `sprint_1_service_foundations.ipynb`. Section 5 continues the guided `lab` and applies the dispatch pilot to the cumulative `project`. Complete the handover first and rerun its check after changes. `version-prepare` records the incoming baseline only when that evidence is current; it never inserts a handover recovery answer.

A marked existing application workspace is reused with edits intact. The saved baseline retains inherited source for exact comparison; a fresh reset needs a new destination. Review source before sharing a checkpoint.

## Tool steps and expected observations

1. Run setup and inspect `app/routes.py` and the displayed `app/diagnose_v2_routes.py`. They use `OPENROUTER_MODEL` and `FIELDCARE_DIAGNOSE_V2_MODEL` respectively. Both retain `DiagnosticRequest`/`DiagnosticResponse`.
2. Run actual local HTTP against both routes: each returns `200`, `mode=demo`, and the four existing output fields.
3. Inspect both rounds from `inspect_version_bindings`. Synthetic model identifiers are injected before import; mocked provider requests reveal their actual binding. Changing only the new module's constants leaves the old prompt/model unchanged. This is not generated-answer evidence.
4. Change the new prompt's two-bullet instruction to three bullets, restart the local process and compare the fresh report. Only the new prompt hash changes; both HTTP operations still succeed. Model settings are read at import time.
5. Apply `deprecated=True` to the old decorator. Only the old operation has that OpenAPI flag; both still return `200`. The synthetic tablet record does not justify removal. Restore exactly this metadata edit using the guarded writer.
6. Let learners complete the dispatch integration before opening the two solved files here. The solution uses `HandoverV2Request` with max `600`, retains nonempty/trimmed input, optional bounded equipment ID and forbidden extras, and preserves `DiagnosticResponse`.
7. Copy the solved schema and route only into a separate reference workspace, then append the visible registration:

```python
from app.handover_v2_routes import router as handover_v2_router
app.include_router(handover_v2_router)
```

8. Run selected requests and inspect the evidence: accepted input `200` on both; a supported `601`-character question `200` on old, `422` on new; missing optional context yields clarification. The helper also checks exactly `600`, malformed input/output and full input-contract equivalence except the allowed limit/name difference.
9. Confirm inherited files are byte-for-byte unchanged. Source fingerprints taken during checks must still match at save; editing afterward keeps the record pending. Export source and timestamped evidence.

## Solved and pending states

`handover_v2_schemas.py` and `handover_v2_routes.py` are the solved reduced-support source. Generated real-model wording has not been evaluated. Untouched notebooks keep independent tasks pending. Completed reference variants must pass the local structural checks; written explanations, generated-answer review and instructor grading remain separate readiness states.

The private author runner supplies completed formative and assessment decisions to the public verifier, which runs both variants twice. The reference completes the cumulative handover before its pilot integration. Untouched prerequisite tasks stay pending. Both variants retain their stage files across reruns.

## Failure notes

- Wrong path or missing registration: verify the decorator and one `include_router` call; do not treat a module existing on disk as a callable endpoint.
- Shared model environment or wrong prompt argument: inspect the binding report's failed row. The helper changes only new settings to expose accidental coupling.
- Model setting appears stale: restart the process after editing source or environment; these constants are imported once.
- Contract report fails: compare every original constraint, not just max length. Losing trimming, nonempty checks, bounded optional equipment ID or `extra=forbid` violates the brief.
- Existing checkpoint fails: recover environment/import errors, or complete the earlier extension. Do not mark an incomplete inherited route as completed work.
- Guard refuses a write: preserve the changed source; use a new workspace or a reviewed expected text. Do not reset learner work.
- Source changed after checks: rerun observations before saving. An old pass does not validate the exported revision.
- Demo wording stays identical: expected. Do not infer prompt quality or model capability from fixed fixtures.

## Debrief lens

Ask learners to point to the original caller's preserved agreement, the pilot's new limit and its independently selected prompt/model. Different URLs alone do not prove independence. The synthetic scheduling client still accepts `900`-character requests on `/v1`; removal is unjustified until migration and the retirement window are verified. A deprecation marker is documentation, not a migration engine.

## Human capture/release checks

Hosted Colab was not opened. Human capture and release review remain pending. Suggested captures: paired actual HTTP outputs; two rounds of binding evidence; `deprecated` flags with both calls succeeding; the learner's integrated old/new contract comparison. Capture actual results rather than manufacturing UI screenshots. The parent lesson's authoring note owns the final release gate.
