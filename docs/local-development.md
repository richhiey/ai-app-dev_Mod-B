# Run FieldCare on your computer

You will keep FastAPI running in one VS Code terminal and make requests from another. The **server** receives requests; the **client** sends them. Both run on your computer, but they are separate processes.

Use Python **3.12** for the course path, Git, and VS Code. Python 3.13 is also included in automated compatibility checks. Install them from [Python](https://www.python.org/downloads/), [Git](https://git-scm.com/downloads), and [VS Code](https://code.visualstudio.com/download). In VS Code, install Microsoft's Python extension. A virtual environment keeps this project's installed packages separate from other projects.

## Get the repository

In a terminal, run:

```text
git clone --branch main https://github.com/richhiey/ai-app-dev_Mod-B.git
cd ai-app-dev_Mod-B
```

In VS Code choose **File → Open Folder** and open `ai-app-dev_Mod-B`. All commands below run from this folder, which contains `pyproject.toml`. Use **Terminal → New Terminal** to open an integrated terminal.

## Create your Python environment

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e . -c requirements.lock
```

**macOS**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e . -c requirements.lock
```

`-e .` installs this repository in editable mode: saved changes under `service/fieldcare/` are the code Python imports. `-c requirements.lock` selects the reviewed dependency versions.

Use **Python: Select Interpreter** in VS Code's command palette and select this project's `.venv`. Close the setup terminal and open two new terminals. The extension normally activates the selected environment. Check **both** terminals:

```text
python -c "import sys; print(sys.executable)"
```

Expected: a path inside this repository's `.venv`. If activation is unavailable, replace `python` in each later command with `.\.venv\Scripts\python.exe` on Windows or `.venv/bin/python` on macOS. You do not need to change PowerShell's security policy. In a path with spaces, use PowerShell's `&` before a quoted executable path.

## Create your local configuration

```text
python -m tools.local_env
git check-ignore .env
```

The first command creates `.env` with two distinct caller keys and an empty provider key. It never prints the values or overwrites an existing file. The second should print `.env`, confirming Git ignores the untracked file. Ignore rules do not remove a file that was already committed.

Open `.env` in VS Code. Keep the provider value empty for the initial checks. `FIELDCARE_DISPATCH_KEY` and `FIELDCARE_PARTNER_KEY` identify callers to your service; `OPENROUTER_API_KEY` authenticates the service to its provider. The application and clients load this file; an existing terminal environment value takes precedence. Restart processes after changing values. Share configuration names, never a screenshot of the values.

## Start the server

In terminal A:

```text
python -m uvicorn fieldcare.main:app --host 127.0.0.1 --port 8000
```

`fieldcare.main:app` means “load `app` from `service/fieldcare/main.py`.” `127.0.0.1` accepts local callers only. The terminal stays busy while the server runs. Keep it open; press **Ctrl+C** when you need to stop it.

In terminal B:

```text
python -c "import httpx; print(httpx.get('http://127.0.0.1:8000/health').json())"
python -m clients.request
```

Expected before adding authentication: health reports `status: ok`, `index_prepared: false`, and `provider_configured: false`; the client receives `200` with `status: needs_clarification`. Its question omits equipment context. Neither operation calls the provider.

Open `clients/request.py`. Find `CALLER`, `PATH`, `BODY`, and the actual `httpx.post` call. These are your experiment inputs. After adding authentication, this unchanged client intentionally receives `401` because `CALLER = None`.

## Prepare real AI requests

Stop terminal A's server. In VS Code, put your OpenRouter key in `.env`; do not paste it into a shell command or source file. Then run:

```text
python -m fieldcare.prepare_index
```

This sends the supplied current service documents to OpenRouter for embeddings and stores them in `var/chroma`. **It uses provider quota.** Successful preparation prints `Index ready`. It creates `var/index.json`, which identifies the document version and embedding model. Re-run preparation if the supplied documents change; stop the service first. It does not generate an answer.

Start the server again. In `clients/request.py`, use this supported body and, once authentication is attached, a recognized caller:

```python
CALLER = "dispatch"
BODY = {
    "question": "Which filter and airflow checks are documented?",
    "equipment_id": "EQ-FC-1002",
}
```

Run the client. A successful result is `200`, `status: ready`, an actual answer, and citations. Read a cited document in `service/data/service_docs.json` and check one answer claim. Wording varies. A provider error or a clarification is an observation to investigate, not a successful generated answer.

## Bring your Sprint 1 work

Keep your original Colab checkpoint ZIP. Unpack it to a **new**, separate directory:

```text
python -m tools.checkpoint unpack "PATH-TO-YOUR-CHECKPOINT.zip" .checkpoint-imports/sprint-1
```

Replace the quoted archive path with your actual file. The command checks archive paths, does not execute restored code, and refuses to replace an existing destination.

Use VS Code's **Select for Compare / Compare with Selected** on the restored source and `service/fieldcare/`. Carry over your added route modules, request/response models, prompts and route registrations. Keep the local starter's `main.py` lifespan, `config.py`, and `resources.py`: these separate index preparation from server startup. Change imports from `app.*` to `fieldcare.*` in copied modules.

For an imported route that needs generation, obtain its graph with:

```python
graph = request.app.state.resources.graph_for(system_prompt=YOUR_ROUTE_PROMPT)
```

Pass that graph to the existing `run_diagnosis` pattern. If your route constructs a graph directly, use `resources = request.app.state.resources.ready()`, then `resources.store` and `resources.client`. `openrouter_model()` supplies the configured model. Run deterministic clarification before requesting AI resources, as `routes.py` demonstrates.

Add each imported router with `app.include_router(...)` before the security attachment. Verify its path in `/docs`, then test its contract and version. Do not replace your earlier work with the supplied diagnostic route and call it a completed checkpoint. If you have no checkpoint, label your starting point as the provided fallback and complete the missing route/contract work before the secured-service assessment.

## Save and carry forward

Continue editing the same folder in Sprint 3. Use `git diff` to review your changes; exclude `.env` and `var`. Put selected safe observations in `evidence/`, following its README.

```text
python -m tools.checkpoint export artifacts/my-service.zip
```

Choose a new archive name on each export; existing archives are preserved. The ZIP contains your service, client code, selected Markdown/JSON evidence and dependency metadata, not `.env`, the database, or raw logs. It is an overlay for a clone of this course repository, not a standalone Python distribution. Record `git rev-parse HEAD` and your changed files in your handoff. Review allowed source and notes for accidental credentials before sharing.

## When something fails

| Observation | Inspect or do this |
|---|---|
| `python` is missing or imports fail | Check the interpreter path; use the explicit `.venv` executable and repeat the install command. |
| Connection refused | Confirm terminal A is running and both client and server use port 8000. |
| Address already in use | Stop your earlier server with Ctrl+C. Do not terminate an unidentified process. |
| Changed code seems ignored | Save the file and restart terminal A. Keep auto-reload off while measuring request allowances. |
| `401` after choosing a recognized caller | Check caller labels and configuration **names** on both sides; restart after `.env` changes. |
| `422` | Inspect the response's validation detail and your request body. |
| `429` | Read `Retry-After`; keep the same server running while waiting for renewal. |
| `503` asking for index preparation | Stop the server, prepare the index, then restart. |
| Embedding request fails | Read the preparation traceback and safe provider message. Key rejection, credit, connectivity and storage need different fixes. |
| Health is OK but generation fails | Health checks process/preparation state, not provider access or answer quality. |

Do not delete your database to conceal a failure. Preserve the error and check its path, permissions and preparation state. Share a sanitized error, source revision and command, never a full environment dump.
