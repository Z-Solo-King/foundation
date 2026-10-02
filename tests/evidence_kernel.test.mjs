import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {clamp,positive,stableJson,digestObject,walkFiles,readText,exists,freshnessScore} from '../tools/evidence_kernel.mjs';

test('shared deterministic primitives are stable',()=>{
  assert.equal(clamp(2),1);
  assert.equal(positive(-1,7),7);
  assert.equal(stableJson({b:1,a:2}),'{"a":2,"b":1}');
  assert.equal(digestObject({b:1,a:2}),digestObject({a:2,b:1}));
});

test('shared filesystem helpers work for audit consumers',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'evidence-kernel-'));
  fs.mkdirSync(path.join(root,'nested'));
  fs.writeFileSync(path.join(root,'nested','a.txt'),'hello');
  assert.deepEqual(walkFiles(root),['nested/a.txt']);
  assert.equal(readText(root,'nested/a.txt'),'hello');
  assert.equal(exists(root,'nested/a.txt'),true);
});

test('shared freshness helper is deterministic at boundary',()=>{
  const now=new Date('2026-10-02T10:00:00Z');
  assert.equal(freshnessScore('2026-10-02T09:59:00Z',120000,now),1);
  assert.equal(freshnessScore('2026-10-02T09:55:00Z',120000,now),0.4);
});
