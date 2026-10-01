import test from 'node:test';
import assert from 'node:assert/strict';
import {validateOperationsGuard} from '../tools/validate_operations_main_guard.mjs';

const repo={full_name:'Z-Solo-King/operations',private:true,default_branch:'main'};
const approved='da86e92d4e0fdb68912efb54ef95c69281a7d613';

test('approved revision passes',()=>assert.equal(validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:approved},workflowsPresent:false,approvedSha:approved}).status,'APPROVED'));
test('main drift is detected',()=>assert.equal(validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:'37b35ba9e94600d746bc81e48cd2918b0c239bc7'},workflowsPresent:false,approvedSha:approved}).status,'DRIFT'));
test('workflows are rejected',()=>assert.throws(()=>validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:approved},workflowsPresent:true,approvedSha:approved}),/.github\/workflows/));
test('non-private repo is rejected',()=>assert.throws(()=>validateOperationsGuard({repository:{...repo,private:false},mainBranch:{name:'main',sha:approved},workflowsPresent:false,approvedSha:approved}),/remain private/));

test('integrity workflow builds validator input with jq -n', async () => {
  const fs = await import('node:fs/promises');
  const workflow = await fs.readFile(new URL('../.github/workflows/operations-private-freeplan-guard.yml', import.meta.url), 'utf8');
  assert.match(workflow, /jq -n --arg approved/);
  assert.doesNotMatch(workflow, /\n\s*jq --arg approved/);
});
