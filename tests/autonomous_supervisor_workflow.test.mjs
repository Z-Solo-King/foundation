import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const WORKFLOW = new URL('../.github/workflows/autonomous-engineering-supervisor.yml', import.meta.url);

test('autonomous supervisor is paused and cannot self-start', () => {
  const text = fs.readFileSync(WORKFLOW, 'utf8');
  assert.match(text, /on:\n  workflow_dispatch:/);
  assert.doesNotMatch(text, /schedule:/);
  assert.doesNotMatch(text, /push:\n/);
  assert.doesNotMatch(text, /actions:\s*write/);
  assert.doesNotMatch(text, /issues:\s*write/);
});
