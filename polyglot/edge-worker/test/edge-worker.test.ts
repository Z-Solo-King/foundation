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

test("frames partial chat identically to the Python public contract", async () => {
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
  const payload = await frameChatSse(body);
  assert.match(payload, /event: start/);
  assert.match(payload, /event: delta/);
  assert.match(payload, /event: usage/);
  assert.match(payload, /event: done/);
  assert.match(payload, /"result_state":"PARTIAL"/);
  assert.match(payload, /"status":"partial"/);
});

test("rejects blocked or malformed chat results", async () => {
  await assert.rejects(frameChatSse({ ok: true }), /invalid_private_chat_response/);
  await assert.rejects(frameChatSse({ ok: true, response: { response_id: "", result_state: "PARTIAL", text: "" } }), /stream_execution_identity_missing/);
  await assert.rejects(frameChatSse({ ok: true, response: { response_id: "r", result_state: "BLOCKED", text: "" } }), /blocked_chat_stream/);
});

test("enforces public response body bound", () => {
  assert.equal(responseBodyWithinBound("hello"), true);
  assert.equal(responseBodyWithinBound("x".repeat(1_048_576)), true);
  assert.equal(responseBodyWithinBound("x".repeat(1_048_577)), false);
});

test("matches the Python SSE golden vector for a partial deterministic response", async () => {
  const payload = await frameChatSse({
    ok: true,
    response: {
      response_id: "chat-r1",
      result_state: "PARTIAL",
      generation_status: "deterministic_fallback",
      text: "hello world",
      usage: { input_tokens: 3, output_tokens: 2 },
    },
  });
  assert.equal(
    payload,
    'event: start\ndata: {"response_id":"chat-r1","status":"streaming","generation":"deterministic_fallback"}\n\n' +
    'event: delta\ndata: {"text":"hello world"}\n\n' +
    'event: usage\ndata: {"input_tokens":3,"output_tokens":2}\n\n' +
    'event: done\ndata: {"response_id":"chat-r1","status":"partial","result_state":"PARTIAL","output_digest":"b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"}\n\n'
  );
});


test("SSE framing is deterministic across repeats and chunk boundaries", async () => {
  const body = {
    ok: true,
    response: {
      response_id: "chunk-r1",
      result_state: "COMPLETE",
      generation_status: "deterministic_fallback",
      text: "a".repeat(256),
    },
  };
  const first = await frameChatSse(body);
  for (let i = 0; i < 3; i += 1) {
    assert.equal(await frameChatSse(body), first);
  }
  assert.match(first, /"response_id":"chunk-r1"/);
  assert.match(first, /"status":"completed"/);
});

test("SSE frame size gate fails closed", async () => {
  const body = {
    ok: true,
    response: {
      response_id: "oversize",
      result_state: "PARTIAL",
      generation_status: "deterministic_fallback",
      text: "x".repeat(10_000),
    },
  };
  await assert.rejects(frameChatSse(body, 100), /stream response exceeds supported size/);
});

test("empty partial response still emits terminal framing with identity and digest", async () => {
  const payload = await frameChatSse({
    ok: true,
    response: {
      response_id: "empty-r1",
      result_state: "PARTIAL",
      text: "",
    },
  });
  assert.match(payload, /event: start/);
  assert.match(payload, /event: done/);
  assert.match(payload, /"output_digest":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"/);
});


test("rejects prefix and nested path route collisions", () => {
  assert.equal(matchRoute({ method: "GET", url: "https://example/api/v1/research/run-123/extra" }).route, "not_found");
  assert.equal(matchRoute({ method: "GET", url: "https://example/not-api/v1/research/run-123" }).route, "not_found");
  assert.equal(matchRoute({ method: "POST", url: "https://example/evil/api/v1/chat" }).route, "not_found");
  assert.equal(matchRoute({ method: "POST", url: "https://example/api/v1/chat-extra" }).route, "not_found");
});
