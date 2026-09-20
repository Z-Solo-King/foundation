import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { test } from "node:test";

const source = fs.readFileSync(new URL("./generated/ui_guards.js", import.meta.url), "utf8");

test("generated UI guard repairs saved ownership immediately and on load", () => {
  let calls = 0;
  const listeners: Record<string, () => void> = {};
  const context = {
    window: {
      RIEFrontend: {
        chatStore: {
          repairSavedOwnership() { calls += 1; },
        },
      },
      addEventListener(name: string, callback: () => void) { listeners[name] = callback; },
    },
    console,
  };
  vm.runInNewContext(source, context);
  assert.equal(calls, 1);
  assert.ok(listeners.load);
  listeners.load();
  assert.equal(calls, 2);
});
