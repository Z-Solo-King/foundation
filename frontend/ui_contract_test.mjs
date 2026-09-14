import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');
const styles = readFileSync(new URL('./styles.css', import.meta.url), 'utf8');
const guards = readFileSync(new URL('./ui_guards.js', import.meta.url), 'utf8');

for (const view of ['chats', 'projects', 'saved', 'settings']) assert.match(html, new RegExp(`data-view="${view}"`));
for (const action of ['new-chat', 'backend-check', 'open-queue', 'toggle-workspace', 'attachments', 'voice', 'queue', 'send']) assert.match(html, new RegExp(`data-action="${action}"`));
assert.match(html, /data-mode="chat"/);
assert.match(html, /data-mode="research"/);
assert.match(html, /id="attachment-list"/);
assert.match(html, /data-action="process-queue"/);

for (const key of ['rie.frontend.chats.v2', 'rie.frontend.projects.v1', 'rie.frontend.saved.v1']) assert.match(app, new RegExp(key.replaceAll('.', '\\.')));
for (const contract of ['Authorization', 'strict_zero_cost_only', 'max_sources', 'max_evidence_items', '/api/v1/research', '/api/v1/research/']) assert.match(app, new RegExp(contract.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
for (const behavior of ['setView', 'selectMode', 'enqueueCurrent', 'processQueue', 'repairSavedOwnership', 'pollResearch', 'renderResearch']) assert.match(app, new RegExp(`function ${behavior}`));
assert.match(app, /chatId\);/);
assert.match(app, /localStorage/);
assert.doesNotMatch(app, /localStorage\.(setItem|getItem)\([^\n]*sessionToken/);
assert.match(styles, /focus-visible/);
assert.match(styles, /prefers-reduced-motion/);
assert.match(guards, /repairSavedOwnership/);
assert.match(guards, /window\.location\.reload\(\)/);

console.log('frontend UI parity contract checks passed');
