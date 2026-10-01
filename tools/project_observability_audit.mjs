import fs from 'node:fs';

const ROOT = new URL('..', import.meta.url);
const MATRIX_URL = new URL('./docs/PROJECT_IMPROVEMENT_MATRIX.json', ROOT);
const CONTRACT_URL = new URL('./docs/PROJECT_OBSERVABILITY_CONTRACT.json', ROOT);
const MAP_URL = new URL('./docs/AI_SYSTEM_MAP.json', ROOT);
const MATRIX = JSON.parse(fs.readFileSync(MATRIX_URL, 'utf8'));
const CONTRACT = JSON.parse(fs.readFileSync(CONTRACT_URL, 'utf8'));
const MAP = JSON.parse(fs.readFileSync(MAP_URL, 'utf8'));

const REQUIRED_CONTROLS = new Set(['audit', 'quality', 'learning', 'ai_automation']);
const REQUIRED_FIELDS = CONTRACT.required_for_each_matrix_component;

function exists(relativePath) {
  return fs.existsSync(new URL(relativePath, ROOT));
}

function navigationMapErrors(matrix, map) {
  const errors = [];
  if (map?.schema_version !== 'ai-system-map/v1') {
    errors.push('ai_map:invalid_schema');
    return errors;
  }

  const matrixComponents = new Set(Object.keys(matrix.components ?? {}));
  const mapComponents = new Set(Object.keys(map.components ?? {}));
  for (const name of matrixComponents) {
    if (!mapComponents.has(name)) errors.push('ai_map:missing_component:' + name);
    const entry = map.components?.[name];
    if (!entry || !Array.isArray(entry.paths) || entry.paths.length === 0) {
      errors.push('ai_map:missing_paths:' + name);
    }
    if (!entry || !Array.isArray(entry.task_families) || entry.task_families.length === 0) {
      errors.push('ai_map:missing_task_families:' + name);
    }
    if (!entry?.next) errors.push('ai_map:missing_next:' + name);
  }
  for (const name of mapComponents) {
    if (!matrixComponents.has(name)) errors.push('ai_map:extra_component:' + name);
  }

  const directoryComponents = new Set(
    (map.functional_planes ?? []).flatMap((plane) => plane.components ?? [])
  );
  for (const name of matrixComponents) {
    if (!directoryComponents.has(name)) errors.push('ai_map:not_reachable_from_functional_plane:' + name);
  }

  if (map.navigation_rules?.categories_may_overlap !== true) {
    errors.push('ai_map:category_overlap_rule_missing');
  }
  if (map.navigation_rules?.unknown_is_not_zero !== true) {
    errors.push('ai_map:unknown_state_rule_missing');
  }
  if (map.navigation_rules?.ai_output_is_not_evidence_authority !== true) {
    errors.push('ai_map:ai_authority_rule_missing');
  }
  if (map.forbidden_routes?.some((item) => item.route === 'Cloudflare R2') === false) {
    errors.push('ai_map:r2_exclusion_missing');
  }
  return errors;
}

export function buildReport(matrix = MATRIX, contract = CONTRACT, map = MAP) {
  const components = Object.entries(matrix.components ?? {});
  const errors = [];
  const rows = [];

  for (const [name, item] of components) {
    const missingFields = REQUIRED_FIELDS.filter((field) => !(field in item));
    const missingWorkflows = (item.workflows ?? []).filter(
      (workflow) => !exists('./.github/workflows/' + workflow)
    );
    const controls = new Set(item.cross_cutting_controls ?? []);
    const controlComplete = [...REQUIRED_CONTROLS].every((control) => controls.has(control));

    const row = {
      component: name,
      registry_complete: missingFields.length === 0,
      workflow_complete: missingWorkflows.length === 0,
      control_complete: controlComplete,
      missing_fields: missingFields,
      missing_workflows: missingWorkflows,
    };
    rows.push(row);

    if (missingFields.length) errors.push(name + ':missing_fields:' + missingFields.join(','));
    if (missingWorkflows.length) errors.push(name + ':missing_workflows:' + missingWorkflows.join(','));
    if (!controlComplete) errors.push(name + ':cross_cutting_controls_drift');
  }

  const navigationErrors = navigationMapErrors(matrix, map);
  errors.push(...navigationErrors);

  const total = Math.max(1, rows.length);
  const registryScore = 100 * rows.filter((row) => row.registry_complete).length / total;
  const workflowScore = 100 * rows.filter((row) => row.workflow_complete).length / total;
  const controlScore = 100 * rows.filter((row) => row.control_complete).length / total;
  const navigationScore = navigationErrors.length ? 0 : 100;

  const requiredAnchors = [
    contract.runtime_snapshot,
    contract.quality_adapter,
    contract.observation_schema,
    contract.universal_evolution_adapter,
  ];
  const missingAnchors = requiredAnchors.filter((path) => !exists('./' + path));
  if (missingAnchors.length) errors.push('contract:missing_anchors:' + missingAnchors.join(','));

  if (contract.cloudflare?.r2_enabled !== false) errors.push('cloudflare_r2:must_remain_excluded');
  if (contract.b2?.max_supported_large_file_bytes !== 10000000000000) errors.push('b2:large_file_ceiling_policy_missing');
  if (contract.b2?.single_request_boundary_bytes !== 5000000000) errors.push('b2:single_request_boundary_policy_missing');
  if (contract.quality_dimensions == null || Math.abs(
    Object.values(contract.quality_dimensions).reduce((a, b) => a + b, 0) - 1
  ) > 1e-9) errors.push('quality_dimensions:must_sum_to_one');

  const score = Math.round((
    registryScore * 0.20 +
    workflowScore * 0.20 +
    controlScore * 0.20 +
    navigationScore * 0.20 +
    (errors.length ? 0 : 100) * 0.20
  ) * 100) / 100;

  return {
    schema: 'project-observability-audit/v1',
    status: errors.length === 0 ? 'PASS' : 'FAIL',
    score,
    scale: '0-100',
    score_type: contract.score_type,
    component_count: rows.length,
    scores: {
      registry: Math.round(registryScore * 100) / 100,
      workflow: Math.round(workflowScore * 100) / 100,
      cross_cutting_controls: Math.round(controlScore * 100) / 100,
      navigation: navigationScore,
      contract: errors.length ? 0 : 100,
    },
    components: rows,
    cloudflare: contract.cloudflare,
    b2_policy: contract.b2,
    navigation: {
      schema: map.schema_version,
      directory: 'docs/AI_SYSTEM_DIRECTORY.md',
      map: 'docs/AI_SYSTEM_MAP.json',
      reachable_component_count: Object.keys(map.components ?? {}).length,
    },
    errors,
    safety: contract.safety,
  };
}

if (import.meta.url === 'file://' + process.argv[1]) {
  const report = buildReport();
  process.stdout.write(JSON.stringify(report, null, 2) + '\n');
  if (process.env.GITHUB_STEP_SUMMARY) {
    const summary = [
      '### Project observability audit',
      '',
      'Status: **' + report.status + '**',
      'Control/observability coverage score: **' + report.score + '/100**',
      'Components: **' + report.component_count + '**',
      'Navigation coverage: **' + report.scores.navigation + '/100**',
      'Workflow coverage: **' + report.scores.workflow + '/100**',
      'Contract coverage: **' + report.scores.contract + '/100**',
      '',
      report.errors.length ? 'Errors: ' + report.errors.length : 'Errors: 0',
    ].join('\n');
    fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY, summary + '\n');
  }
  process.exitCode = report.status === 'PASS' ? 0 : 1;
}
