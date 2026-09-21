import test from "node:test";
import assert from "node:assert/strict";

import { frameChatSse } from "../src/sse.ts";

function body(result_state: string) {
  return {
    ok: true,
    response: {
      response_id: "chat-test",
      result_state,
      text: "hello",
      generation_status: "test",
    },
  };
}

test("CANCELLED remains CANCELLED in SSE terminal event", async () => {
  const output = await frameChatSse(body("CANCELLED"));
  assert.match(output, /event: done/);
  assert.match(output, /\"status\":\"cancelled\"/);
});

test("FAILED remains failed in SSE terminal event", async () => {
  const output = await frameChatSse(body("FAILED"));
  assert.match(output, /event: done/);
  assert.match(output, /\"status\":\"failed\"/);
});

test("unknown terminal states fail closed", async () => {
  await assert.rejects(() => frameChatSse(body("TIMEOUT")), /unsupported_terminal_state:TIMEOUT/);
});