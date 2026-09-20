import assert from 'node:assert/strict';
import fs from 'node:fs';

const index = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const lifecycle = fs.readFileSync(new URL('./lifecycle_controller.js', import.meta.url), 'utf8');
const stateMachine = fs.readFileSync(new URL('./generated/lifecycle.js', import.meta.url), 'utf8');
const queue = fs.readFileSync(new URL('./lifecycle_queue_controls.js', import.meta.url), 'utf8');
const workspace = fs.readFileSync(new URL('./workspace_view.js', import.meta.url), 'utf8');

assert.match(index, /lifecycle_state_machine\.js/);
assert.match(index, /lifecycle_controller\.js/);
assert.match(index, /durable browser-local queue items/);
assert.doesNotMatch(index, /data-action="process-queue"/);
assert.match(stateMachine, /NEW_CHAT/);
assert.match(stateMachine, /AUTH_EXPIRED/);
assert.match(stateMachine, /canTransition/);
assert.match(stateMachine, /advance/);
assert.match(stateMachine, /fromBackend/);
assert.match(lifecycle, /lifecycleStateMachine/);
assert.match(lifecycle, /ui_state/);
assert.match(lifecycle, /Idempotency-Key/);
assert.match(lifecycle, /rie\.frontend\.research\.queue\.v1/);
assert.match(lifecycle, /rie\.frontend\.research\.active\.v1/);
assert.match(lifecycle, /visibilitychange/);
assert.match(lifecycle, /window\.addEventListener\('online'/);
assert.match(lifecycle, /status: 'unknown'/);
assert.match(lifecycle, /AUTH_EXPIRED/);
assert.match(lifecycle, /MAX_POLL_MS/);
assert.match(lifecycle, /rie:composer-send/);
assert.match(lifecycle, /rie:composer-queue/);
assert.match(lifecycle, /rie:queue-clear-requested/);
assert.match(lifecycle, /rie:queue-remove-requested/);
assert.match(lifecycle, /Follow-up queued FIFO/);
assert.match(lifecycle, /backend state/i);
assert.match(workspace, /Browser UI observes backend state/);
assert.match(queue, /rie:queue-clear-requested|rie:queue-remove-requested/);
assert.doesNotMatch(queue, /localStorage\.setItem\(QUEUE_KEY/);

console.log('frontend lifecycle contract: PASS');
