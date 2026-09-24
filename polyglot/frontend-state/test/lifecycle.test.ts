import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { test } from "node:test";

const generated = fs.readFileSync(new URL("../../../frontend/generated/lifecycle.js", import.meta.url), "utf8");

interface LifecycleGlobal {
  lifecycleStateMachine: {
    STATES: string[];
    normalize(value: unknown): string | null;
    advance(from: string, to: string): string;
    fromBackend(value: unknown): string;
  };
}

function machine() {
  const context = { window: {} as { RIEFrontend?: LifecycleGlobal }, console };
  vm.runInNewContext(generated, context);
  const frontend = context.window.RIEFrontend;
  if (!frontend) throw new Error('RIEFrontend registry was not initialized');
  return frontend.lifecycleStateMachine;
}

test("preserves the canonical state vocabulary", () => {
  assert.deepEqual(Array.from(machine().STATES), [
    "NEW_CHAT","SUBMITTING","QUEUED","RUNNING","STREAMING","COMPLETE","PARTIAL",
    "CANCELLED","FAILED","BLOCKED","REJECTED","UNAVAILABLE","UNKNOWN","RECONNECTING","RESUMED","REPLAYED","AUTH_EXPIRED",
  ]);
});

test("normalizes backend state spellings exactly", () => {
  const m = machine();
  assert.equal(m.normalize("completed"), "COMPLETE");
  assert.equal(m.normalize("auth-expired"), "AUTH_EXPIRED");
  assert.equal(m.normalize("paused"), "RECONNECTING");
  assert.equal(m.normalize("cancelled"), "CANCELLED");
  assert.equal(m.normalize("failed"), "FAILED");
  assert.equal(m.normalize("not-a-state"), null);
});

test("illegal transitions fail closed to UNKNOWN", () => {
  const m = machine();
  assert.equal(m.advance("COMPLETE", "RUNNING"), "UNKNOWN");
  assert.equal(m.advance("STREAMING", "AUTH_EXPIRED"), "AUTH_EXPIRED");
  assert.equal(m.advance("QUEUED", "RUNNING"), "RUNNING");
});

test("backend envelope extraction is deterministic", () => {
  const m = machine();
  assert.equal(m.fromBackend({ status: "completed" }), "COMPLETE");
  assert.equal(m.fromBackend({ run: { state: "streaming" } }), "STREAMING");
  assert.equal(m.fromBackend({ nope: "value" }), "UNKNOWN");
});
