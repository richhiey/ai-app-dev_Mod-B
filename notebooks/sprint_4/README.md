# Sprint 4 Live notebook — local UI planning and evidence

Open [the Live notebook](sprint_4_fieldcare_live.ipynb) for LS13–LS14. Its eight Markdown cells give source outcomes, local preparation, activity prompts, documentation structure and an evidence card. Save one personal copy for both sessions. It contains no executable setup, hosted API observer or model calls.

The required work uses the [neutral Streamlit lab](../../examples/live/streamlit/README.md). Prepare its separate service and UI environments before class. The lab accepts a question and optional supplied context; no Campus project, equipment record or assessment work is required. ChatGPT may help write or explain code. Application generation uses the approved OpenRouter integration in the service; the UI holds only its own caller key.

| Session | Notebook section | Evidence |
|---|---|---|
| LS13 — interactive AI interface | `ls13-plan`, `s4-evidence` | A guarded submit, current-turn response states, actual fixture request ID and matching safe record, plus one independently chosen improvement. |
| LS14 — integration and documentation | `ls14-tests`, `ls14-documents`, `s4-save` | Predicted checks, controlled service failure and recovery, concrete service/UI/API instructions and a reader retry. |

Keep authored Demo, actual HTTP fixture, optional provider and learner evidence distinct. A sidebar rerun should add no request. Partial output remains incomplete without a terminal completion event. No context produces Needs context. A stopped service produces a fresh failed attempt with no new record from that process. A restarted process has reset allowances; it does not prove timed renewal.

## Preparation and recovery

Rehearse the reference UI with the local fixture and match a response to its exact request ID in the safe log. Run the starter separately so learners can see what remains to build. Save learner UI source and documentation beside the copied app; notebook saving does not preserve those local files. Follow the lab README for directories, environment activation, explicit startup modes and recovery.

Optional provider work requires private preparation in the service and remains pending until executed. Keep unavailable provider checks recorded honestly. The notebook cannot reach a laptop through Colab's `127.0.0.1` or establish that browser interaction occurred.

The [Lovable exploration](../../docs/lovable-student-guide.md) is optional on a personal free account: a small mock preview, useful notes, a sketch or skipping it is valid. No paid features, export, Cloud setup, publication or generated artifact is required. The core lab remains independent.

Campus integration and LS15–LS16 follow their separate project instructions. The legacy filename is retained for existing links; this notebook supports the neutral LS13–LS14 Live journey.
