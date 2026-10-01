import test from 'node:test';
import assert from 'node:assert/strict';
import { IMPROVEMENT_COMPONENTS, PROJECT_IMPROVEMENT_MATRIX, MISSION_WORKFLOWS, validatePlan } from '../tools/autonomous_mission_router.mjs';

test('matrix covers major project components', () => {
  const expected = ['chatbot','extractor','mapper','research','provider_fleet','runtime_governance','cloudflare_runtime','storage_b2','security_ci','feed_recovery'];
  assert.equal(PROJECT_IMPROVEMENT_MATRIX.schema, 'project-improvement-matrix/v1');
  for (const component of expected) {
    const entry = PROJECT_IMPROVEMENT_MATRIX.components[component];
    assert.ok(entry); assert.ok(entry.workflows.length); assert.ok(entry.ai_task_families.length);
  }
  assert.deepEqual([...IMPROVEMENT_COMPONENTS].sort(), [...expected].sort());
});

test('autonomous task execution is disabled for matrix workflows', () => {
  assert.throws(() => validatePlan({
    schema:'autonomous-mission-plan/v1',
    mission_type:'component_improvement',
    target_component:'chatbot',
    summary:'x',
    terminal:null,
    actions:[{id:'a1',kind:'dispatch_workflow',workflow:'live-chatbot-production-smoke.yml',inputs:{},reason:'test',retry_policy:'none'}],
    next_state:'executing',
    stop_reason:null
  }), /autonomous task workflow execution is disabled/);
});

test('component plan cannot cross into another component', () => {
  assert.throws(() => validatePlan({schema:'autonomous-mission-plan/v1',mission_type:'component_improvement',target_component:'chatbot',summary:'x',terminal:null,actions:[{id:'a1',kind:'dispatch_workflow',workflow:'provider-fleet-runtime-state.yml',inputs:{},reason:'wrong component',retry_policy:'none'}],next_state:'executing',stop_reason:null}), /autonomous task workflow execution is disabled/);
});
