import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { test } from "node:test";

const generated = fs.readFileSync(new URL("../../../frontend/generated/ui_guards.js", import.meta.url), "utf8");

test("generated UI guard repairs ownership immediately and on load", () => {
  let repairs = 0;
  const listeners: Record<string, () => void> = {};
  const window = {
    RIEFrontend: {
      chatStore: {
        repairSavedOwnership() {
          repairs += 1;
        },
      },
    },
    addEventListener(name: string, callback: () => void) {
      listeners[name] = callback;
    },
  };

  vm.runInNewContext(generated, { window, console });
  assert.equal(repairs, 1);
  assert.equal(typeof listeners.load, "function");
  listeners.load();
  assert.equal(repairs, 2);
});
