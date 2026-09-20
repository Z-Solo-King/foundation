import assert from "node:assert/strict";
import { test } from "node:test";
import { STATES, advance, canTransition, fromBackend, normalize } from "../src/lifecycle.ts";

test("preserves the canonical state vocabulary", () => {
  assert.deepEqual(STATES, [
    "NEW_CHAT",
    "SUBMITTING",
    "QUEUED",
    "RUNNING",
    "STREAMING",
    "COMPLETE",
    "PARTIAL",
    "BLOCKED",
    "REJECTED",
    "UNAVAILABLE",
    "UNKNOWN",
    "RECONNECTING",
    "RESUMED",
    "REPLAYED",
    "AUTH_EXPIRED",
  ]);
});

test("normalizes backend state spellings exactly", () => {
  assert.equal(normalize("completed"), "COMPLETE");
  assert.equal(normalize("auth-expired"), "AUTH_EXPIRED");
  assert.equal(normalize("paused"), "RECONNECTING");
  assert.equal(normalize("not-a-state"), null);
});

test("illegal transitions fail closed to UNKNOWN", () => {
  assert.equal(advance("COMPLETE", "RUNNING"), "UNKNOWN");
  assert.equal(advance("STREAMING", "AUTH_EXPIRED"), "AUTH_EXPIRED");
  assert.equal(advance("QUEUED", "RUNNING"), "RUNNING");
});

test("backend envelope extraction is deterministic", () => {
  assert.equal(fromBackend({ status: "completed" }), "COMPLETE");
  assert.equal(fromBackend({ run: { state: "streaming" } }), "STREAMING");
  assert.equal(fromBackend({ nope: "value" }), "UNKNOWN");
});

test("transition helper mirrors the canonical allowlist", () => {
  assert.equal(canTransition("NEW_CHAT", "SUBMITTING"), true);
  assert.equal(canTransition("NEW_CHAT", "RUNNING"), false);
  assert.equal(canTransition("AUTH_EXPIRED", "RECONNECTING"), true);
});
