# Sprint 4 — Campus and Live notebooks

- [Campus Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_4/sprint_4_fieldcare_campus.ipynb) supports C20–C23 with one actual streamed model-backed request, a valid deterministic clarification, and an optional schema-rejection observation.
- [Live Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_4/sprint_4_fieldcare_live.ipynb) supports LS13–LS16 with a bounded request sequence, actual response/event inspection, and sanitized API evidence.

Both notebooks are direct API callers, separate from the Lovable browser path. The UI integration must be checked in the actual Lovable preview and correlated with its own service request ID. Neither notebook fabricates a model answer or claims to exercise the UI connector.

## Course setup required

The course team must provision one reachable HTTPS FieldCare service origin and an approved caller credential, then add them to Colab Secrets as `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY`. `OPENROUTER_API_KEY` remains on FieldCare and is not placed in these client notebooks.

The Lovable reference bridge source is in [`examples/lovable`](../../examples/lovable/README.md). It includes `fieldcareClient` and the authenticated `fieldcare-proxy` Edge Function. The course team must deploy and verify it in the prepared Lovable Cloud project, with the same reachable service origin and caller key stored as backend secrets. Enable anonymous sign-in so the client can obtain a user JWT without adding a login screen. Keep Edge Function JWT verification enabled.

The notebooks use Colab’s existing `requests` package and make bounded HTTP calls; they do not launch Uvicorn, open a tunnel, or install another framework. The connector source is present but has not been deployed to a Lovable project or checked against a reachable FieldCare service. Treat deployment, anonymous-auth configuration, secret setup, stream pass-through, real model-backed output, clarification handling, and request-ID correlation as release gates. Do not replace a missing hosted path with a mock or guessed target.
