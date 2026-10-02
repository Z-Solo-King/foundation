import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {assertPlanSafe, classifyPaths, planVerification, scanFoundation} from '../tools/verification_fabric.mjs';

test('classifies cross-cutting paths into multiple domains', () => {
  const domains = classifyPaths([
    'extractor_mapper/extraction/generic.py',
    'private/chatbot/provider_runtime.py',
    '.github/workflows/required-pr-checks.yml',
  ]);
  assert(domains.includes('extractor'));
  assert(domains.includes('chatbot'));
  assert(domains.includes('provider'));
  assert(domains.includes('workflows'));
});

test('verification plan deduplicates canonical workflows', () => {
  const plan = planVerification({domains:['extractor','mapper','security'],mode:'pr'});
  assertPlanSafe(plan);
  const workflows = plan.checks.map(x=>x.workflow);
  assert.equal(workflows.length,new Set(workflows).size);
  assert(workflows.includes('.github/workflows/extractor-surface-governance.yml'));
});

test('scanner catches unpinned action and secret-like literals as findings', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(),'verification-fabric-'));
  fs.mkdirSync(path.join(root,'.github','workflows'),{recursive:true});
  fs.writeFileSync(path.join(root,'.github','workflows','x.yml'),'name: x\non:\n  push:\njobs:\n  x:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v7\n');
  fs.writeFileSync(path.join(root,'REPOSITORY_MAP.json'),'{}\n');
  for (const f of ['docs/CODE_OWNERSHIP_AND_PLACEMENT.md','docs/CURRENT_SOURCE_OF_TRUTH.md','polyglot/REGISTRY.json','.github/workflows/autonomous-engineering-supervisor.yml']) {
    fs.mkdirSync(path.dirname(path.join(root,f)),{recursive:true});
    fs.writeFileSync(path.join(root,f),'ok\n');
  }
  fs.writeFileSync(path.join(root,'leak.js'),'const x = "sk-abcdefghijklmnopqrstuvwxyz123456";\n');
  const report = scanFoundation(root);
  assert(report.findings.some(f=>f.kind==='unpinned_action'));
  assert(report.findings.some(f=>f.kind==='secret_like_literal'));
});

test('scanner is non-authoritative for warnings', () => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(),'verification-fabric-'));
  for (const f of ['REPOSITORY_MAP.json','docs/CODE_OWNERSHIP_AND_PLACEMENT.md','docs/CURRENT_SOURCE_OF_TRUTH.md','polyglot/REGISTRY.json','.github/workflows/autonomous-engineering-supervisor.yml']) {
    fs.mkdirSync(path.dirname(path.join(root,f)),{recursive:true});
    fs.writeFileSync(path.join(root,f),'ok\n');
  }
  const report = scanFoundation(root);
  assert.equal(report.findings.filter(f=>f.severity==='critical').length,0);
});
