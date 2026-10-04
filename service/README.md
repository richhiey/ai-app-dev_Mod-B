# Your FieldCare application

Edit `fieldcare/` throughout Sprints 2 and 3. The folder is installed as the `fieldcare` Python package; run commands from the repository root.

| File | Read it to find… |
|---|---|
| `main.py` | App creation, route registration, lifecycle and your middleware attachments |
| `routes.py`, `schemas.py` | The buffered operation and its input/output contract |
| `security_settings.py` | Caller configuration names and your request allowance |
| `stream_routes.py` | The supplied streaming pattern you register during Sprint 3 |
| `service.py` | Clarification and scope checks before generation |
| `orchestration.py`, `model.py` | Retrieval/generation coordination and the provider call |
| `resources.py`, `prepare_index.py` | Opening prepared resources and the separate embedding step |
| `config.py` | Local environment loading and stable runtime paths |

Keep your added routes here. `data/` contains the synthetic case records and reference-evaluation design. Runtime state belongs in `var/` at the repository root.

[Setup](../docs/local-development.md) · [Authentication and limits](../docs/sprint-2.md) · [Streaming and observation](../docs/sprint-3.md)
