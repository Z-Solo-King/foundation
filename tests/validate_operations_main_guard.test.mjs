import test from 'node:test';
import assert from 'node:assert/strict';
import { validateOperationsGuard } from '../tools/validate_operations_main_guard.mjs';

const base={repository:{full_name:'Z-Solo-King/operations',private:true,default_branch:'main'},workflowsPresent:false,approvedSha:'da86e92d4e0fdb68912efb54ef95c69281a7d613'};

test('accepts canonical GitHub branch payload commit.sha',()=>{const r=validateOperationsGuard({...base,mainBranch:{name:'main',commit:{sha:base.approvedSha}}});assert.equal(r.observed_main_sha,base.approvedSha);assert.equal(r.status,'APPROVED')});

test('reports drift without losing observed SHA',()=>{const sha='09bbff6e49040edad1655dd1c2bc0c753ff5a3ae';const r=validateOperationsGuard({...base,mainBranch:{name:'main',commit:{sha}}});assert.equal(r.observed_main_sha,sha);assert.equal(r.status,'DRIFT')});
