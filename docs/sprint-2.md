# Sprint 2: secure your service

Nice work getting FieldCare ready for real callers. HelioDesk is now opening it to a partner application, and you’ll decide who the service recognizes and how much work each caller may request. Keep your existing routes and contracts as you add these protections.

Start with the [local development guide](local-development.md). The Campus lessons explain each boundary; this page keeps the source locations and commands together.

## Add authentication

Read `service/fieldcare/security_settings.py`. It maps public caller labels to environment-variable names; `POLICY = None` means authentication without a limiter.

In `service/fieldcare/main.py`, add the following **after all router registrations**. Do this once; do not attach a second guard if your imported service already has one.

```python
from module_b.security import SecurityMiddleware, protected_post_paths
from fieldcare.security_settings import CALLER_ENV, POLICY

app.add_middleware(
    SecurityMiddleware,
    caller_env=CALLER_ENV,
    protected_paths=protected_post_paths(app),
    policy=POLICY,
)
```

The route inventory includes registered static POST paths. A new router added after the inventory is collected would be missed. The supplied pattern does not cover mounted applications or dynamic path parameters.

Restart the server in terminal A. In terminal B, edit and run `clients/request.py` once per experiment:

| Caller and body | Expected result |
|---|---|
| `CALLER = None`, valid body without equipment | `401` |
| `CALLER = "wrong"`, same body | `401` |
| `CALLER = "dispatch"`, `BODY = {}` | `422` |
| `CALLER = "dispatch"`, valid body without equipment | `200`, `needs_clarification` |

The first two stop at authentication. The third reaches validation. The fourth reaches deterministic application logic. The final two demonstrate that a key does not make input valid or evidence sufficient.

Prepare the index using the local guide, then send a supported question. Record an actual answer and inspect its citations. This is a separate provider-backed check.

## Apply a caller-wide allowance

The supplied type is `module_b.security.LimitPolicy`. Its arguments are `allowance` and `window_seconds`. Set `POLICY` in your application's settings file during the practice. Restart once to load it, then keep that process running through the sequence.

- Guided reasoning uses **2 admitted attempts per 60 seconds**.
- Independent practice uses **3 per 60 seconds**.
- The assessment brief uses **4 per 60 seconds** and a new caller mapping.

One bucket belongs to an authenticated caller across all protected paths. Admitted malformed bodies, clarification requests, and provider failures consume an attempt. `401` and `429` do not consume an additional attempt. A restart clears all buckets; it is not evidence of time-based renewal.

## Build your request experiment

`clients/burst.py` has an empty `REQUESTS` list. Each row contains `label`, `caller`, `path`, and `body`. Here is the shape of one row, not a completed experiment:

```python
{"label": "my first probe", "caller": "dispatch", "path": "/v1/diagnose", "body": {}}
```

Write your predictions in `evidence/observations.md` before executing:

```text
python -m clients.burst
```

Use a second caller and a second route from your own project. Repeated deterministic requests isolate the limiter without buying model calls. Demonstrate renewal by waiting at least the returned `Retry-After` while the same server remains running, then retrying. Treat a restart as a new experiment.

For the assessment's new caller labels, update both `service/fieldcare/security_settings.py` and the mapping in `clients/common.py`; put new values only in `.env`. You can rename the generated caller-variable names in `.env` while retaining their distinct values. Never print those values in your evidence.

## Hand off your result

Use the [evidence template](../evidence/README.md). Your source, chosen request sequence, actual results and explanation must describe the same run. Include the protected route inventory and a limitation of this single-process limiter. A request-count allowance is not a spending cap or a distributed quota system.

[Campus lessons in Notion](https://app.notion.com/p/3ea5a55972ad81b89303c88816f5b3df) · [Continue to streaming](sprint-3.md)
