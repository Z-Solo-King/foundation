import assert from 'node:assert/strict';
import fs from 'node:fs';

const index = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const lifecycle = fs.readFileSync(new URL('./lifecycle_controller.js', import.meta.url), 'utf8');

assert.match(index, /lifecycle_controller\.js/);
assert.match(index, /durable browser-local queue items/);
assert.doesNotMatch(index, /data-action="process-queue"/);

assert.match(lifecycle, /Idempotency-Key/);
assert.match(lifecycle, /rie\.frontend\.research\.queue\.v1/);
assert.match(lifecycle, /rie\.frontend\.research\.active\.v1/);
assert.match(lifecycle, /visibilitychange/);
assert.match(lifecycle, /window\.addEventListener\('online'/);
assert.match(lifecycle, /status: 'unknown'/);
assert.match(lifecycle, /MAX_POLL_MS/);
assert.match(lifecycle, /currentMode\(\) === 'research'/);
assert.match(lifecycle, /Follow-up queued FIFO/);
assert.match(lifecycle, /Backend state only/);

console.log('frontend lifecycle contract: PASS');
