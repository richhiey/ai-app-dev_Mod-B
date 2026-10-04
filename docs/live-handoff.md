# Bring workshop learning into your local service

Your Campus project for Sprints 2–3 stays on your computer. The instructor's Live Colab is a separate demonstration environment. Its `app/` workspace and checkpoint ZIP format differ from the local `service/fieldcare/` project.

## Before a session

Keep your local source and evidence saved. Have VS Code and your two terminals ready. For the instructor demonstration, use the Live notebook's supplied starter or a checkpoint exported by that Live notebook. Label that starting state. Do not import a local Campus source ZIP into the Live notebook.

## During a session

Follow the instructor's demonstration in the named Live section. Results from its demo adapter establish only that demonstration's behavior. Keep them separate from requests to your own application and from real-provider evidence.

When it is your turn, make the change in your local source, restart your server, and run your local clients. `127.0.0.1` means the machine running the client: a Colab request cannot reach the service on your laptop through that address.

| Workshop concept | Your local source and experiment |
|---|---|
| Authentication and secrets | `service/fieldcare/main.py`, `security_settings.py`, private `.env`; vary caller/body in `clients/request.py`. |
| Caller allowances | Set the lesson policy in `security_settings.py`; write your own timeline in `clients/burst.py`. |
| Streaming | Register `stream_routes.py` before the guard; inspect events using `clients/stream.py`. |
| Structured logs and privacy | Attach observation last; match a request ID using `clients/logs.py`; run your privacy check. |
| Evaluation feedback | Select original case IDs; run `clients/evaluate.py` and explain the reference-design boundary. |
| Checkpoint review | Explain your own changed files, selected safe evidence, and the next reproducible check. |

The [Sprint 2](sprint-2.md) and [Sprint 3](sprint-3.md) guides contain the local attachment patterns and commands. Preserve your previous routes and policy. A Live example is a pattern to inspect, not a replacement for your project.

## After a session

Run the relevant checks against your local service. Record which process and source produced each observation. Keep any provider failure as a failure to investigate. Export your local work with `python -m tools.checkpoint export artifacts/my-service.zip`, using a fresh filename, and follow the [evidence guide](../evidence/README.md).

Notebook instructions to import a Campus checkpoint or apply changes back to a Campus copy describe the older Colab workflow. For local Campus work, use the mapping above. Earlier Live-only checkpoint imports remain valid within the Live environment.
