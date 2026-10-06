# Connect your Lovable interface to FieldCare

Use this course example with a UI built in Lovable. For the first guided interaction, follow the [public local reference guide](reference-service.md); it includes a runnable recovery UI, an explicitly labelled offline fixture and an opt-in real-provider path. Independent practice adapts that connection to your own cumulative FieldCare service. The [Lovable student guide](../../docs/lovable-student-guide.md) covers prompt design, review, the default backend, Git Sync, privacy, and framework versions.

Keep Lovable Cloud, Lovable's built-in Supabase-based backend. Do not connect a separate Supabase project. FieldCare remains the service that answers equipment questions. For the classroom integration, run both apps on your computer:

```text
Browser → local Lovable UI
        → same-origin TanStack Start server route
        → local FieldCare service
        → retrieval, model, streaming, and safe observation
```

Lovable preview and Cloud Edge Functions run remotely and cannot call `localhost` on your computer. Do not publish this local bridge or use a tunnel. A hosted integration needs a separately deployed FieldCare API and an appropriately secured server-side connection.

## Keep the key on the server

Copy [`src/routes/api.fieldcare.ts`](src/routes/api.fieldcare.ts) into the generated TanStack Start UI repository at `src/routes/api.fieldcare.ts`. The route handles same-origin `POST /api/fieldcare`, checks that the configured FieldCare address is loopback, forwards to the fixed `POST /v1/diagnose-stream` path, and reads the caller key in the server handler. The browser never receives the key.

Copy [`.env.example`](.env.example) to a new `.env.local` in the UI repository. Set `FIELDCARE_CALLER_KEY` to the private key for a caller registered in your current `service/fieldcare/security_settings.py`. For the cumulative weekend-pilot project, use `weekend_partner`’s `FIELDCARE_WEEKEND_PARTNER_KEY` value from FieldCare’s private `.env`. Only the original starter uses `partner`/`FIELDCARE_PARTNER_KEY`; retain your checkpoint mappings and allowance. Keep `.env.local` private and uncommitted. Before adding a key, run `git check-ignore .env.local` from the UI repository root; it should print `.env.local`. If it prints nothing, add `.env.local` to that repository’s `.gitignore` first. Keep `OPENROUTER_API_KEY` in FieldCare's `.env`; the UI does not need it. Restart the UI dev server after changing its environment. Verify that its server configuration actually loads these private variables: the [reference Vite configuration](reference-ui/vite.config.ts) explicitly loads `FIELDCARE_` settings into the server process. Merge this small block into a generated project if needed, preserving its existing plugins and settings; do not expose settings with `VITE_` or `define`.

This route is an intentionally limited local development scaffold. It only accepts HTTP loopback FieldCare URLs, checks the browser origin, and fixes the upstream path. It is not a public endpoint or a production substitute for designing an authenticated deployment.

## Map the response to the screen

Copy [`src/lib/fieldcareClient.ts`](src/lib/fieldcareClient.ts) into the matching UI folder. Connect the form's submit handler to `streamDiagnosis({ question, equipment_id })`. The client yields stream events or wraps an ordinary JSON clarification as a `response` event.

- On `metadata`, save the citations and request ID for the current request.
- On each `delta`, append text to the answer in progress.
- On `complete`, mark that request complete.
- On `error`, non-success HTTP status, malformed event, or missing terminal event, show a recoverable error and do not present partial text as final.
- On a JSON clarification, tell the user what context is missing; do not call it a connection error.

Keep request state tied to one submission so a previous answer cannot appear current after a later error. Follow the components and style of your generated screen rather than replacing it with a transport demo.

## Run the two apps locally

1. Start the FieldCare service you have extended since Sprint 1 using the [local development instructions](../../docs/local-development.md), and keep that terminal open.
2. Open a second terminal at the cloned UI repository root (the folder containing `package.json`). Check `node --version` against its `engines.node` requirement, if present, and use the package manager named by `packageManager`, its README and lockfile. For an npm project with `package-lock.json` and a `dev` script, run:

   ```text
   npm ci
   npm run dev
   ```

   If the project specifies pnpm, Yarn or Bun, use its documented install/dev commands instead; do not generate a second package manager’s lockfile. For npm without a lockfile, use `npm install` for the initial install. `npm run` lists available scripts if there is no `dev` entry. Keep this terminal open alongside FieldCare’s terminal.
3. Open the local URL printed by the UI development server. Send a supported synthetic question and equipment ID. If a live response succeeds, compare its citations and request ID in the UI with the same ID in FieldCare's safe observation record.
4. Try a valid question without the equipment context, then stop FieldCare and submit again. Check that clarification and connection failure remain different states and that loading ends on failure. Restart FieldCare after this stopped-service check.

Compare the browser, UI-server terminal, and FieldCare record. A mock interaction or a direct Python-client call is not evidence that the UI request reached the service.

> 💭 A `429` is a caller allowance result, not a broken connection. The bridge preserves `Retry-After`; inspect it in the browser Network panel, keep FieldCare running, and wait at least that duration before retrying. The weekend-pilot policy is four admitted attempts per 60 seconds across protected routes. Keep that policy rather than resetting the service to get another attempt.

## If your project is older

New Lovable apps use TanStack Start; older projects may use React + Vite. Inspect `package.json` and `src/routes/` before copying the example. Its route is for TanStack Start. Upgrade an eligible older project if Lovable offers that option; otherwise ask for a verified pattern for that actual framework. Do not guess how to keep the caller key server-side.

The course keeps Lovable Cloud as the default backend but does not require a Cloud database table for the FieldCare request. The browser talks to the local UI route, and the route talks to the local service.
