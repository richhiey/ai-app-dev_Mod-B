# Run FieldCare on your computer

Welcome! You’ll bring FieldCare to life on your own computer, with the service running in one VS Code terminal and requests coming from another. The service receives each request; the client sends it. Both run locally as separate processes, so you can see exactly what happens on each side.

## Install the tools

Install Python **3.12**, Git, and VS Code. In VS Code, install Microsoft's Python extension. The steps below work in Windows PowerShell and macOS Terminal.

## Clone the course repository

Clone the course's `main` branch once. Keep this folder for Sprints 1–4 so your work carries forward.

```text
git clone --branch main https://github.com/richhiey/ai-app-dev_Mod-B.git
cd ai-app-dev_Mod-B
```

In VS Code, choose **File → Open Folder** and open `ai-app-dev_Mod-B`. Open **Terminal → New Terminal**. Run the following commands from the folder containing `pyproject.toml`.

## Create the project environment

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

`-e .` means Python imports the files in this folder, so changes you save under `service/fieldcare/` are the code the service runs. `-c requirements.lock` keeps the installed dependency versions aligned with the course.

In VS Code, open the Command Palette and run **Python: Select Interpreter**. Choose this project's `.venv`. Close the setup terminal and open two new terminals. In each, check the selected interpreter:

```text
python -c "import sys; print(sys.executable)"
```

The printed path should be inside this repository's `.venv`. If automatic activation is unavailable, use `\.venv\Scripts\python.exe` in PowerShell or `.venv/bin/python` on macOS in place of `python` below. You do not need to change PowerShell's execution policy.

## Set up local configuration

```text
python -m tools.local_env
git check-ignore .env
```

The first command creates `.env` once. It generates two different caller keys and leaves the provider key blank. It never prints key values or overwrites an existing file. The second command should print `.env`, which confirms the file is ignored by Git. That’s a good sign: your local setup is keeping its secrets out of future commits.

Open `.env` in VS Code. Leave `OPENROUTER_API_KEY` blank for the first local checks. `FIELDCARE_DISPATCH_KEY` and `FIELDCARE_PARTNER_KEY` identify callers to FieldCare; `OPENROUTER_API_KEY` identifies the service to its model provider. Keep each value in this local file. Do not paste a key into a terminal command, browser code, or screenshot. Restart running processes after changing configuration.

## Start the service and send a request

In **terminal A**, start the service:

```text
python -m uvicorn fieldcare.main:app --host 127.0.0.1 --port 8000
```

`fieldcare.main:app` means “load the `app` object from `service/fieldcare/main.py`.” The `127.0.0.1` address accepts requests from this computer only. Leave this terminal open; press **Ctrl+C** to stop the server.

In **terminal B**, check health and make the starter request:

```text
python -c "import httpx; print(httpx.get('http://127.0.0.1:8000/health').json())"
python -m clients.request
```

Expected: health reports `status: ok`, `index_prepared: false`, and `provider_configured: false`. The client receives HTTP `200` and application status `needs_clarification`; its question intentionally has no equipment context. These deterministic checks do not call the provider.

Open `clients/request.py`. Find `CALLER`, `PATH`, `BODY`, and the `httpx.post` call. Those values control the experiment. Once Sprint 2 authentication is attached, the unchanged client receives `401` because `CALLER = None`.

## Prepare a real AI request

Preparing the document index and generating an answer use provider quota. You can inspect routes, validation, clarification, and authentication without setting a provider key. When a lesson asks you to observe real retrieval and generation, put your key in `.env`, stop the server, and run:

```text
python -m fieldcare.prepare_index
```

Successful preparation prints `Index ready`. It embeds the supplied service documents and stores the index in `var/chroma`; `var/index.json` records the source and embedding model versions. It does not generate an answer. If the documents change, stop the service and prepare the index again.

Start the server again. Edit `clients/request.py` to send a supported request using a recognized caller:

```python
CALLER = "dispatch"
BODY = {
    "question": "Which filter and airflow checks are documented?",
    "equipment_id": "EQ-FC-1002",
}
```

Run the client again. A successful generated response has HTTP `200`, status `ready`, an answer, and citations. Wording varies. Inspect a cited entry in `service/data/service_docs.json` and check one answer claim against it. A provider error or clarification is an observation to investigate, not a successful generated answer.

## Save work and evidence

Continue in this same clone through Sprints 1–4. Save changes before updating course code and use `git diff` to review them. Runtime files in `.env` and `var/` are local and ignored by Git. Keep selected, sanitized observations in [`evidence/`](../evidence/README.md). Never save keys, full request bodies, or raw private logs there.

## When something fails

| What you see | What to check |
|---|---|
| `python` is missing or imports fail | Check the interpreter path. Use the explicit `.venv` executable and repeat the install command. |
| Connection refused | Confirm terminal A still runs and both processes use port 8000. |
| Address already in use | Stop your earlier server with Ctrl+C. Do not terminate an unidentified process. |
| Saved code seems ignored | Save the file and restart terminal A. Keep auto-reload off while measuring request allowances. |
| `401` after choosing a recognized caller | Compare caller labels and configuration **names** on both sides. Restart after `.env` changes. |
| `422` | Read the validation detail and inspect the request body. |
| `429` | Read `Retry-After`. Keep the same server running while waiting for the allowance to renew. |
| `503` says to prepare the index | Stop the server, prepare the index, then restart. |
| Embedding fails | Keep the traceback. Key rejection, provider credit, network access, and storage permissions have different fixes. |
| Health works but generation fails | Health describes process and preparation state; it does not prove provider access or answer quality. |

Do not delete the database to hide an error. Preserve the failing command and sanitized error message, then check the index path and preparation state. Share the source revision and command if you need help; never share an environment dump.
