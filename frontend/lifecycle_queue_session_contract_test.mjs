import assert from 'node:assert/strict';
import fs from 'node:fs';

const index = fs.readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const queueControls = fs.readFileSync(new URL('./lifecycle_queue_controls.js', import.meta.url), 'utf8');
const chatView = fs.readFileSync(new URL('./chat_view.js', import.meta.url), 'utf8');
const sessionBridgePath = new URL('./session_bridge.js', import.meta.url);

assert.match(index, /lifecycle_queue_controls\.js/);
assert.doesNotMatch(index, /session_bridge\.js/);
assert.match(queueControls, /rie\.frontend\.research\.queue\.v1/);
assert.match(queueControls, /data-action="clear-queue"|data-action=\\?\"clear-queue/);
assert.match(queueControls, /storage/);
assert.match(chatView, /save-session-token/);
assert.match(chatView, /clear-session-token/);
assert.match(chatView, /sessionStorage\.setItem/);
assert.ok(!fs.existsSync(sessionBridgePath), 'retired session_bridge.js must be removed');

console.log('frontend queue/session ownership contract: PASS');