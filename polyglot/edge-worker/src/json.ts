import { MAX_PUBLIC_JSON_BODY_BYTES } from "./contracts.ts";

export const MAX_JSON_DEPTH = 32;
export const MAX_JSON_COLLECTION_ITEMS = 1_024;
export const MAX_JSON_STRING_CHARS = 131_072;

export function parseBoundedJson(
  raw: string | Uint8Array,
  contentType: string | null | undefined,
  contentLength?: string | null,
): Record<string, unknown> {
  const mediaType = String(contentType ?? "").split(";", 1)[0].trim().toLowerCase();
  if (mediaType !== "application/json") throw new Error("invalid content type");

  if (contentLength != null) {
    const declared = Number.parseInt(String(contentLength).trim(), 10);
    if (!Number.isSafeInteger(declared) || declared < 0 || declared > MAX_PUBLIC_JSON_BODY_BYTES) {
      throw new Error("invalid content length");
    }
  }

  const text = typeof raw === "string" ? raw : new TextDecoder().decode(raw);
  if (new TextEncoder().encode(text).byteLength > MAX_PUBLIC_JSON_BODY_BYTES) {
    throw new Error("JSON body exceeds supported size");
  }

  let value: unknown;
  try {
    value = JSON.parse(text);
  } catch {
    throw new Error("invalid JSON object");
  }
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error("invalid JSON object");
  }

  const stack: Array<{ value: unknown; depth: number }> = [{ value, depth: 0 }];
  while (stack.length) {
    const current = stack.pop()!;
    if (current.depth > MAX_JSON_DEPTH) throw new Error("JSON nesting exceeds the supported depth");
    if (typeof current.value === "string") {
      if (current.value.length > MAX_JSON_STRING_CHARS) throw new Error("JSON string exceeds the supported length");
      continue;
    }
    if (Array.isArray(current.value)) {
      if (current.value.length > MAX_JSON_COLLECTION_ITEMS) throw new Error("JSON array exceeds the supported item count");
      for (const item of current.value) stack.push({ value: item, depth: current.depth + 1 });
      continue;
    }
    if (current.value && typeof current.value === "object") {
      const entries = Object.entries(current.value as Record<string, unknown>);
      if (entries.length > MAX_JSON_COLLECTION_ITEMS) throw new Error("JSON object exceeds the supported field count");
      for (const [key, item] of entries) {
        if (key.length > MAX_JSON_STRING_CHARS) throw new Error("JSON key exceeds the supported length");
        stack.push({ value: item, depth: current.depth + 1 });
      }
    }
  }

  return value as Record<string, unknown>;
}
