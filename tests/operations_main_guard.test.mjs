import test from 'node:test';
import assert from 'node:assert/strict';
import {validateOperationsGuard} from '../tools/validate_operations_main_guard.mjs';

const repo={full_name:'Z-Solo-King/operations',private:true,default_branch:'main'};
const approved='90fa37df10d63824acd3fe20b64cc91043af9627';

test('approved revision passes',()=>assert.equal(validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:approved},workflowsPresent:false,approvedSha:approved}).status,'APPROVED'));
test('main drift is detected',()=>assert.equal(validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:'37b35ba9e94600d746bc81e48cd2918b0c239bc7'},workflowsPresent:false,approvedSha:approved}).status,'DRIFT'));
test('workflows are rejected',()=>assert.throws(()=>validateOperationsGuard({repository:repo,mainBranch:{name:'main',sha:approved},workflowsPresent:true,approvedSha:approved}),/.github\/workflows/));
test('non-private repo is rejected',()=>assert.throws(()=>validateOperationsGuard({repository:{...repo,private:false},mainBranch:{name:'main',sha:approved},workflowsPresent:false,approvedSha:approved}),/remain private/));