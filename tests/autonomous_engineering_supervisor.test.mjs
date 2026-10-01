import test from 'node:test';
import assert from 'node:assert/strict';
import { deterministicFallbackPlan, parseState, sanitize } from '../tools/autonomous_engineering_supervisor.mjs';

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
