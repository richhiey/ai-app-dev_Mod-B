# Build with Lovable and connect your FieldCare service

In Sprint 4, you will use Lovable to shape a small technician interface, bring its code into VS Code, and connect it to the FieldCare service you built in Sprints 1–3. Think of Lovable as a pair-builder: you set the goal, review the change, try it, and decide whether it is ready to keep.

Your finished course flow has one question form and response area. It preserves FieldCare's citations and request ID, handles clarification and errors clearly, and has a real local request that can be matched to the service's safe record. The first Lovable preview uses a mock response so you can improve the interface before debugging a connection.

> **Backend for this course:** Keep Lovable Cloud, Lovable's built-in backend. It is enabled by default and uses Supabase's open-source foundation. Do not connect a separate Supabase project that you own. FieldCare remains the service that answers equipment questions.

## Before you start

You need the FieldCare repository from the earlier sprints, Git and a GitHub account, VS Code, Node.js, your existing local Python setup, and access to the course Lovable workspace. Install Node.js from its [official download page](https://nodejs.org/en/download). Keep the FieldCare repository and the Lovable UI repository in separate folders.

Use only synthetic course examples. Never paste a caller key, `OPENROUTER_API_KEY`, password, real customer or employee information, or confidential code into a prompt, screenshot, issue, or commit. Lovable's account plans have different usage and data settings; check the current [FAQ](https://docs.lovable.dev/introduction/faq) and your workspace policy before you begin. As of September 9, 2026, Lovable says Free and Pro project material may be used to improve its models unless the account owner opts out in Preferences; Business and Enterprise workspace data is excluded by default. Course material should still stay synthetic.

## 1. Get oriented before you prompt

Open the course Lovable workspace and its Sprint 4 project. Find the chat, interactive preview, code view, Cloud view, and Git settings. The chat is where you describe a change; the preview is where you try it; the code view helps you find what changed. Generated code is a first draft, and a polished preview does not prove a service connection.

> 📸 **SCREENSHOT PLACEHOLDER — Editor map:** add a course-workspace capture that labels chat, preview, code view, Cloud view, and Git settings. Hide account names and project IDs.

For a quick tour, use Lovable's [quick start](https://docs.lovable.dev/introduction/getting-started) and [editor guide](https://docs.lovable.dev/features/projects/editor).

## 2. Ask for one useful screen

Start with the person, their task, what they will enter, what the screen will show, and the states it must handle. Ask Lovable to plan before it changes files. For example:

> Plan a single-screen companion for a HelioDesk dispatcher. They enter a required maintenance question and an optional equipment ID. The screen needs labelled fields, one submit action, a loading state, an answer area for citations and request ID, and distinct clarification and error states. Use synthetic examples and a mock response for this UI pass. Keep the default Lovable Cloud backend; do not connect a separate Supabase project or add database tables. Do not add a model call, credentials, or a second AI answer feature. First summarize the proposed screen, states, and files you expect to change.

Read the plan. If Lovable adds a dashboard, login flow, invented endpoint, database feature, or model call, narrow the brief before asking it to build. Use a mock for this stage so you can focus on labels and interaction before network behavior.

> 📸 **SCREENSHOT PLACEHOLDER — First brief:** add a crop of the prompt and Lovable's plan, with no account details or private content.

## 3. Build, review, and iterate with AI

Ask Lovable to build the plan you approved. Try the form with a supported synthetic example and an empty question. Check the preview at a narrow width and use the keyboard to reach and submit every control. Notice whether loading, answer, clarification, and error states are visually distinct.

When you find one issue, describe one change and one behavior to preserve. For example: “On a narrow screen, stack the fields and keep each label visible. Do not change validation or submit behavior.” Try the same interaction again after Lovable updates the page. Check the changed files before accepting the result.

A prompt that is easy to review usually names:

- **Goal:** what the user is trying to do.
- **Context:** the current screen and the relevant code or contract.
- **Change:** one specific behavior or layout change.
- **Keep:** behavior that must remain unchanged.
- **Check:** what you will test in the preview when it is done.

For example, after a layout change you could ask: “Which files did you change, and how can I verify that the labels and submit behavior stayed the same?” Treat the answer as a guide to inspect, not as evidence that a test passed. You are responsible for trying the flow and checking the code.

Lovable's [preview guide](https://docs.lovable.dev/features/projects/preview) explains interactive preview versus a published snapshot. For this course's local end-to-end check, you will run the UI on your computer; the hosted preview cannot reach FieldCare at your computer's `localhost` address.

## 4. Keep Lovable Cloud as the default backend

Lovable Cloud is the built-in backend and is enabled by default. It uses Supabase's open-source foundation for managed database, authentication, storage, and serverless-function capabilities. A separate Supabase connection links your Lovable app to a Supabase project you own, with its own account and billing. The course does not ask you to make that connection. Do not use the “connect your own Supabase project” flow.

These pieces have different jobs:

| Part | Job in this project |
|---|---|
| Lovable Cloud | The Lovable project's default managed app backend. No new data table is needed for the companion UI exercise. |
| FieldCare | Your existing AI service: it checks the caller, retrieves course evidence, calls the model, streams events, and writes a safe service observation. |

The default Cloud backend is not a route to the FieldCare process on your laptop. Keep FieldCare as the answer service and use the local server route described below for the classroom integration.

Read the official [Lovable Supabase guide](https://docs.lovable.dev/integrations/supabase) if you want to understand built-in Cloud versus bringing your own Supabase project. They are different choices; there is no automatic migration between them.

## 5. Sync the UI code to its own repository

When the screen is ready for local work, use Git Sync to link the Lovable project to GitHub. Lovable creates a new repository from the project; it cannot start from the existing FieldCare repository. Wait until the Git settings show that Lovable and GitHub are in sync. Clone the generated UI repository's `main` branch into a folder of its own, then open that folder in VS Code:

```text
git clone --branch main <your-ui-repository-url>
```

Git Sync is two-way, but follows one branch at a time. Check its current sync state before switching between Lovable and local edits; use the official [Git Sync guide](https://docs.lovable.dev/integrations/git-sync-overview) if the branches diverge. Never commit FieldCare's `.env` or the UI's `.env.local`.

New Lovable apps created from May 13, 2026 (June 22, 2026 in Enterprise workspaces) use TanStack Start. Older projects may use React + Vite. Check `package.json` and `src/routes/` before copying framework-specific code. This course's checked-in server route is for TanStack Start. If your older project cannot be upgraded, ask for a verified pattern for its actual framework before continuing; do not paste a TanStack route into a Vite project.

> 📸 **SCREENSHOT PLACEHOLDER — Git Sync:** add a capture showing the generated UI repository name and “in sync” status. Hide account details.

The [FAQ](https://docs.lovable.dev/introduction/faq) explains framework versions, project ownership, and code export. The [Git Sync guide](https://docs.lovable.dev/integrations/git-sync-overview) explains how the synced branch behaves.

## 6. Connect the local UI to local FieldCare

Lovable preview and Cloud Edge Functions run remotely. They cannot call a service that listens only at `127.0.0.1` on your computer; Lovable's [API guide](https://docs.lovable.dev/integrations/any-api) says an integrated service must be reachable from the internet. Do not use a public tunnel to work around this limit.

For the course test, run both programs on your computer. In a TanStack Start project, the checked-in [`api.fieldcare.ts`](../examples/lovable/src/routes/api.fieldcare.ts) provides a same-origin server route. The browser calls the UI server; that route reads the recognized FieldCare caller key on the server and forwards the request to the fixed local `/v1/diagnose-stream` path. The browser does not receive the key. The example accepts only a loopback URL and is a development scaffold, not a production bridge.

Copy that route and [`fieldcareClient.ts`](../examples/lovable/src/lib/fieldcareClient.ts) from the FieldCare repository into the matching folders in the UI repository. Copy [`examples/lovable/.env.example`](../examples/lovable/.env.example) to a new `.env.local` in the UI repository, then set `FIELDCARE_CALLER_KEY` to the recognized `FIELDCARE_PARTNER_KEY` value from FieldCare's private `.env`. Keep `OPENROUTER_API_KEY` only in the FieldCare `.env`. Never use a browser-visible variable prefix for the caller key.

Start FieldCare in one VS Code terminal. In a second terminal, install and start the UI using the actual commands in its `package.json`. Open the local UI URL printed by that server. The [`Lovable integration example`](../examples/lovable/README.md) gives the short copy/run path.

> 📸 **SCREENSHOT PLACEHOLDER — Local run:** add a capture of the UI and both local terminals after removing or covering all environment values, account names, and private request text.

## 7. Test the request and save honest evidence

Use synthetic examples. Test the complete UI flow and compare what you see in three places: browser, UI-server terminal, and FieldCare's safe observation. Do not report a mock as a service call.

1. **Supported request:** submit a known equipment ID and supported question. Look for answer chunks, citations, and a request ID. Find that same ID in FieldCare's safe observation record.
2. **Needs clarification:** omit the equipment context. The UI should present FieldCare's clarification rather than inventing a diagnosis.
3. **Service unavailable:** stop FieldCare, submit again, and check that loading ends with a useful retry message. Restart FieldCare before continuing.
4. **Invalid or unauthorized request:** use the checks in the FieldCare lesson. Confirm the UI handles the response without showing keys or tracebacks.
5. **Responsive and keyboard use:** complete the form with the keyboard and inspect a narrow layout.

A request that appears only in the UI mock is not an end-to-end result. Save the case, expected outcome, actual observation, whether the request reached FieldCare, and its matching ID. Use the earlier-sprint [evidence guide](../evidence/README.md) to keep the record useful and private.

> 📸 **SCREENSHOT PLACEHOLDER — Verified request:** add a crop of a synthetic completed response showing citation IDs and request ID. Make sure no key, private data, account identity, or terminal output is visible.

## 8. Know what publishing changes

Publishing creates a hosted snapshot of the UI; it does not make your laptop's FieldCare service reachable. A hosted UI needs FieldCare deployed at a reachable HTTPS address and a server-side credential configuration designed for that deployment. A Cloud Edge Function could call such a deployed service, but cannot call your laptop's `localhost`.

Do not publish the classroom service or add a public tunnel for this exercise. A Lovable security scan is useful feedback, not a complete security review. Review generated server-side code against the current [security best practices](https://docs.lovable.dev/tips-tricks/security-best-practices).

## Official references

- [Lovable FAQ](https://docs.lovable.dev/introduction/faq) — current framework, ownership, Git Sync, usage, and privacy information.
- [Quick start](https://docs.lovable.dev/introduction/getting-started) and [editor guide](https://docs.lovable.dev/features/projects/editor) — first prompt and editor tour.
- [Preview and testing](https://docs.lovable.dev/features/projects/preview) — interactive preview and published snapshots.
- [Git Sync](https://docs.lovable.dev/integrations/git-sync-overview) — connect and work with the generated repository.
- [Connect to Supabase](https://docs.lovable.dev/integrations/supabase) — built-in Cloud versus a Supabase project you own.
- [Integrate any API](https://docs.lovable.dev/integrations/any-api) and [security best practices](https://docs.lovable.dev/tips-tricks/security-best-practices) — server-side API and credential guidance.
- [TanStack Start server routes](https://tanstack.com/start/latest/docs/framework/react/guide/server-routes) and [environment variables](https://tanstack.com/start/latest/docs/framework/react/guide/environment-variables) — framework details for the checked-in local bridge.

Lovable's interface and documentation can change. If a control has moved, use the linked official docs and inspect your generated repository before following framework-specific instructions.
