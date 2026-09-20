import assert from "node:assert/strict";
import { test } from "node:test";
import { parseBoundedJson } from "../src/json.ts";

test("accepts bounded application/json objects", () => {
  assert.deepEqual(
    parseBoundedJson('{"message":"hello"}', "application/json", "19"),
    { message: "hello" },
  );
});

test("rejects wrong content type and arrays", () => {
  assert.throws(() => parseBoundedJson('{"x":1}', "text/plain"), /content type/);
  assert.throws(() => parseBoundedJson("[1,2,3]", "application/json"), /JSON object/);
});

test("rejects oversized body and pathological depth", () => {
  assert.throws(
    () => parseBoundedJson("x".repeat(1_048_577), "application/json"),
    /supported size/,
  );
  let nested: string = "0";
  for (let i = 0; i < 33; i += 1) nested = '{"next":' + nested + "}";
  assert.throws(() => parseBoundedJson(nested, "application/json"), /nesting/);
});

test("rejects oversized collections and strings", () => {
  const tooMany = JSON.stringify(
    Object.fromEntries(Array.from({ length: 1_025 }, (_, index) => [String(index), 0])),
  );
  assert.throws(() => parseBoundedJson(tooMany, "application/json"), /field count/);
  assert.throws(() => parseBoundedJson(JSON.stringify({ text: "x".repeat(131_073) }), "application/json"), /string/);
});
