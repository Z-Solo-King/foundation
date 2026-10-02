import test from 'node:test';
import assert from 'node:assert/strict';
import { stableJson, digestObject } from '../tools/evidence_kernel.mjs';

test('canonical evidence rejects undefined and non-finite numbers', () => {
  assert.throws(() => stableJson(undefined), /not canonical JSON/);
  assert.throws(() => stableJson(NaN), /not canonical JSON/);
  assert.throws(() => stableJson(Infinity), /not canonical JSON/);
  assert.throws(() => digestObject({value: Number.NEGATIVE_INFINITY}), /not canonical JSON/);
});

test('canonical evidence remains deterministic for JSON-compatible primitives', () => {
  assert.equal(stableJson({b: 1, a: 'x'}), '{"a":"x","b":1}');
  assert.equal(digestObject({b: 1, a: 'x'}), digestObject({a: 'x', b: 1}));
});
