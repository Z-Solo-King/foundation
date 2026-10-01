import assert from "node:assert/strict";
import { test } from "node:test";
import { mapBounded, mapBoundedByKey } from "./bounded_parallel.mjs";

test("mapBounded preserves input order and global concurrency", async () => {
  const items = Array.from({ length: 10 }, (_, i) => i);
  let active = 0;
  let maxActive = 0;
  const output = await mapBounded(items, 3, async item => {
    active += 1;
    maxActive = Math.max(maxActive, active);
    await new Promise(resolve => setTimeout(resolve, 5));
    active -= 1;
    return item * 2;
  });

  assert.deepEqual(output, items.map(item => item * 2));
  assert.equal(maxActive, 3);
});

test("mapBoundedByKey preserves global concurrency and serializes each key", async () => {
  const items = ["a1", "a2", "b1", "b2", "c1", "c2"];
  let active = 0;
  let maxActive = 0;
  const activeByKey = new Map();
  const maxByKey = new Map();

  const output = await mapBoundedByKey(
    items,
    3,
    item => item[0],
    async item => {
      const key = item[0];
      active += 1;
      maxActive = Math.max(maxActive, active);
      const current = (activeByKey.get(key) ?? 0) + 1;
      activeByKey.set(key, current);
      maxByKey.set(key, Math.max(maxByKey.get(key) ?? 0, current));
      await new Promise(resolve => setTimeout(resolve, 5));
      activeByKey.set(key, current - 1);
      active -= 1;
      return item.toUpperCase();
    },
    1,
  );

  assert.deepEqual(output, items.map(item => item.toUpperCase()));
  assert.equal(maxActive, 3);
  assert.deepEqual([...maxByKey.values()], [1, 1, 1]);
});

test("invalid concurrency limits fail closed", async () => {
  await assert.rejects(() => mapBounded([], 0, async item => item), RangeError);
  await assert.rejects(() => mapBoundedByKey([], 1, () => "x", async item => item, 0), RangeError);
});
