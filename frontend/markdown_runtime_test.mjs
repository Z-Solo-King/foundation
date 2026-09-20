import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = fs.readFileSync(new URL('./generated/markdown.js', import.meta.url), 'utf8');

test('generated markdown candidate preserves safe formatting behavior', () => {
  const context = {
    window: {
      RIEFrontend: {
        escapeHtml(value) {
          return String(value)
            .replaceAll('&', '&amp;')
            .replaceAll('<', '&lt;')
            .replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;');
        },
      },
    },
    console,
  };
  vm.runInNewContext(source, context);
  const html = context.window.RIEFrontend.renderMarkdown('**bold** and [docs](https://example.test)');
  assert.match(html, /<strong>bold<\/strong>/);
  assert.match(html, /target="_blank"/);
  assert.doesNotMatch(html, /<script>/i);
});
