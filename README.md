# FieldCare: build an AI service

Welcome to FieldCare! In this module, you’ll turn a technician-support feature into a service that callers—and a Lovable-built interface—can use. You’ll build and run it on your computer, then grow the same project through authentication, limits, streaming, logging, evaluation, and UI integration.

## Start here

1. Install Git, Python 3.12, and VS Code, then [set up your local project](docs/local-development.md). The guide has a step-by-step path for Windows and macOS.
2. Read the Campus lessons in order. The lesson pages link to the relevant parts of this repository.
3. Keep working in the same clone through Sprints 1–4 so each new skill builds on the code you already understand. Update from `main` only when a lesson asks; never replace your project with a fresh clone.
4. In Sprint 4, use Lovable to create your interface with the [Lovable student guide](docs/lovable-student-guide.md), then connect it to the local service with the [integration example](examples/lovable/README.md).

Sprint 1 also has one [Colab checkpoint notebook](notebooks/sprint_1/sprint_1_service_foundations.ipynb) for the assessment. Colab is not the development environment for the other Campus lessons.

## Find your work

- [`service/fieldcare/`](service/README.md) is the FastAPI application you will extend.
- [`clients/`](clients/README.md) contains small callers for repeatable local experiments.
- [`service/data/`](service/data/) contains synthetic equipment and service records.
- [`evidence/`](evidence/README.md) explains how to keep useful, sanitized observations.
- [`src/module_b/`](docs/helpers.md) contains shared mechanics used by the service.

## Keep the project safe and runnable

Keep `.env` private. Never put provider or caller keys in source code, a browser variable, a screenshot, or a commit. Run the server in one VS Code terminal and requests in another. The [local development guide](docs/local-development.md) includes expected results and recovery steps for common errors.
