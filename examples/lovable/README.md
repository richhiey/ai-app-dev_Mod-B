# Lovable connector for FieldCare

This small reference package connects a Lovable UI to the existing Module B FieldCare service. It is course support code, not a new AI service and not a student setup exercise.

```text
Lovable UI → fieldcareClient → authenticated Edge Function → FastAPI FieldCare
                                                          → LangGraph → ChromaDB/OpenRouter
```

The browser sends the request through `fieldcareClient`. The Edge Function adds the FieldCare caller key on the server and forwards the original body to `POST /v1/diagnose-stream`. It passes through the real NDJSON stream or the service's JSON clarification, along with the safe request ID. OpenRouter keys stay inside FieldCare. There is no second database or model call.

## Files

- `src/lib/fieldcareClient.ts` — obtains the current Supabase Auth session, opens an anonymous session when needed, calls the Edge Function with a user JWT, and yields actual service events as they arrive.
- `supabase/functions/fieldcare-proxy/index.ts` — authenticates the user JWT, reads the service origin and caller key from backend secrets, forwards the request, and streams the response without logging request content.

The browser must use the Lovable project's existing Supabase client. Pass the same client, project URL, and publishable key that the starter already uses to call `createClient`; confirm their actual names and paths in the starter. These public client values are not service or provider secrets. Do not paste service or provider credentials into Lovable chat, frontend variables, notebook outputs, or source control.

## Course-team setup

Provision the connection once in the provided Lovable Cloud starter so students can spend their time learning the UI/service boundary:

1. Enable anonymous sign-in in the project’s Auth settings. The UI does not need a login form; the client obtains a user JWT so the Edge Function can require `auth: "user"`.
2. Add `FIELDCARE_SERVICE_URL` and `FIELDCARE_CALLER_KEY` as backend secrets. The first value is the reachable HTTPS origin only; the second is the service caller credential. Keep `OPENROUTER_API_KEY` in the FieldCare service environment.
3. Add the Edge Function from `supabase/functions/fieldcare-proxy/index.ts` and leave JWT verification enabled. Its handler also requires an authenticated user. Do not change the function to public access.
4. Add `fieldcareClient.ts` to the UI project and call it from the submit action with the existing Supabase client, project URL, publishable key, and request body.
5. Check one supported request and one request without optional equipment context in the actual Lovable preview. Confirm actual service events and the matching `X-Request-ID` before using the starter in class.

The function fixes its upstream path to `/v1/diagnose-stream`; the browser cannot supply a URL. The configured service must be reachable over HTTPS from the function runtime. CORS only controls which browser origins may read a response; the user JWT check is the function's caller authentication. Anonymous sign-in is convenient for this classroom UI but is not an abuse-prevention or production identity policy.

## Calling the client

```ts
const input = {
  question,
  ...(equipmentId ? { equipment_id: equipmentId } : {}),
};

for await (const event of diagnoseWithFieldCare(
  supabase,
  SUPABASE_URL,
  SUPABASE_PUBLISHABLE_KEY,
  input,
)) {
  if (event.type === "metadata") setStatus(event.status);
  if (event.type === "delta") setAnswer((current) => current + event.text);
  if (event.type === "response") setClarification(event.response);
  if (event.type === "complete") setComplete(true);
  if (event.type === "error") setFailed(true);
}
```

This is a usage example, not a fabricated service result. `delta` text comes from the current provider-backed request. A JSON `response` is the deterministic service clarification. If the stream ends without `complete` or `error`, the client reports an incomplete request; it never promotes partial text to a completed answer.

## Release status

The source is prepared for the course starter, but it has not been deployed to a Lovable project or checked against a reachable FieldCare service. The course team must verify the project’s anonymous-auth setting, function deployment, secrets, CORS in its preview, stream pass-through, actual OpenRouter-backed output, clarification response, and request-ID correlation before declaring the walkthrough runnable. Until then, these files are a reviewed implementation draft, not proof of a working hosted integration.

## Product and platform references

- [Lovable Cloud](https://docs.lovable.dev/features/cloud)
- [Lovable Edge Functions](https://docs.lovable.dev/features/edge-functions)
- [Lovable Secrets](https://docs.lovable.dev/features/secrets)
- [Supabase Edge Function authentication](https://supabase.com/docs/guides/functions/auth)
- [Supabase authorization headers](https://supabase.com/docs/guides/functions/auth-headers)
- [Supabase Edge Function secrets](https://supabase.com/docs/guides/functions/secrets)
