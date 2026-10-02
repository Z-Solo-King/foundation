import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';
import {inventory,buildPlan,assertComplete,LENSES} from '../tools/unified_scan_fabric.mjs';
import {composeRun,planProviderCrossfire} from '../tools/unified_crossfire_planner.mjs';
test('inventory coverage and deep-lens assignment',()=>{const root=fs.mkdtempSync(path.join(os.tmpdir(),'fabric-'));fs.mkdirSync(path.join(root,'src'));fs.writeFileSync(path.join(root,'src','a.ts'),'x');fs.writeFileSync(path.join(root,'README.md'),'x');const files=inventory(root);const plan=buildPlan(files,{changedPaths:['src/a.ts']});assertComplete(plan);assert.equal(plan.covered,plan.total);assert.equal(plan.rows.find(x=>x.path==='src/a.ts').priority,'deep');assert.ok(plan.rows.find(x=>x.path==='src/a.ts').lenses.includes('rust-quality'));});
test('six-provider evidence thresholds and shortage semantics',()=>{assert.equal(planProviderCrossfire({availableProviders:['a','b','c','d','e','f']}).strength,'full_6');assert.equal(planProviderCrossfire({availableProviders:['a','b','c','d','e']}).strength,'strong_5');const short=planProviderCrossfire({availableProviders:['a']});assert.equal(short.strength,'no_result');assert.match(short.rule,/never simulated/);});
test('composed run separates deterministic and AI layers',()=>{const run=composeRun({inventory:[{path:'a.py'}],availableProviders:['a','b','c','d','e','f']});assert.equal(run.deterministic.coverage_complete,true);assert.equal(run.ai_crossfire.selected_count,6);assert.equal(LENSES.length,6);});
