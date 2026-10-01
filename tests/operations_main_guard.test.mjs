import test from 'node:test';
import assert from 'node:assert/strict';
import { validateOperationsGuard } from '../tools/validate_operations_main_guard.mjs';

const repo = {full_name:'Z-Solo-King/operations', private:true, default_branch:'main'};
const branch = {name:'main', sha:'90fa37df10d63824acd3fe20b64cc91043af9627'};

test('accepts an approved immutable Operations revision', () => {
  const receipt = validateOperationsGuard({repository:repo,mainBranch:branch,workflowsPresent:false,approvedSha:branch.sha});
  assert.equal(receipt.status, 'APPROVED');
});

test('detects Operations main drift without mutating it', () => {
  const receipt = validateOperationsGuard({
    repository:repo,
    mainBranch:{...branch,sha:'37b35ba9e94600d746bc81e48cd2918b0c239bc7'},
    workflowsPresent:false,
    approvedSha:branch.sha
  });
  assert.equal(receipt.status, 'DRIFT');
});

test('rejects a private repository with workflows', () => {
  assert.throws(() => validateOperationsGuard({
    repository:repo,
    mainBranch:branch,
    workflowsPresent:true,
    approvedSha:branch.sha
  }), /must not contain .github\/workflows/);
});

test('rejects non-private Operations repository', () => {
  assert.throws(() => validateOperationsGuard({
    repository:{...repo,private:false},
    mainBranch:branch,
    workflowsPresent:false,
    approvedSha:branch.sha
  }), /remain private/);
});
