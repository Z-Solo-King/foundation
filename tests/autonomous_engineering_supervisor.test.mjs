import test from 'node:test';
import assert from 'node:assert/strict';
import { deterministicFallbackPlan, parseState, reconcileChildState, sanitize } from '../tools/autonomous_engineering_supervisor.mjs';

test('mission state parser reads durable issue marker', () => {
  const body = '<!-- autonomous-mission-state:start -->\n```json\n{"schema":"autonomous-mission-state/v1","state":"executing"}\n```\n<!-- autonomous-mission-state:end -->';
  assert.equal(parseState(body).state, 'executing');
});

test('sanitizer removes credential-like values before planner context', () => {
  const value = 'API_KEY=secret123 PRIVATE_KEY=abc SECRET=xyz ordinary';
  const output = sanitize(value);
  assert.equal(output.includes('secret123'), false);
  assert.equal(output.includes('abc'), false);
  assert.equal(output.includes('xyz'), false);
  assert.equal(output.includes('ordinary'), true);
});

test('deterministic fallback creates a bounded component plan', () => {
  const plan = deterministicFallbackPlan({mode:'component_improvement',target_component:'chatbot',open_issues:[],recent_runs:[]});
  assert.equal(plan.mission_type, 'component_improvement');
  assert.equal(plan.target_component, 'chatbot');
  assert.equal(plan.actions[0].workflow, 'live-chatbot-production-smoke.yml');
  assert.deepEqual(plan.actions[0].inputs, {});
});

test('deterministic fallback classifies migration issues', () => {
  const plan = deterministicFallbackPlan({mode:'standard',open_issues:[{title:'mapper migration',body:'polyglot evidence'}],recent_runs:[]});
  assert.equal(plan.mission_type, 'migration');
});


test('deterministic fallback avoids an active matching workflow path', () => {
  const plan = deterministicFallbackPlan({mode:'component_improvement',target_component:'chatbot',open_issues:[],recent_runs:[{path:'.github/workflows/live-chatbot-production-smoke.yml',status:'in_progress',conclusion:null,created_at:new Date().toISOString()}]});
  assert.notEqual(plan.actions[0].workflow, 'live-chatbot-production-smoke.yml');
});

test('completed child run advances execution into verification state', () => {
  const state = { state:'executing', child_runs:[101], last_summary:'running', terminal_reason:null, retriable:true };
  const next = reconcileChildState(state, [{id:101,status:'completed',conclusion:'success'}]);
  assert.equal(next.state, 'verifying');
  assert.equal(next.retriable, true);
});

test('active child run remains executing', () => {
  const state = {state:'executing',child_runs:[101],retriable:true};
  const next = reconcileChildState(state,[{id:101,status:'in_progress',conclusion:null}]);
  assert.equal(next.state,'executing');
});

test('unknown child run does not create false verification', () => {
  const state = {state:'executing',child_runs:[101],retriable:true};
  const next = reconcileChildState(state,[{id:101,status:'unknown',conclusion:'unavailable'}]);
  assert.equal(next.state,'executing');
});

test('deterministic fallback rotates after a workflow reaches its attempt budget', () => {
  const plan = deterministicFallbackPlan({
    mode:'standard',
    open_issues:[{title:'feed recovery',body:'woocommerce'}],
    recent_runs:[],
    workflow_attempts:{'woocommerce-clean-recovery.yml':3},
  });
  assert.notEqual(plan.actions[0].workflow, 'woocommerce-clean-recovery.yml');
});

test('deterministic fallback blocks only when every candidate reached the attempt budget', () => {
  assert.throws(() => deterministicFallbackPlan({
    mode:'standard',
    open_issues:[{title:'feed recovery',body:'woocommerce'}],
    recent_runs:[],
    workflow_attempts:{
      'woocommerce-clean-recovery.yml':3,
      'native-google-feed-hunt.yml':3,
      'woocommerce-identified-family-exhaustive-v5.yml':3,
    },
  }), /fallback_workflow_unavailable/);
});
