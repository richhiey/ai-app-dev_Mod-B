# FieldCare: build an AI service

Turn a technician-support application into a service that other software can call. You will add access controls, stream useful answers, and investigate requests through safe logs and evaluation.

| Your starting point | Open this |
|---|---|
| Sprint 1: explore routes and contracts | [Campus Colab](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_1/sprint_1_service_foundations.ipynb) |
| Sprint 2: develop on your computer | [Set up VS Code and your terminal](docs/local-development.md), then [secure your service](docs/sprint-2.md) |
| Sprint 3: continue your secured service | [Streaming, logs, and evaluation](docs/sprint-3.md) |
| Instructor-led sessions | [Sprint 1](notebooks/sprint_1/README.md) · [Sprint 2](notebooks/sprint_2/README.md) · [Sprint 3](notebooks/sprint_3/README.md) |
| Sprint 4: connect a companion UI | [UI integration](notebooks/sprint_4/README.md) |

## Where you work

- **`service/fieldcare/`** — your application. Begin with `main.py`, then follow the imports into routes and schemas.
- **`clients/`** — small Python programs that make HTTP requests. Edit inputs and inspect actual responses.
- **`service/data/`** — supplied synthetic equipment records, documents, and evaluation design.
- **`evidence/`** — your selected observations and reproduction notes.
- **`src/module_b/`** — supplied provider, security, streaming, and evaluation mechanics. [What each helper does](docs/helpers.md).

The local starter has the original diagnostic route. Your Sprint 1 additions are yours to carry forward; the [transition instructions](docs/local-development.md#bring-your-sprint-1-work) preserve them. Authentication, limiting, streaming registration, and observation are applied during the lessons.

Use the same local project throughout Sprints 2 and 3. Always clone `main`; a new lesson does not mean cloning over your existing work. Keep `.env` private and save your changes before updating course code.

## When something fails

Keep the server terminal visible. Its traceback identifies the failing operation; the client shows what the caller received. Start with the [recovery guide](docs/local-development.md#when-something-fails). A running server, a prepared index, and a successful provider response are three different observations.
