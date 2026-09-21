import {
  MAX_PUBLIC_JSON_BODY_BYTES,
  MAX_SSE_CHUNK_CHARS,
  type ChatProxyEnvelope,
} from "./contracts.ts";

function json(value: unknown): string {
  return JSON.stringify(value);
}

function sse(event: string, payload: unknown): string {
  return `event: ${event}\ndata: ${json(payload)}\n\n`;
}

async function sha256Hex(value: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(value));
  return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function frameChatSse(body: ChatProxyEnvelope, maxBytes = MAX_PUBLIC_JSON_BODY_BYTES): Promise<string> {
  const response = body.response;
  if (!response) throw new Error("invalid_private_chat_response");

  const responseId = response.response_id.trim();
  if (!responseId) throw new Error("stream_execution_identity_missing");

  const resultState = response.result_state.toUpperCase();
  if (resultState === "BLOCKED") throw new Error("blocked_chat_stream");

  const text = String(response.text ?? "");
  const encoder = new TextEncoder();
  const events: string[] = [];
  let bytes = 0;

  const pushEvent = (event: string, payload: unknown): void => {
    const encoded = sse(event, payload);
    const encodedBytes = encoder.encode(encoded).byteLength;
    if (bytes + encodedBytes > maxBytes) {
      throw new Error("stream response exceeds supported size");
    }
    events.push(encoded);
    bytes += encodedBytes;
  };

  pushEvent("start", {
    response_id: responseId,
    status: "streaming",
    generation: response.generation_status ?? "unknown",
  });

  for (let offset = 0; offset < text.length; offset += MAX_SSE_CHUNK_CHARS) {
    pushEvent("delta", { text: text.slice(offset, offset + MAX_SSE_CHUNK_CHARS) });
  }

  const usage = response.usage;
  if (usage) {
    pushEvent("usage", {
      input_tokens: usage.input_tokens,
      output_tokens: usage.output_tokens,
    });
  }

  const outputDigest = await sha256Hex(text);
  const status = resultState === "COMPLETE" ? "completed" : "partial";
  pushEvent("done", {
    response_id: responseId,
    status,
    result_state: resultState,
    output_digest: outputDigest,
  });

  return events.join("");
}
