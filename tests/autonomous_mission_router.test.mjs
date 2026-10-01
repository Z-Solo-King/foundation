import test from 'node:test';
import assert from 'node:assert/strict';
import { parsePlanDocument, validatePlan } from '../tools/autonomous_mission_router.mjs';

const base = (overrides = {}) => ({
  schema: 'autonomous-mission-plan/v1',
  mission_type: 'nightly_research',
  summary: 'continue nightly research',
  terminal: null,
  actions: [{id:'a1',kind:'dispatch_workflow',workflow:'nightly-multi-agent-research-v3.yml',inputs:{},reason:'continue canonical research',retry_policy:'bounded'}],
  next_state: 'executing',
  stop_reason: null,
  ...overrides,
});

test('accepts allowlisted workflow', () => {
  assert.equal(validatePlan(base()).actions[0].workflow, 'nightly-multi-agent-research-v3.yml');
});

test('rejects production workflow', () => {
  assert.throws(() => validatePlan(base({mission_type:'audit',actions:[{id:'a1',kind:'dispatch_workflow',workflow:'heroic-ai-production-release.yml',inputs:{},reason:'release',retry_policy:'none'}]})), /allowlisted/);
});

test('rejects non-empty workflow inputs', () => {
  assert.throws(() => validatePlan(base({actions:[{...base().actions[0],inputs:{auto_fix:true}}]})), /inputs must be empty/);
});

test('accepts a component-scoped improvement plan', () => {
  const result = validatePlan(base({mission_type:'component_improvement',target_component:'chatbot',actions:[{id:'a1',kind:'dispatch_workflow',workflow:'live-chatbot-production-smoke.yml',inputs:{},reason:'exercise chatbot runtime evidence',retry_policy:'bounded'}]}));
  assert.equal(result.target_component, 'chatbot');
});

test('accepts a blocked terminal plan', () => {
  const result = validatePlan(base({terminal:'blocked',actions:[],next_state:'blocked',stop_reason:'requires admin'}));
  assert.equal(result.terminal, 'blocked');
});

test('parses fenced JSON', () => {
  const result = parsePlanDocument('\`\`\`json\n' + JSON.stringify(base()) + '\n\`\`\`');
  assert.equal(result.schema, 'autonomous-mission-plan/v1');
});

test('rejects duplicate workflow actions even with distinct IDs', () => {
  const action = base().actions[0];
  assert.throws(() => validatePlan(base({actions:[action,{...action,id:'a2'}]})), /duplicate workflow action/);
});

test('accepts three distinct migration cross-fire actions', () => {
  const result = validatePlan(base({
    mission_type:'migration',
    summary:'run migration cross-fire lanes',
    actions:[
      {id:'a1',kind:'dispatch_workflow',workflow:'polyglot-migration-review.yml',inputs:{},reason:'five-lane migration evidence',retry_policy:'bounded'},
      {id:'a2',kind:'dispatch_workflow',workflow:'open-issue-polyglot-deep-scan.yml',inputs:{},reason:'independent open-issue deep scan',retry_policy:'bounded'},
      {id:'a3',kind:'dispatch_workflow',workflow:'hybrid-language-pilots.yml',inputs:{},reason:'candidate-specific migration pilots',retry_policy:'bounded'},
    ],
  }));
  assert.equal(result.actions.length, 3);
});
