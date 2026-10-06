# Bring workshop learning into your local service

Your Campus project for Sprints 1–4 stays on your computer. For Sprints 1–3, the Live Colab is the shared teaching and learner-practice environment for core concepts. It uses a separate public practice workspace with the same `service/fieldcare/` source layout. Its source export remains Live practice, not Campus assessment evidence.

## Before a session

Open the sprint’s Live notebook and save a personal copy. Use its supplied starter or restore your own Live practice ZIP. No local Campus project, VS Code setup or business-case preparation is required for LS01–LS12. Do not import a Campus source ZIP into a Live notebook. Follow the notebook’s setup, section entry points and recovery guidance.

## During a session

Follow the instructor's demonstration in the named Live section. Deterministic clarification and validation establish only those request boundaries. Keep them separate from requests to your own application and from real-provider evidence.

Follow the session’s stated workspace. LS02 has you create the formative checklist route in the separate Live Files workspace and register it in `live_extension.py`; LS03 continues that composition. Keep that public practice evidence separate. When applying the pattern to your Campus project, make the change in your local source, restart your server, and run your local clients. `127.0.0.1` means the machine running the client: a Colab request cannot reach the service on your laptop through that address.

| Workshop concept | Your local source and experiment |
|---|---|
| Service and contracts | Inspect `main.py`, `routes.py` and `schemas.py`; edit `clients/request.py`, then run it in terminal B. |
| Extension and versioning | Register a route in `main.py`, keep its prompt/schema separate, restart terminal A, and compare the original caller. |
| Authentication and secrets | `service/fieldcare/main.py`, `security_settings.py`, private `.env`; vary caller/body in `clients/request.py`. |
| Caller allowances | Set the lesson policy in `security_settings.py`; write your own timeline in `clients/burst.py`. |
| Streaming | Register `stream_routes.py` before the guard; inspect events using `clients/stream.py`. |
| Structured logs and privacy | Attach observation last; match a request ID using `clients/logs.py`; run your privacy check. |
| Evaluation feedback | Select original case IDs; run `clients/evaluate.py` and explain the reference-design boundary. |
| Checkpoint review | Explain your own changed files, selected safe evidence, and the next reproducible check. |

The [Sprint 2](sprint-2.md) and [Sprint 3](sprint-3.md) guides contain the local attachment patterns and commands. Preserve your previous routes and policy. A Live example is a pattern to inspect, not a replacement for your project.

## After a session

Save notebook notes and outputs, run the final Live export cell, and download its ZIP after each workshop. Files-panel source edits are saved in the ZIP, not inside the notebook. Keep the printed V1/V2 model choices with your notes (also saved as `evidence/live-models.json` in the ZIP). In a fresh runtime, upload that Live ZIP, set `LIVE_ARCHIVE`, fill both `RESTORED_MODELS`, and choose a new `LIVE_FOLDER` in setup. Review restored source before starting it. Clear `LIVE_ARCHIVE` before rerunning setup in that same runtime; the marked folder is reused. Re-enter private credentials and explicitly prepare any needed index. Campus checkpoints use their separate runner.

LS07's summary cell saves only the edited log/prompt policies and selected synthetic checks/results under `evidence/`; rerun it after your final edits before exporting. Its disposable Git repository and secret-shaped fixture files are excluded. LS08 can inspect the restored evidence without claiming it is a fresh execution.

Run the relevant checks against your local service. Record which process and source produced each observation. Keep any provider failure as a failure to investigate. Export your local work with `python -m tools.checkpoint export artifacts/my-service.zip`, using a fresh filename, and follow the [evidence guide](../evidence/README.md).

The Live compositions make the same registration order visible: routes first, security next, observation last. Each notebook starts a new owned process when changing composition. Keep a single process running for any allowance-renewal experiment. Prepare the document index explicitly before opting into provider calls. A Colab provider key belongs in Secrets or hidden input; a local provider key belongs in private `.env`.

## Sprint 4: local UI workshops

Keep the generated UI in a separate repository beside FieldCare. The first guided interaction uses the [public reference service](../examples/lovable/reference-service.md); then adapt its trusted connector to your own cumulative service. The supplied LS13–LS14 plan uses this local path for the scoped companion UI, integration testing and documentation. The Live notebook is an optional hosted API observer and cannot verify a browser interaction. Keep fixture, provider and learner-project evidence distinct.
