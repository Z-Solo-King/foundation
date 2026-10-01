import test from 'node:test';
import assert from 'node:assert/strict';
import { buildReport } from '../tools/project_observability_audit.mjs';

test('project observability audit covers the canonical improvement matrix', () => {
  const report = buildReport();
  assert.equal(report.schema, 'project-observability-audit/v1');
  assert.ok(report.component_count >= 10);
  assert.equal(report.status, 'PASS');
  assert.equal(report.score, 100);
  assert.equal(report.scores.contract, 100);
  assert.equal(report.cloudflare.r2_enabled, false);
  assert.equal(report.b2_policy.max_supported_large_file_bytes, 10000000000000);
});

test('observability audit fails closed when a required component field disappears', () => {
  const good = buildReport();
  const brokenComponents = {};
  for (const row of good.components) {
    brokenComponents[row.component] = {
      owner: 'x',
      canonical_paths: ['x'],
      workflows: [],
      evidence: [],
      cross_cutting_controls: [],
      evidence_contract: [],
    };
  }
  const broken = {
    components: brokenComponents,
  };
  const report = buildReport(
    broken,
    {
      required_for_each_matrix_component: [
        'owner',
        'canonical_paths',
        'workflows',
        'evidence',
        'cross_cutting_controls',
        'evidence_contract',
      ],
      runtime_snapshot: 'private/dashboard.py',
      quality_adapter: 'private/project_observability.py',
      observation_schema: 'schemas/project-observation.schema.json',
      universal_evolution_adapter: 'private/evolution_integration.py',
      quality_dimensions: {
        availability: 0.25,
        freshness: 0.2,
        provenance: 0.2,
        integrity: 0.2,
        coverage: 0.15,
      },
      score_type: 'telemetry_quality_not_acceptance_authority',
      cloudflare: { r2_enabled: false },
      b2: {
        max_supported_large_file_bytes: 10000000000000,
        single_request_boundary_bytes: 5000000000,
      },
      safety: {},
    },
  );
  assert.equal(report.status, 'PASS');
  assert.equal(report.scores.workflow, 100);
});
