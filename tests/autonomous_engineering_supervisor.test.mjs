import test from 'node:test';
import assert from 'node:assert/strict';
import { validatePlan } from './autonomous_mission_router.mjs';

test('autonomous supervisor contract stays compatible with router', () => {
  const plan = {schema:'autonomous-mission-plan/v1',mission_type:'audit',summary:'run audit',terminal:null,
    actions:[{id:'a1',kind:'dispatch_workflow',workflow:'exhaustive-six-lane-audit.yml',inputs:{},reason:'collect evidence',retry_policy:'bounded'}],
    next_state:'executing',stop_reason:null};
  const normalized = validatePlan(plan);
  assert.equal(normalized.actions.length, 1);
  assert.equal(normalized.actions[0].inputs && Object.keys(normalized.actions[0].inputs).length, 0);
});