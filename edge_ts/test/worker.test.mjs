import test from "node:test";
import assert from "node:assert/strict";
import { handleShadow, readinessResponse } from "../src/worker.ts";

test("health preserves a stable public contract", async () => {
  const response = await handleShadow(new Request("https://example.test/health"));
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.ok, true);
  assert.equal(body.status, "ok");
  assert.equal(body.contract_version, "public-edge-shadow/v1");
});

test("readiness fails closed without the Operations binding", async () => {
  const response = readinessResponse({});
  assert.equal(response.status, 503);
  const body = await response.json();
  assert.equal(body.ok, false);
  assert.match(body.error, /service binding/i);
});

test("readiness succeeds when the Operations binding exists", async () => {
  const response = readinessResponse({ operations: { fetch: async () => new Response("ok") } });
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.ok, true);
  assert.equal(body.status, "ready");
});

test("unmigrated routes fail explicitly instead of silently shadowing production", async () => {
  const response = await handleShadow(new Request("https://example.test/api/v1/chat"));
  assert.equal(response.status, 404);
});
