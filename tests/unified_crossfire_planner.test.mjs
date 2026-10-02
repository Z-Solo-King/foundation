import assert from 'node:assert/strict';
import test from 'node:test';
import {AI_PROVIDER_STRONG_THRESHOLD,AI_PROVIDER_TARGET,composeRun,planProviderCrossfire} from '../tools/unified_crossfire_planner.mjs';

test('six-provider automation has explicit strength thresholds',()=>{
  assert.equal(AI_PROVIDER_TARGET,6);
  assert.equal(AI_PROVIDER_STRONG_THRESHOLD,5);
  assert.equal(planProviderCrossfire({availableProviders:['a','b','c','d','e','f']}).strength,'full_6');
  assert.equal(planProviderCrossfire({availableProviders:['a','b','c','d','e']}).strength,'strong_5');
});

test('provider shortages are reported rather than simulated',()=>{
  const plan=planProviderCrossfire({availableProviders:['a']});
  assert.equal(plan.strength,'no_result');
  assert.equal(plan.selected_count,1);
  assert.match(plan.rule,/never simulated/);
});

test('composed run preserves complete inventory coverage',()=>{
  const inventory=[{path:'a.py'},{path:'b.ts'},{path:'.github/workflows/x.yml'}];
  const run=composeRun({inventory,changedPaths:['b.ts'],availableProviders:['a','b','c','d','e','f']});
  assert.equal(run.deterministic.coverage_complete,true);
  assert.equal(run.deterministic.lane_plan.assignments_total,3);
  assert.equal(run.domains.length,8);
});
