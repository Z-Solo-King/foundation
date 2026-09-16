import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const state = fs.readFileSync(path.join(ROOT, 'frontend', 'frontend_state.js'), 'utf8');
const app = fs.readFileSync(path.join(ROOT, 'frontend', 'app.js'), 'utf8');
const product = fs.readFileSync(path.join(ROOT, 'docs', 'HEROIC_AI_PRODUCT.md'), 'utf8');

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

assert(state.includes("guestTest: 'rie.frontend.guestTestMode.v1'"), 'guest mode must have a dedicated session key');
assert(state.includes("queryMode === 'test' || queryMode === 'guest'"), 'guest mode URL activation is missing');
assert(state.includes("sessionStorage.setItem(keys.guestTest, '1')"), 'guest mode must use sessionStorage');
assert(state.includes('sessionStorage.removeItem(keys.guestTest)'), 'guest mode must be clearable');

const start = app.indexOf('async function submitGuestTestChat');
const end = app.indexOf('async function consumeChatStream');
assert(start >= 0 && end > start, 'guest test function boundaries are missing');
const guest = app.slice(start, end);
assert(!guest.includes('fetch('), 'guest test mode must not make network requests');
assert(!guest.includes('Authorization'), 'guest test mode must not construct Authorization headers');
assert(guest.includes("result_state: 'TEST_ONLY'"), 'guest responses must be marked TEST_ONLY');
assert(guest.includes("generation_status: 'deterministic_test'"), 'guest responses must identify deterministic test generation');
assert(guest.includes('pending: false'), 'guest lifecycle must clear pending state');
assert(guest.includes('streaming: false'), 'guest lifecycle must terminate streaming state');
assert(guest.includes('normalizedText.slice(0, 1200)'), 'guest echo must cap normalized user text');
assert(app.includes("if (!normalizedText) throw new Error('Message is required');"), 'guest direct-call input guard is missing');
assert(app.includes("if (normalizedText.length > 12_000) throw new Error('Message exceeds the 12000 character limit');"), 'guest direct-call length guard is missing');
assert(state.includes('function newChat()'), 'new chat state lifecycle is missing');
assert(state.includes("title: 'New chat'"), 'new chats must start with the canonical title');
assert(state.includes('setActiveChat(chat.id)'), 'new chats must become the active chat');
assert(app.includes("document.dispatchEvent(new CustomEvent('rie:chat-response'"), 'chat response event bridge is missing');
assert(product.includes('Guest Test mode'), 'product documentation must describe Guest Test mode');
assert(!product.includes('frontend never invents assistant answers when the private runtime is unavailable.'), 'product documentation still contains the superseded guest-mode contradiction');

console.log('guest_test_mode_contract_test: PASS');
