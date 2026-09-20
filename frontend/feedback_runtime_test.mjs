import assert from 'node:assert/strict';
import fs from 'node:fs';
import vm from 'node:vm';
import { test } from 'node:test';

const source = fs.readFileSync(new URL('./generated/feedback.js', import.meta.url), 'utf8');

test('generated feedback runtime preserves the candidate-only evidence contract', () => {
  const context = { window: {}, console, Date };
  vm.runInNewContext(source, context);
  const feedback = context.window.RIEFeedback;
  const record = feedback.createFeedback({ kind: 'rating', rating: 5, receiptIds: ['r1'] });
  assert.equal(record.schema_version, 'chat-feedback/v1');
  assert.equal(record.authority, 'candidate');
  assert.equal(record.evidence_overwrite_allowed, false);
  assert.deepEqual(record.receipt_ids, ['r1']);
});
