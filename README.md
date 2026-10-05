# FieldCare — build an AI service

Welcome to FieldCare. You will turn a technician-support feature into a service that can answer equipment questions, protect its callers, show progress as it works, and support a small Lovable-built interface. You will grow the **same local project through Sprints 1–4**, so each new skill has a place in the application you already understand.

## Start on your computer

1. Install **Git**, **Python 3.12**, and **VS Code** with Microsoft's Python extension. The [local development guide](docs/local-development.md) covers Windows PowerShell and macOS Terminal.
2. Clone the course repository from `main` and open the folder in VS Code:

   ```text
   git clone --branch main https://github.com/richhiey/ai-app-dev_Mod-B.git
   cd ai-app-dev_Mod-B
   ```

3. Follow [Run FieldCare on your computer](docs/local-development.md) to create your virtual environment, set up private local configuration, start the service, and send your first request. The guide shows the results to expect and what to check when a command fails.

Keep this clone for every sprint. Save and review your changes before a lesson asks you to update from `main`; a fresh clone would leave your project work behind.

## Follow the Campus sprint path

Use the matching repository guide when you need file locations, commands, expected behavior, or a troubleshooting path during a Campus lesson.

| Sprint | Repository guides | What you will build |
|---|---|---|
| **1 — Service foundations** | [Local setup](docs/local-development.md) · [Checkpoint setup](docs/colab-setup.md) | Explore and extend the FastAPI service, then explain a versioned service contract. |
| **2 — Secure the service** | [Sprint 2 guide](docs/sprint-2.md) | Recognize callers, protect credentials, and give each caller a fair request allowance. |
| **3 — Streaming and observability** | [Sprint 3 guide](docs/sprint-3.md) | Stream a real answer, record safe service signals, and connect an observation to evaluation. |
| **4 — Companion UI** | [Lovable student guide](docs/lovable-student-guide.md) · [Integration example](examples/lovable/README.md) | Build a focused UI, connect it to your local service, test the full path, and write a handoff. |

The [Sprint 1 Colab notebook](notebooks/sprint_1/sprint_1_service_foundations.ipynb) is for its checkpoint. The walkthrough and practice work happen in your local project. Sprints 2–4 continue in VS Code and the terminal.

## Find what you need

| Resource | Use it for |
|---|---|
| [Service source](service/README.md) | Find the FastAPI routes, contracts, provider call, and files you will extend. |
| [Request clients](clients/README.md) | Send repeatable local requests and inspect responses, streams, logs, and evaluation cases. |
| [Synthetic service data](service/data/) | Check equipment context and cited documents without using private customer data. |
| [Architecture guide](docs/architecture.md) | See how the caller, service, retrieval, model, and UI fit together. |
| [Shared helper guide](docs/helpers.md) | Understand the reusable mechanics behind the service. |
| [Evidence guide](evidence/README.md) | Record useful, sanitized observations for practice and checkpoints. |

Keep `.env` private. Put provider and caller keys in local configuration, never in source code, browser variables, screenshots, or commits. When you need to troubleshoot, the [local development guide](docs/local-development.md) starts with the common errors and their checks.
