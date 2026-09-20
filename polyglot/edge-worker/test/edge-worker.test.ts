import assert from "node:assert/strict";
import { test } from "node:test";
import {
  authenticatedJsonHeaders,
  extractBearerToken,
  matchRoute,
  responseBodyWithinBound,
  sseHeaders,
} from "../src/router.ts";
import { frameChatSse } from "../src/sse.ts";

test("matches public worker health/readiness without auth", () => {
  assert.deepEqual(matchRoute({ method: "GET", url: "https://example/health?x=1" }), {
    route: "health", method: "GET", pathname: "/health", requiresAuth: false,
  });
  assert.deepEqual(matchRoute({ method: "GET", url: "https://example/readiness" }), {
    route: "readiness", method: "GET", pathname: "/readiness", requiresAuth: false,
  });
});

test("matches authenticated chat/research/diagnostic routes", () => {
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/chat" }).route, "chat");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/chat/stream" }).route, "chat_stream");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/chatbot/diagnostic" }).route, "chatbot_diagnostic");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/storage/diagnostic" }).route, "storage_diagnostic");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/research" }).route, "research");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/research/publish" }).route, "research_publish");
  assert.equal(matchRoute({ method: "GET", url: "https://example/api/v1/research/run-123" }).route, "research_run");
  assert.equal(matchRoute({ method: "GET", url: "https://example/api/v1/dashboard" }).route, "dashboard");
});

test("preserves auth boundary and cache policy", () => {
  assert.equal(extractBearerToken("Bearer secret"), "secret");
  assert.equal(extractBearerToken("Basic secret"), null);
  assert.deepEqual(authenticatedJsonHeaders(), {
    "Content-Type": "application/json",
    "Cache-Control": "private, no-store, max-age=0, must-revalidate",
  });
  assert.deepEqual(sseHeaders(), {
    "Content-Type": "text/event-stream; charset=utf-8",
    "Cache-Control": "no-store, no-cache, max-age=0, must-revalidate",
    "X-Content-Type-Options": "nosniff",
  });
});

test("frames partial chat identically to the Python public contract", () => {
  const body = {
    ok: true,
    response: {
      response_id: "chat-r1",
      result_state: "PARTIAL",
      generation_status: "deterministic_fallback",
      text: "hello world",
      usage: { input_tokens: 3, output_tokens: 2 },
    },
  };
  const payload = frameChatSse(body);
  assert.match(payload, /event: start/);
  assert.match(payload, /event: delta/);
  assert.match(payload, /event: usage/);
  assert.match(payload, /event: done/);
  assert.match(payload, /"result_state":"PARTIAL"/);
  assert.match(payload, /"status":"partial"/);
});

test("rejects blocked or malformed chat results", () => {
  assert.throws(() => frameChatSse({ ok: true }), /invalid_private_chat_response/);
  assert.throws(() => frameChatSse({ ok: true, response: { response_id: "", result_state: "PARTIAL", text: "" } }), /stream_execution_identity_missing/);
  assert.throws(() => frameChatSse({ ok: true, response: { response_id: "r", result_state: "BLOCKED", text: "" } }), /blocked_chat_stream/);
});

test("enforces public response body bound", () => {
  assert.equal(responseBodyWithinBound("hello"), true);
  assert.equal(responseBodyWithinBound("x".repeat(1_048_576)), true);
  assert.equal(responseBodyWithinBound("x".repeat(1_048_577)), false);
});
