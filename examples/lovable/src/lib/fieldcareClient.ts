import type { SupabaseClient } from "@supabase/supabase-js";

export type FieldCareRequest = {
  question: string;
  equipment_id?: string;
};

export type FieldCareResponse = {
  answer: string;
  status: string;
  citations: string[];
  mode?: string;
};

export type FieldCareEvent =
  | { type: "response"; response: FieldCareResponse; request_id?: string }
  | { type: "metadata"; status: string; citations: string[]; mode: string; request_id: string }
  | { type: "delta"; text: string }
  | { type: "usage"; [key: string]: unknown }
  | { type: "complete"; [key: string]: unknown }
  | { type: "error"; [key: string]: unknown };

export class FieldCareHttpError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly requestId: string | null,
  ) {
    super(message);
    this.name = "FieldCareHttpError";
  }
}

async function getUserToken(supabase: SupabaseClient): Promise<string> {
  const current = await supabase.auth.getSession();
  if (current.error) throw current.error;
  if (current.data.session) return current.data.session.access_token;

  const anonymous = await supabase.auth.signInAnonymously();
  if (anonymous.error) throw anonymous.error;
  const token = anonymous.data.session?.access_token;
  if (!token) throw new Error("Could not start the FieldCare session.");
  return token;
}

function asEvent(value: unknown): FieldCareEvent {
  if (!value || typeof value !== "object" || !("type" in value)) {
    throw new Error("FieldCare returned an invalid stream event.");
  }
  const event = value as Record<string, unknown>;
  if (!["metadata", "delta", "usage", "complete", "error"].includes(String(event.type))) {
    throw new Error("FieldCare returned an unknown stream event.");
  }
  if (event.type === "metadata" && (
    typeof event.status !== "string" ||
    !Array.isArray(event.citations) ||
    typeof event.mode !== "string" ||
    typeof event.request_id !== "string"
  )) {
    throw new Error("FieldCare returned incomplete stream metadata.");
  }
  if (event.type === "delta" && typeof event.text !== "string") {
    throw new Error("FieldCare returned an invalid text event.");
  }
  return event as FieldCareEvent;
}

async function* readEvents(body: ReadableStream<Uint8Array>): AsyncGenerator<FieldCareEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let pending = "";
  let terminal = false;

  const parseLine = (line: string): FieldCareEvent | undefined => {
    if (!line.trim()) return;
    return asEvent(JSON.parse(line));
  };

  try {
    while (true) {
      const { done, value } = await reader.read();
      pending += decoder.decode(value, { stream: !done });
      const lines = pending.split("\n");
      pending = lines.pop() ?? "";

      for (const line of lines) {
        const event = parseLine(line);
        if (!event) continue;
        yield event;
        if (event.type === "complete" || event.type === "error") {
          terminal = true;
          await reader.cancel();
          return;
        }
      }

      if (done) break;
    }

    const finalEvent = parseLine(pending);
    if (finalEvent) {
      yield finalEvent;
      if (finalEvent.type === "complete" || finalEvent.type === "error") terminal = true;
    }
    if (!terminal) throw new Error("FieldCare stream ended without a terminal event.");
  } finally {
    if (!terminal) await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export async function* diagnoseWithFieldCare(
  supabase: SupabaseClient,
  supabaseUrl: string,
  publishableKey: string,
  input: FieldCareRequest,
): AsyncGenerator<FieldCareEvent> {
  const accessToken = await getUserToken(supabase);
  const response = await fetch(`${supabaseUrl.replace(/\/$/, "")}/functions/v1/fieldcare-proxy`, {
    method: "POST",
    headers: {
      "Accept": "application/x-ndjson, application/json",
      "Authorization": `Bearer ${accessToken}`,
      "apikey": publishableKey,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(input),
  });

  const requestId = response.headers.get("X-Request-ID");
  if (!response.ok) {
    throw new FieldCareHttpError("FieldCare request was rejected.", response.status, requestId);
  }

  const contentType = response.headers.get("Content-Type")?.toLowerCase() ?? "";
  if (contentType.includes("application/json")) {
    const result = await response.json() as FieldCareResponse;
    yield { type: "response", response: result, request_id: requestId ?? undefined };
    return;
  }

  if (!contentType.includes("application/x-ndjson") || !response.body) {
    throw new Error("FieldCare returned an unsupported response format.");
  }

  yield* readEvents(response.body);
}
