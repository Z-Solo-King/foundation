import assert from 'node:assert/strict';
import fs from 'node:fs';

const index = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const queueControls = fs.readFileSync(new URL('./lifecycle_queue_controls.js', import.meta.url), 'utf8');
const sessionBridge = fs.readFileSync(new URL('./session_bridge.js', import.meta.url), 'utf8');

assert.match(index, /lifecycle_queue_controls\.js/);
assert.match(index, /session_bridge\.js/);
assert.match(queueControls, /rie\.frontend\.research\.queue\.v1/);
assert.match(queueControls, /data-action="clear-queue"|data-action=\\?\"clear-queue/);
assert.match(queueControls, /storage/);
assert.match(sessionBridge, /rie\.frontend\.sessionToken\.v1/);
assert.match(sessionBridge, /save-session-token/);
assert.match(sessionBridge, /clear-session-token/);
assert.match(sessionBridge, /sessionStorage/);

console.log('frontend queue/session bridge contract: PASS');
