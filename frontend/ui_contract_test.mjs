import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const html = readFileSync(new URL('./index.html', import.meta.url), 'utf8');
const app = readFileSync(new URL('./app.js', import.meta.url), 'utf8');
const guards = readFileSync(new URL('./ui_guards.js', import.meta.url), 'utf8');

assert.match(html, /<script src="\.\/app\.js"><\/script>/);
assert.match(html, /<script src="\.\/ui_guards\.js"><\/script>/);
for (const view of ['chats', 'projects', 'saved', 'settings']) {
  assert.match(html, new RegExp(`data-view="${view}"`));
}

assert.match(app, /rie\.frontend\.chats\.v2/);
assert.match(app, /rie\.frontend\.projects\.v1/);
assert.match(app, /rie\.frontend\.saved\.v1/);
assert.match(app, /sessionToken/);
assert.match(app, /data-project/);
assert.match(app, /data-save-message/);
assert.match(app, /data-view/);
assert.match(app, /Authorization/);
assert.doesNotMatch(app, /localStorage\.(setItem|getItem)\([^\n]*sessionToken/);

assert.match(guards, /activeChatId/);
assert.match(guards, /repairSavedOwnership/);
assert.match(guards, /chatId/);
assert.match(guards, /data-saved-message/);
assert.match(guards, /data-ui-guard-save/);
assert.match(guards, /window\.location\.reload\(\)/);

console.log('frontend UI contract checks passed');
