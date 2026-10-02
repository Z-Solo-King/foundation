import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {inventory,buildPlan,reconcile,assertComplete,LENSES} from '../tools/unified_scan_fabric.mjs';

test('inventory covers every non-ignored filesystem entry',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'scan-fabric-'));
  fs.mkdirSync(path.join(root,'src'));
  fs.writeFileSync(path.join(root,'src','a.ts'),'export const a=1;');
  fs.writeFileSync(path.join(root,'README.md'),'x');
  const files=inventory(root);
  assert.equal(files.length,2);
  const plan=buildPlan(files,{changedPaths:['src/a.ts']});
  assertComplete(plan);
  assert.equal(plan.covered,plan.total);
  assert.ok(plan.rows.find(x=>x.path==='src/a.ts').lenses.includes('rust-quality'));
});

test('reconciliation preserves independent sources',()=>{
  const out=reconcile([
    {invariant:'duplicate_authority',source:'typescript-breadth'},
    {invariant:'duplicate_authority',source:'rust-quality'},
    {invariant:'duplicate_authority',source:'policy-reconciler'}
  ]);
  assert.equal(out[0].corroborated,true);
  assert.equal(out[0].sources.length,3);
});

test('lens catalog separates breadth and quality',()=>{
  assert.ok(LENSES.find(x=>x.id==='typescript-breadth' && x.role==='breadth'));
  assert.ok(LENSES.find(x=>x.id==='rust-quality' && x.role==='quality'));
});