import assert from "node:assert/strict";
import test from "node:test";
import EdgeWorker from "../edge.ts";

test("public edge fails closed when its core binding is absent", async () => {
  const response = await EdgeWorker.fetch(new Request("https://edge/health"), {});
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { ok: false, error: "core_service_unavailable" });
});

test("public edge forwards request to the Python core through HTTP service binding", async () => {
  let seen;
  const env = {
    CORE: {
      fetch: async (request) => {
        seen = request;
        return new Response('{"ok":true}', {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    },
  };

  const response = await EdgeWorker.fetch(
    new Request("https://edge/api/v1/chat?x=1", {
      method: "POST",
      headers: {
        authorization: "Bearer test",
        "content-type": "application/json",
      },
      body: '{"message":"hello"}',
    }),
    env,
  );

  assert.equal(response.status, 200);
  assert.deepEqual(await response.json(), { ok: true });
  assert.equal(seen.method, "POST");
  assert.equal(new URL(seen.url).pathname, "/api/v1/chat");
  assert.equal(new URL(seen.url).search, "?x=1");
  assert.equal(seen.headers.get("authorization"), "Bearer test");
  assert.deepEqual(await seen.json(), { message: "hello" });
});

test("public edge maps binding failures to a stable 503", async () => {
  const env = {
    CORE: {
      fetch: async () => {
        throw new Error("synthetic binding failure");
      },
    },
  };

  const response = await EdgeWorker.fetch(new Request("https://edge/health"), env);
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { ok: false, error: "core_service_unavailable" });
});
