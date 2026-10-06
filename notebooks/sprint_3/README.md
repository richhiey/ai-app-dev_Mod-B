# Sprint 3 Live — Streaming, safe logs and evaluation

Use one personal [Sprint 3 Live Colab notebook](https://colab.research.google.com/github/richhiey/ai-app-dev_Mod-B/blob/main/notebooks/sprint_3/sprint_3_live_workshops.ipynb) for LS09–LS12. Each 60-minute session teaches a core concept, applies it in Colab and checks the explanation. The supplied service is a small runnable example; no Campus project or business-case preparation is required.

| Session | Exact learning outcome | Main notebook cells |
|---|---|---|
| LS09 | Enable streaming on the project service and observe the difference from the client side. | `ls09-source`, `code-04`, `ls09-boundaries`, `code-05` |
| LS10 | Add structured logging that captures request ID, model, tokens, latency, and errors — with redaction for personal data and sensitive prompts. | `ls10-configure-source`, `ls10-configure-start`, `ls10-requests`, `code-07`, `code-09` |
| LS11 | Connect service logs back into the evaluation framework from Module A — no new eval framework built. | `code-11`, independent case selection |
| LS12 | Demo the streaming service with structured logging, redaction, and the eval feedback hook. | Concept clinic, repeated LS09–11 checks, `save-checkpoint` |

## Start and continue

Save a personal notebook copy and run setup. It clones current `main`, installs the lock and preserves an existing marked Live folder. Edit source only under the printed `PROJECT` path in the Files editor, save, inspect the saved source and restart the relevant owned service. A Colab loopback address is inside that runtime; it is not a browser endpoint on your laptop.

Provider preparation and generated-answer comparison require two explicit opt-in switches. With both false, health, authorization/validation/clarification, safe logging, local minimization and the original Module A reference evaluator remain available. An unexecuted provider stream stays pending; deterministic or written examples do not count as observed generation.

The logging application intentionally starts without observation attached. Follow the supplied attachment, retain the required fields, choose whether the optional first-content timer serves your question, then make fresh requests. Independent conclusions and case choices remain the learner's work.

Save the notebook and export a Live ZIP after each session. The ZIP preserves source edits, selected safe observation summaries and model choices. It excludes credentials, indexes, raw response bodies and the runtime JSONL log. In a fresh runtime, upload your ZIP, select a new folder and restore with both saved model choices; review restored source, start it and make fresh requests. Historical evidence is not proof of a new run. See the notebook's setup, recovery table and export instructions.

## Separate Campus work

Campus continues the cumulative local project in VS Code; it does not use this Live notebook as its project environment. Use the [Campus development guide](../../docs/sprint-3.md) and [local setup](../../docs/local-development.md) for that work. FieldCare project application in Live sessions begins in Sprint 4. The old Sprint 3 Campus notebook is retired.
