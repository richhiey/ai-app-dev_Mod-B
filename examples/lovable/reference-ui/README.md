# FieldCare local recovery UI

Public, hand-authored TanStack Start reference. This is not a Lovable-generated project or learner assessment solution. It provides a runnable form and stream-state example when diagnosing a local integration problem. Keep your generated screen for the learning task.

Prerequisites: Node `>=22.12.0`, npm, the installed course Python environment, and a local reference service. Follow [reference setup](../reference-service.md) to create the two ignored private configuration files without printing secrets.

From this directory:

```text
npm ci
npm run dev
```

Open `http://127.0.0.1:3000`. The server binds loopback and refuses another port. `npm run build` checks production bundling; `npm run check` checks TypeScript after the build generates the route tree. No deployment is configured or required.

The server loads `.env.local` via `vite.config.ts`. Only the server route reads `FIELDCARE_CALLER_KEY`. The browser uses `/api/fieldcare`; the bridge fixes the upstream path to `/v1/diagnose-stream`. `src/routes/api.fieldcare.ts` and `src/lib/fieldcareClient.ts` intentionally match the copyable parent examples; a Python test detects drift.

Use the supported question and `EQ-FC-1002` already in the form. Fixture mode returns explicitly labelled fixed text over actual local HTTP, without AI. Remove the equipment ID for clarification. Stop the reference service for connection failure, then restart it. The form clears stale results before every request and waits for `complete` before calling a stream complete. Match the current request ID with the reference service log using the linked guide. Provider mode is an explicit separate opt-in.

Use the component as a worked mapping reference, not as a replacement for the screen built in Lovable. In independent project work, preserve the learner's caller mapping and allowance.
