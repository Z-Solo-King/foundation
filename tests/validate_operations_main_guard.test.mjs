import test from 'node:test';
import assert from 'node:assert/strict';
import { validateOperationsGuard } from '../tools/validate_operations_main_guard.mjs';

const base = {
  repository: { full_name: 'Z-Solo-King/operations', private: true, default_branch: 'main' },
  workflowsPresent: false,
  approvedSha: 'da86e92d4e0fdb68912efb54ef95c69281a7d613',
};

test('accepts GitHub branch payload with nested commit.sha', () => {
  const receipt = validateOperationsGuard({
    ...base,
    mainBranch: { name: 'main', commit: { sha: base.approvedSha } },
  });
  assert.equal(receipt.observed_main_sha, base.approvedSha);
  assert.equal(receipt.status, 'APPROVED');
});

test('reports drift without losing the observed SHA', () => {
  const receipt = validateOperationsGuard({
    ...base,
    mainBranch: { name: 'main', commit: { sha: '09bbff6e49040edad1655dd1c2bc0c753ff5a3ae' } },
  });
  assert.equal(receipt.observed_main_sha, '09bbff6e49040edad1655dd1c2bc0c753ff5a3ae');
  assert.equal(receipt.status, 'DRIFT');
});