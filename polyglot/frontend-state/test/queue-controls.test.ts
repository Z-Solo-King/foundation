import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { test } from "node:test";

const generated = fs.readFileSync(new URL("../../../frontend/generated/lifecycle_queue_controls.js", import.meta.url), "utf8");

test("generated queue controls preserve the browser-local queue contract", () => {
  const listeners: Record<string, (event: unknown) => void> = {};
  const elements: Record<string, any> = {};
  const localStorage = {
    getItem(key: string) {
      assert.equal(key, "rie.frontend.research.queue.v1");
      return JSON.stringify([
        { id: "q1", request_id: "r1", text: "<GPU>" },
        { id: "q2", request_id: "r2", text: "Second" },
      ]);
    },
  };

  function element() {
    return {
      textContent: "",
      hidden: false,
      innerHTML: "",
      classList: { add() {}, remove() {} },
      setAttribute() {},
    };
  }

  const document = {
    getElementById(id: string) {
      elements[id] ??= element();
      return elements[id];
    },
    querySelector() {
      return element();
    },
    addEventListener(name: string, callback: (event: unknown) => void) {
      listeners[name] = callback;
    },
    dispatchEvent() {},
  };

  const window = {
    RIEFrontend: {
      escapeHtml(value: unknown) {
        return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;");
      },
    },
    addEventListener(name: string, callback: (event: unknown) => void) {
      listeners[name] = callback;
    },
  };

  class ElementStub {
    closest() {
      return null;
    }
  }

  vm.runInNewContext(generated, {
    window,
    document,
    localStorage,
    Element: ElementStub,
    Event,
    CustomEvent,
    console,
  });

  assert.equal(elements["queue-count"].textContent, "2");
  assert.equal(elements["queue-status"].textContent, "2 waiting");
  assert.match(elements["queue-list"].innerHTML, /&lt;GPU&gt;/);

  listeners.storage?.({ key: "rie.frontend.research.queue.v1" });
  assert.equal(elements["queue-status"].textContent, "2 waiting");
});
