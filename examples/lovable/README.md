# Connect your Lovable interface to FieldCare

Use this course example after you have a FieldCare service from Sprints 1–3 and a UI built in Lovable. The [Lovable student guide](../../docs/lovable-student-guide.md) covers prompt design, review, the default backend, Git Sync, privacy, and framework versions.

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

Copy [`.env.example`](.env.example) to a new `.env.local` in the UI repository. Set `FIELDCARE_CALLER_KEY` to the recognized `FIELDCARE_PARTNER_KEY` value from FieldCare's private `.env`. Keep `.env.local` private and uncommitted. Keep `OPENROUTER_API_KEY` in FieldCare's `.env`; the UI does not need it. Restart the UI dev server after changing its environment.

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
2. In a second terminal, open the cloned UI repository, install its listed dependencies, and run the development command shown in its `package.json` (commonly `npm run dev`).
3. Open the local URL printed by the UI development server. Send a supported synthetic question and equipment ID. If a live response succeeds, compare its citations and request ID in the UI with the same ID in FieldCare's safe observation record.
4. Try a valid question without the equipment context, then stop FieldCare and submit again. Check that clarification and connection failure remain different states and that loading ends on failure.

Compare the browser, UI-server terminal, and FieldCare record. A mock interaction or a direct Python-client call is not evidence that the UI request reached the service.

## If your project is older

New Lovable apps use TanStack Start; older projects may use React + Vite. Inspect `package.json` and `src/routes/` before copying the example. Its route is for TanStack Start. Upgrade an eligible older project if Lovable offers that option; otherwise ask for a verified pattern for that actual framework. Do not guess how to keep the caller key server-side.

The course keeps Lovable Cloud as the default backend but does not require a Cloud database table for the FieldCare request. The browser talks to the local UI route, and the route talks to the local service.
