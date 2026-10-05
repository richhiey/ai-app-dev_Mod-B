# FieldCare: build an AI service

In this module, you will turn a technician-support feature into a service that a caller and a Lovable-built interface can use. You will build and run the service on your computer, then continue the same project through authentication, limits, streaming, logging, evaluation, and UI integration.

## Start here

1. Install Git, Python 3.12, and VS Code, then [set up your local project](docs/local-development.md).
2. Read the Campus lessons in order. The lesson pages link to the relevant parts of this repository.
3. Keep working in the same clone through Sprints 1–4. Update from `main` only when the lesson asks; never replace your project with a fresh clone.
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
