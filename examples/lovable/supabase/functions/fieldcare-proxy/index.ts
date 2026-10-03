import { withSupabase } from "npm:@supabase/server@1";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, apikey, content-type, x-client-info",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Expose-Headers": "content-type, retry-after, x-request-id",
};

const handleAuthenticatedRequest = withSupabase(
  { auth: "user" },
  async (request: Request) => {
    if (request.method !== "POST") {
      return Response.json({ detail: "Method not allowed." }, { status: 405, headers: corsHeaders });
    }

    const serviceOrigin = Deno.env.get("FIELDCARE_SERVICE_URL")?.trim();
    const callerKey = Deno.env.get("FIELDCARE_CALLER_KEY");
    if (!serviceOrigin || !callerKey) {
      return Response.json({ detail: "FieldCare connection is not configured." }, { status: 503, headers: corsHeaders });
    }

    let target: URL;
    try {
      target = new URL(serviceOrigin);
    } catch {
      return Response.json({ detail: "FieldCare connection is not configured." }, { status: 503, headers: corsHeaders });
    }

    if (target.protocol !== "https:" || target.pathname !== "/" || target.search || target.hash || target.username || target.password) {
      return Response.json({ detail: "FieldCare connection is not configured." }, { status: 503, headers: corsHeaders });
    }

    const contentType = request.headers.get("content-type") ?? "";
    if (!contentType.toLowerCase().includes("application/json")) {
      return Response.json({ detail: "Content-Type must be application/json." }, { status: 415, headers: corsHeaders });
    }

    const body = await request.text();
    if (new TextEncoder().encode(body).byteLength > 16_384) {
      return Response.json({ detail: "Request body is too large." }, { status: 413, headers: corsHeaders });
    }

    try {
      JSON.parse(body);
    } catch {
      return Response.json({ detail: "Request body must be valid JSON." }, { status: 400, headers: corsHeaders });
    }

    try {
      const upstream = await fetch(new URL("/v1/diagnose-stream", target.origin), {
        method: "POST",
        headers: {
          "Accept": "application/x-ndjson, application/json",
          "Content-Type": "application/json",
          "X-API-Key": callerKey,
        },
        body,
      });

      const headers = new Headers(corsHeaders);
      headers.set("Cache-Control", "no-store");
      for (const name of ["content-type", "x-request-id", "retry-after"]) {
        const value = upstream.headers.get(name);
        if (value) headers.set(name, value);
      }

      return new Response(upstream.body, {
        status: upstream.status,
        headers,
      });
    } catch {
      return Response.json({ detail: "FieldCare could not be reached." }, { status: 502, headers: corsHeaders });
    }
  },
);

export default {
  fetch(request: Request) {
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }
    return handleAuthenticatedRequest(request).then((response) => {
      const headers = new Headers(response.headers);
      for (const [name, value] of Object.entries(corsHeaders)) {
        if (!headers.has(name)) headers.set(name, value);
      }
      return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers,
      });
    });
  },
};
