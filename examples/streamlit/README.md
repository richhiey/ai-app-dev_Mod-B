# FieldCare Streamlit teaching kit

Use the supplied FieldCare design brief to build a local Python UI. Lovable is an optional exploration, never a prerequisite. The handoff is the interaction design and acceptance checks, not exported React code. The default student workflow uses text chat, manual copy/paste into VS Code, and local execution; an editor agent is optional.

## ChatGPT writes code; OpenRouter runs the model

Use ChatGPT only to generate, explain and refine the Python code you inspect and run locally. The application's model provider is OpenRouter, using the existing FieldCare integration and approved model configuration.

```text
Browser → Streamlit Python server → FieldCare service → OpenRouter
             FIELDCARE_CALLER_KEY      OPENROUTER_API_KEY
```

Keep `OPENROUTER_API_KEY` in FieldCare's private configuration. Streamlit uses the supplied FieldCare client; it needs no direct model SDK or OpenAI API key. A ChatGPT subscription does not fund OpenRouter requests. Demo and fixture checks make no model calls.

For the quickest connection to your existing service, use the [Sprint 4 connection guide](../../docs/sprint-4.md). It carries the same chat through connection, tests and handoff.

## Files and ownership

| File | Purpose |
|---|---|
| `design-brief.txt` | Fill the user, layout and wording before generation; record an observed improvement after the first run. |
| `build-prompt.txt` + `client-contract.txt` | Paste into chat with your brief. Send `END OF CONTEXT` after all three. |
| `app_starter.py` | Verify the local installation before generating. |
| `app.py` | Your generated, inspected and revised UI; you create this file. |
| `app_reference.py` | Runnable worked reference and recovery; using it is not evidence of your own AI-assisted iteration. |
| `fieldcare_client.py` | Supplied validation, private settings and local HTTP/stream transport. |
| `mock_client.py` | Predictable UI-only success, clarification, unavailable and interrupted scenarios. |
| `test-notes-template.md` | Record predictions, actual request evidence and a handoff reader trial. |
| `.env.example` | Names only. Actual settings go in ignored `.env.local`. |

## 1. Run the starter

Use Python 3.12 and VS Code. Open a new terminal, enter the course repository and then `cd examples/streamlit`. Keep this UI environment separate from the existing service environment. Create and activate the UI environment, then keep it active while you work on the app.

macOS:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app_starter.py --server.address 127.0.0.1
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app_starter.py --server.address 127.0.0.1
```

Open the local address printed by Streamlit, normally `http://127.0.0.1:8501`. Expect the installation-ready message. Stop with Ctrl+C before changing the entry file. With the environment still active, run `streamlit run app.py --server.address 127.0.0.1` for your generated app or `streamlit run app_reference.py --server.address 127.0.0.1` for the worked reference. Do not run all three at once.

The UI uses its own pinned requirements; leave the FieldCare service's existing environment and lockfile alone. Later starts do not need another installation. Python code runs on the Streamlit server; the browser displays widgets. The Streamlit server makes the HTTP request to FieldCare, so no TanStack proxy, Node setup or Lovable code export is needed.

## 2. Prepare the design and generate

Fill the user/task, two layout or guidance decisions, and exact labels in `design-brief.txt`. Leave the observed issue, chosen improvement and acceptance check blank until you have run the first app. A prototype screenshot can be useful if image input is available, but plain text is sufficient.

Paste `build-prompt.txt`, your completed brief and `client-contract.txt` into one ChatGPT conversation, then send `END OF CONTEXT`. You can send these as consecutive text messages; no upload or repository connection is required. Copy the returned Python code, without the Markdown fences, into a new `app.py` beside the supplied clients. Do not overwrite a working file without saving a copy or committing it first. In VS Code, select this folder's `.venv` interpreter for editor diagnostics.

Read the imports and locate the chat composer, submission guard, per-turn session state, client call and event loop. Reject invented client methods or new dependencies. Run locally and complete the demo checks before asking for a change. Save your prompt, one actual before/after observation and the source revision.

Account/model availability and usage limits can change. Use the tools currently available to your Free account; this activity does not require a specific model, agent, upload, API key or paid editor feature. If chat is limited, continue inspecting and editing saved code or use the worked reference to diagnose the issue, then resume your own iteration when access returns. ChatGPT access does not pay for FieldCare's OpenRouter usage; demo and fixture checks use no model, while a real provider check uses the existing course provider configuration and allowance. [Official account guidance](https://learn.chatgpt.com/docs/use-chatgpt) and [plan guidance](https://learn.chatgpt.com/docs/pricing).

## 3. Check the mock before using a service

Submit a question and `EQ-FC-1002` in Demo/Success: text should appear progressively and finish. Submit without equipment: expect clarification. Then try Unavailable after a success: keep the successful turn visible, but the new failed reply must have no old text, sources or ID. Interrupted must label partial text incomplete. The empty composer disables submission; a whitespace-only question should show validation feedback without calling either client. Toggle request help after a completed result: it must remain visible without making another request. Keep the failed question visible; Retry this message must append a labelled attempt with its original input and connection. New chat clears history without calling a client. Send two messages and check that each keeps its own reply and details.

The main-page composer uses `st.chat_input(submit_mode="disable")` in the pinned Streamlit version; this disables submission during execution. `st.chat_message` holds each user question and assistant reply. Keep equipment in the sidebar and details in per-reply expanders. Visible history is not model memory: the service receives only the current question and equipment. After a clarification, set equipment and resend a full question. Multi-turn context is a separate service-contract extension.

Open a reply's `Sources & request details` to inspect its target, event order, chunk count, UI elapsed/first-text times, actual reported model/tokens, citations and request ID. `usage.tokens` is an integer or null; the event may be absent. Show `Not reported` rather than guessing from answer length. UI timings include the client boundary and must not be equated with service log timings. Demo/fixture answers still prove no model call. The [signal guide](../../docs/sprint-4.md#read-the-service-through-one-reply) explains these distinctions.

## 4. Configure the guided reference

Use a clean teaching checkout of the course repository and its established service environment. Keep your cumulative service separate. In a **service terminal**, activate the Python environment you use for FieldCare, move to that checkout's root, then run:

```text
python -m module_b.ui_reference init --ui-kind streamlit --ui-dir examples/streamlit
```

If your UI is in a different checkout, replace `examples/streamlit` with the **absolute path to the folder containing your running `app.py`**, in quotes. In VS Code, right-click that folder and choose **Copy Path**. A relative path is resolved from the reference checkout, so it can configure an unused UI copy. Initialization creates `var/ui-reference/reference.env` and the UI's `.env.local` with a shared random caller key. It prints no key and refuses to overwrite either file. Check that each path is ignored with `git check-ignore` from the appropriate repository root.

If a reference config already exists from earlier work, reuse it: privately copy the value of its `FIELDCARE_REFERENCE_KEY` into the UI's `FIELDCARE_CALLER_KEY`, and set `FIELDCARE_SERVICE_URL=http://127.0.0.1:8001` in the UI's `.env.local`. These are local editor actions, never chat inputs. Keep `OPENROUTER_API_KEY` only in the service. Do not generate a second key that the running reference does not recognize.

With the service environment still active, start the reference in that terminal:

```text
python -m module_b.ui_reference serve --mode fixture
```

Keep it running. Start your `app.py` in the UI terminal using its own interpreter. Select Local service, submit `Which filter and airflow checks are documented?` with `EQ-FC-1002`, and expect `FIXTURE ONLY` text, source mode `fixture`, completion and a request reference. Fixture mode makes real HTTP requests but calls no model. Find the same record from another service-environment terminal at the reference checkout root:

```text
python -m module_b.ui_reference show-log --mode fixture --request-id UUID_FROM_SCREEN
```

Replace the final token with the actual displayed ID. Expect outcome `completed` and source `none`. Test clarification, then stop the reference and submit once to check failure. Restart after that check. Its allowance is four admitted attempts per 60 seconds. On `429`, read the wait time displayed by the UI, keep the service running and wait; the server-to-service headers are not a browser Network request.

## 5. Complete a provider-backed reference interaction

Stop the fixture reference. Privately configure this reference checkout’s `.env` with `OPENROUTER_API_KEY` and the course-approved model. Your cumulative project’s `.env` is not loaded from another checkout. Use its existing prepared index when available. In the reference checkout's service environment:

```text
python -m fieldcare.prepare_index
python -m module_b.ui_reference serve --mode provider
```

Index preparation and the supported question use provider quota. Keep the UI on the same local target and submit the supported input once. A completed generated answer has source mode `live`, actual text/citations and completion. Match its actual ID with:

```text
python -m module_b.ui_reference show-log --mode provider --request-id UUID_FROM_SCREEN
```

Expect `source=live_provider` and `outcome=completed`; inspect one claim against a cited document. A missing index, provider rejection or incomplete stream is a failure observation, not a successful model call. Keep that final check pending if provider access is unavailable; do not relabel a fixture as live.

## 6. Carry the same app into your project

Follow the [quick project connection](../../docs/sprint-4.md#connect-the-existing-project-without-rebuilding-it): start your existing service, set the private UI target/caller, run the same chat, and first prove a no-equipment clarification plus its project record before spending provider quota. Keep `app.py` and its design brief. Independently compare the reference and your cumulative service contracts. Change the private target to your service, normally `http://127.0.0.1:8000`, and use a key for a caller it currently recognizes. Preserve the checkpoint's caller mapping and allowance, including `weekend_partner` where applicable. Adapt only mappings that actually differ, then repeat the correlated live interaction. Do not copy reference middleware over your project.

## Troubleshooting and scope

- `ModuleNotFoundError`: use the UI's `.venv` interpreter and keep clients beside `app.py`.
- A response disappears on a widget change: store all turns in `st.session_state` and render history outside the submission block.
- Another service request happens on a widget change: put the client call behind the explicit chat submission/retry guard; do not cache calls or trigger them while rendering.
- `401`: compare the private caller value with the target service's registered caller, without printing it.
- `429`: show `retry_after`, wait and keep the service process running. No automatic retries.
- Partial output: completion needs `complete`; neither HTTP `200` nor the first chunk proves completion.
- Hosted deployment: outside this local exercise. A remote Streamlit server also cannot reach the FieldCare process on your laptop.

Official references: [chat input](https://docs.streamlit.io/develop/api-reference/chat/st.chat_input), [chat messages](https://docs.streamlit.io/develop/api-reference/chat/st.chat_message), [session state](https://docs.streamlit.io/develop/api-reference/caching-and-state/st.session_state), [execution flow](https://docs.streamlit.io/develop/api-reference/execution-flow), [secrets](https://docs.streamlit.io/develop/concepts/connections/secrets-management). The source package is a worked pattern; each generated app still needs its own checks.
