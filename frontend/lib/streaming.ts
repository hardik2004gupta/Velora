import type { ChatRequest, StreamChunk } from "@/types";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("velora_access_token");
}

/**
 * Async generator that calls POST /api/v1/chat/stream and yields parsed SSE
 * chunks until the stream ends or the AbortSignal fires.
 *
 * Throws if the server returns a non-2xx status.
 */
export async function* streamChat(
  payload: ChatRequest,
  signal?: AbortSignal
): AsyncGenerator<StreamChunk> {
  const token = getToken();

  const res = await fetch(`${BASE_URL}/api/v1/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(payload),
    signal,
  });

  if (!res.ok) {
    let message = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      message = err?.error?.message ?? message;
    } catch {
      // non-JSON body
    }
    throw new Error(message);
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE events are separated by double newlines
      const parts = buffer.split("\n\n");
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        for (const line of part.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          try {
            const chunk: StreamChunk = JSON.parse(line.slice(6));
            yield chunk;
          } catch {
            // malformed JSON — skip
          }
        }
      }
    }
  } finally {
    reader.cancel().catch(() => {});
  }
}
