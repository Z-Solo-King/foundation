import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const WORKFLOW = new URL('../.github/workflows/autonomous-engineering-supervisor.yml', import.meta.url);

test('autonomous supervisor keeps scheduled execution and adds a main-only self-smoke trigger', () => {
  const text = fs.readFileSync(WORKFLOW, 'utf8');
  assert.match(text, /cron: "37 \* \* \* \*"/);
  assert.match(text, /push:\n    branches: \[main\]/);
  assert.match(text, /- "tools\/autonomous_engineering_supervisor\.mjs"/);
  assert.match(text, /- "tests\/autonomous_engineering_supervisor\.test\.mjs"/);
  assert.match(text, /actions: write/);
  assert.match(text, /issues: write/);
});
