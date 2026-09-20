import { createHash } from "node:crypto";
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

export function frameChatSse(body: ChatProxyEnvelope, maxBytes = MAX_PUBLIC_JSON_BODY_BYTES): string {
  const response = body.response;
  if (!response) throw new Error("invalid_private_chat_response");

  const responseId = response.response_id.trim();
  if (!responseId) throw new Error("stream_execution_identity_missing");

  const resultState = response.result_state.toUpperCase();
  if (resultState === "BLOCKED") throw new Error("blocked_chat_stream");

  const text = String(response.text ?? "");
  const events: string[] = [
    sse("start", {
      response_id: responseId,
      status: "streaming",
      generation: response.generation_status ?? "unknown",
    }),
  ];

  for (let offset = 0; offset < text.length; offset += MAX_SSE_CHUNK_CHARS) {
    events.push(sse("delta", { text: text.slice(offset, offset + MAX_SSE_CHUNK_CHARS) }));
  }

  const usage = response.usage;
  if (usage) {
    events.push(sse("usage", {
      input_tokens: usage.input_tokens,
      output_tokens: usage.output_tokens,
    }));
  }

  const outputDigest = createHash("sha256").update(text, "utf8").digest("hex");
  const status = resultState === "COMPLETE" ? "completed" : "partial";
  events.push(sse("done", {
    response_id: responseId,
    status,
    result_state: resultState,
    output_digest: outputDigest,
  }));

  const payload = events.join("");
  const bytes = new TextEncoder().encode(payload).byteLength;
  if (bytes > maxBytes) throw new Error("stream response exceeds supported size");
  return payload;
}
