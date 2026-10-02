import test from 'node:test';
import assert from 'node:assert/strict';
import { buildAdaptivePriority, normalizeFinding, reconcileFindings } from '../tools/governance_finding_contract.mjs';

test('normalizes severity into risk, evidence, and mutation policy', () => {
  const f = normalizeFinding({ lane: 'provider_runtime', category: 'provider', severity: 'critical', code: 'provider_probe_missing', paths: ['tools/x.py'] });
  assert.equal(f.risk_class, 'critical');
  assert.equal(f.evidence_level, 'L2');
  assert.equal(f.mutation_policy, 'blocked_until_verified');
  assert.match(f.dedupe_key, /^[0-9a-f]{20}$/);
});

test('deduplicates repeated findings without losing strongest evidence', () => {
  const a = { lane: 'security', category: 'auth', severity: 'attention', code: 'x', paths: ['a'] };
  const b = { lane: 'security', category: 'auth', severity: 'attention', code: 'x', paths: ['a'] , evidence_level:'L3'};
  const out = reconcileFindings([{findings:[a]}, {findings:[b]}]);
  assert.equal(out.length, 1);
  assert.equal(out[0].evidence_level, 'L3');
});

test('adaptive priority increases lanes tied to material findings', () => {
  const lanes = [
    {id:'provider_runtime', family:'provider_runtime', prior_yield:0.5},
    {id:'maps_docs_policy', family:'maps_docs_policy', prior_yield:0.8},
  ];
  const out = buildAdaptivePriority([{lane:'provider_runtime', risk_class:'critical'}], lanes);
  assert.equal(out[0].id, 'provider_runtime');
  assert.ok(out[0].priority_score > out[1].priority_score);
});
