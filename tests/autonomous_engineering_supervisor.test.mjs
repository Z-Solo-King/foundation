import test from 'node:test';
import assert from 'node:assert/strict';
import { parseState, sanitize } from '../tools/autonomous_engineering_supervisor.mjs';

test('mission state parser reads durable issue marker', () => {
  const body = '<!-- autonomous-mission-state:start -->\n```json\n{"schema":"autonomous-mission-state/v1","state":"executing"}\n```\n<!-- autonomous-mission-state:end -->';
  assert.equal(parseState(body).state, 'executing');
});

test('sanitizer removes credential-like values before planner context', () => {
  const value = 'API_KEY=secret123 PRIVATE_KEY=abc SECRET=xyz ordinary';
  const output = sanitize(value);
  assert.equal(output.includes('secret123'), false);
  assert.equal(output.includes('abc'), false);
  assert.equal(output.includes('xyz'), false);
  assert.equal(output.includes('ordinary'), true);
});