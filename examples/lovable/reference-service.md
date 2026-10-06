# Guided local reference and recovery

This is public teaching support for the first guided UI interaction. It does not modify `service/fieldcare/main.py`, install assessment solutions, or replace a learner's cumulative project. Use a clean teaching checkout when demonstrating the reference; keep the learner project and its caller policy separate. The source service binds the public stream route plus the provided authentication and safe-observation patterns.

| State | What it establishes | What it cannot establish |
|---|---|---|
| Lovable mock preview | Screen layout and interaction design | A service request or service record |
| Reference `fixture` mode | Actual local browser → UI server → HTTP service → streamed fixed text → matching safe record | Retrieval, generation, model quality or Lovable-account behavior |
| Reference `provider` mode | The same local path with actual FieldCare retrieval and provider streaming, if successful | Learner-project integration until independently repeated there |

The public [recovery UI](reference-ui/README.md) is a complete TanStack Start example. It is hand-authored support, not a claimed Lovable export. Use it to isolate a connection failure, then return to the learner's generated screen. It is not a substitute for building and revising that screen in Lovable.

## Prepare the reference once

Use the course Python 3.12 environment from [local setup](../../docs/local-development.md). Commands below run at the course repository root; `python` must be that environment's interpreter. If your existing service source is modified, preserve it and create a separate clean teaching clone of `main` and its own environment first. Never reset the learner's checkout.

For the provided recovery UI:

```text
python -m module_b.ui_reference init --ui-dir examples/lovable/reference-ui
```

For a learner's already synced UI instead, replace the argument with the path to its directory containing `package.json`, for example `../fieldcare-ui`. Run initialization only once for a reference/UI pair. It creates `var/ui-reference/reference.env` and the UI's `.env.local` with the same generated caller key, without printing it. It adds the UI ignore rule. It refuses to overwrite existing configuration. If either file exists, reuse it; for another UI, privately configure `FIELDCARE_SERVICE_URL=http://127.0.0.1:8001` and the same reference key in that UI's ignored `.env.local`.

Check `git check-ignore var/ui-reference/reference.env` in the course repository and `git check-ignore .env.local` in the UI repository. Each should print the named path. Keep configuration outside commits and screenshots.

## Connect the same generated screen

1. Check that the generated project uses TanStack Start. Copy `src/routes/api.fieldcare.ts` and `src/lib/fieldcareClient.ts` from this example to the same paths in that UI. Inspect existing files before copying; merge an existing handler deliberately rather than overwriting it.
2. Make sure the local UI server loads the two private variables from `.env.local`. The supplied recovery UI's [`vite.config.ts`](reference-ui/vite.config.ts) explicitly loads only `FIELDCARE_` settings into the server process. If the generated Vite configuration does not already do this, merge that small `loadEnv` block into its existing configuration; keep its plugins and existing options. Never add `VITE_` to either key or inject it with `define`.
3. Find the generated form's mock submit handler. Replace only its response source with `streamDiagnosis`. The [worked React component](reference-ui/src/routes/index.tsx) shows the full state transitions. Keep the generated screen's labels, layout and components. Use this mapping:

   | Event | Update for this submission |
   |---|---|
   | Before the call | Clear previous answer, citations and request ID; show loading; prevent concurrent submission. |
   | `metadata` | Save `mode`, `request_id` and `citations`. |
   | `delta` | Append `text`; keep loading. |
   | `complete` | Mark complete. |
   | `response` | Display its JSON `answer`, `status` and `mode`; retain the event's `request_id` from the response header. |
   | `error` or thrown error | End loading, distinguish failure from clarification; partial text is not final. |
   | Finally | Re-enable submission. |

   Pass `{ question, equipment_id }`; omit `equipment_id` if its field is blank. Preserve the question's required validation. A fixture must remain visibly labelled `fixture` and its text must not be presented as equipment advice.

## Rehearse the local path without a provider

In terminal A at the course root:

```text
python -m module_b.ui_reference serve --mode fixture
```

This serves only `127.0.0.1:8001`. Health at `http://127.0.0.1:8001/health` identifies the mode; health does not verify a provider. In terminal B, at the recovery UI directory:

```text
npm ci
npm run dev
```

For a generated UI, use its actual package manager, lockfile and dev script, as described in the [two-app run guide](README.md#run-the-two-apps-locally). Open the **local** UI URL, not hosted Lovable preview. The recovery URL is `http://127.0.0.1:3000`.

Submit `Which filter and airflow checks are documented?` with `EQ-FC-1002`. Expect `FIXTURE ONLY` text, mode `fixture`, terminal `Complete`, and a request ID. This text is intentionally fixed; no provider is called. In another course-root terminal, replace `UUID_FROM_SCREEN` with that actual ID:

```text
python -m module_b.ui_reference show-log --mode fixture --request-id UUID_FROM_SCREEN
```

Expect one record with the same ID, route `/v1/diagnose-stream`, status `200`, outcome `completed`, and source `none`. The log means the HTTP response completed; it does not mean AI generated an answer. Logs live in `var/ui-reference/fixture-events.jsonl` and contain no question, answer or key.

Remove the equipment ID and submit again: expect JSON clarification, not completion of a generated answer. Stop terminal A with Ctrl+C and submit again: expect `502`, no stale answer or request ID, and loading ends. Restart with the same command. A blank question should not submit.

The reference allows **four admitted attempts per 60 seconds**. A `429` preserves `Retry-After`; leave the service running and wait at least that duration. Restarting is for the explicitly stopped-service check, not proof of quota renewal.

## Complete the guided provider interaction

Stop the fixture service. Configure `OPENROUTER_API_KEY` privately in the reference checkout's `.env` using the existing local setup guide. The key stays in FieldCare, not the UI. Index preparation uses provider quota and is separate from startup:

```text
python -m fieldcare.prepare_index
python -m module_b.ui_reference serve --mode provider
```

Keep the UI's target at port `8001`; restart the UI only if its environment changed. Submit the same supported input from the same screen. Expect mode `live`, actual progressive content and citations, terminal `complete`, and the screen's request ID in:

```text
python -m module_b.ui_reference show-log --mode provider --request-id UUID_FROM_SCREEN
```

A successful provider record has source `live_provider` and outcome `completed`. Inspect one cited document against one answer claim. Exact wording is not fixed. Missing configuration/index, a provider rejection or an interrupted stream is a real failure observation; never change to fixtures and label it a provider success. Record that the provider check remains pending until it succeeds.

## Carry the same UI into independent project work

Save the reference UI revision and one sanitized provider request/record pair. Then independently change the private UI target to the learner service (normally port `8000`) and use the key for a caller in that service's **current** mapping. Keep `operations`/`weekend_partner` and the existing allowance where the checkpoint uses them. Do not copy the reference middleware configuration into the learner service. Compare the actual contract, adapt only necessary mappings, and reproduce the interaction and matching record on the learner service.

## Source and verification boundary

Official sources checked 5 October 2026: [Lovable framework FAQ](https://docs.lovable.dev/introduction/faq), [Git Sync](https://docs.lovable.dev/integrations/github), [TanStack server routes](https://tanstack.com/start/latest/docs/framework/react/guide/server-routes) and [environment variables](https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables). Inspect the actual generated framework and active synced branch; not every existing project is TanStack Start. The course-account Lovable build/sync and generated-project rehearsal still require actual account verification. Automated fixture and source checks cannot establish those facts.
