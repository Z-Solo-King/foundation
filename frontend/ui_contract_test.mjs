import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');
const styles = readFileSync(new URL('./styles.css', import.meta.url), 'utf8');
const guards = readFileSync(new URL('./ui_guards.js', import.meta.url), 'utf8');

for (const view of ['chats', 'projects', 'saved', 'settings']) assert.ok(html.includes(`data-view="${view}"`));
for (const action of ['new-chat', 'backend-check', 'open-queue', 'toggle-workspace', 'attachments', 'voice', 'queue', 'send']) assert.ok(html.includes(`data-action="${action}"`));
for (const mode of ['chat', 'research']) assert.ok(html.includes(`data-mode="${mode}"`));
for (const element of ['attachment-list', 'queue-count', 'workspace', 'message-queue']) assert.ok(html.includes(`id="${element}"`));

for (const contract of ['rie.frontend.chats.v2', 'rie.frontend.projects.v1', 'rie.frontend.saved.v1', 'Authorization', 'strict_zero_cost_only', 'max_sources', 'max_evidence_items', '/api/v1/research', '/api/v1/research/']) assert.ok(app.includes(contract), `missing app contract: ${contract}`);
for (const behavior of ['function setView', 'function selectMode', 'function enqueueCurrent', 'function processQueue', 'function repairSavedOwnership', 'async function pollResearch', 'function renderResearch']) assert.ok(app.includes(behavior), `missing UI behavior: ${behavior}`);
assert.ok(app.includes('chatId'), 'research results must retain source chat identity');
assert.ok(app.includes('localStorage'), 'local browser persistence should remain available');
assert.ok(!/localStorage\.(setItem|getItem)\([^\n]*sessionToken/.test(app), 'session token must not be persisted');
assert.ok(styles.includes('focus-visible'), 'keyboard focus treatment missing');
assert.ok(styles.includes('prefers-reduced-motion'), 'reduced-motion treatment missing');
assert.ok(guards.includes('repairSavedOwnership'), 'legacy saved-data repair missing');
assert.ok(guards.includes('window.location.reload()'), 'legacy chat navigation repair missing');

console.log('frontend UI parity contract checks passed');
