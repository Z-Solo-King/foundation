import assert from "node:assert/strict";
import fs from "node:fs";
import vm from "node:vm";
import { test } from "node:test";

const source = fs.readFileSync(new URL("./generated/lifecycle_queue_controls.js", import.meta.url), "utf8");

test("generated queue controls render validated local queue state", () => {
  let renderCalls = 0;
  const listeners: Record<string, (event: any) => void> = {};
  const html: Record<string, any> = {};
  const document = {
    getElementById(id: string) {
      if (!html[id]) html[id] = { textContent: "", hidden: false, innerHTML: "", classList: { add() {}, remove() {} }, setAttribute() {} };
      return html[id];
    },
    querySelector() { return { classList: { add() {}, remove() {} } }; },
    addEventListener(name: string, cb: (event: any) => void) {
      listeners[name] = cb;
    },
    dispatchEvent() { renderCalls += 1; },
  };
  const window = {
    RIEFrontend: { escapeHtml(value: unknown) { return String(value).replaceAll("<", "&lt;").replaceAll(">", "&gt;"); } },
    addEventListener(name: string, cb: (event: any) => void) { listeners[name] = cb; },
  };
  const localStorage = {
    getItem() {
      return JSON.stringify([{ id: "1", request_id: "r1", text: "<GPU>" }]);
    },
  };
  vm.runInNewContext(source, { window, document, localStorage, console, Element: class {}, CustomEvent, Event });
  assert.equal(html["queue-count"].textContent, "1");
  assert.match(html["queue-list"].innerHTML, /&lt;GPU&gt;/);
  assert.ok(listeners.storage);
  listeners.storage({ key: "rie.frontend.research.queue.v1" });
  assert.equal(html["queue-status"].textContent, "1 waiting");
});
