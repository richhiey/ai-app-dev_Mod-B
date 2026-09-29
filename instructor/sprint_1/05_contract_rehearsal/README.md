# Contract observations — facilitator support

Use section 4 of `notebooks/sprint_1/sprint_1_service_foundations.ipynb`. The worked example declares a 300-character technician input in `lab`, retains optional bounded equipment context, registers the supplied route, and sends actual local HTTP. The separate contract probe observes validation before and after application work. Keep the route in `lab`; no cleanup cell or additional notebook is required.

The accepted, at-limit, over-limit, missing-question, missing-context and deliberately malformed-output probe cases should return `200`, `200`, `422`, `422`, `200`, `500`, with adapter counts `1`, `1`, `0`, `0`, `0`, `1`. The malformed result is injected only in the isolated probe after application work. A schema-valid unsupported answer does not establish factual correctness.

The independent application is the 600-character dispatch pilot in section 5 of the same notebook. Its facilitator reference lives in `../06_versioning_endpoints/`. It preserves the original 2000-character agreement in the cumulative student project. The 240-character schema file in this directory is a legacy helper-test fixture, not a student task or a second notebook requirement.

For failures, inspect router registration on `404`, the request model and declared maximum on boundary mismatches, and the selected supported equipment/question when a request clarifies. Preserve student edits before repairs. Debrief which validation boundary ran, whether adapter work had already happened, and why a valid response shape cannot prove its claims.

Before publication, rehearse the final sprint notebook in hosted Colab and complete the human release pass. Any selected UI capture must show actual results; no fabricated screenshot is supplied here.
