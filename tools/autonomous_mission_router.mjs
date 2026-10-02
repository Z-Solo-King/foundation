import fs from 'node:fs';

const IMPROVEMENT_MATRIX_URL = new URL('../docs/PROJECT_IMPROVEMENT_MATRIX.json', import.meta.url);
export const PROJECT_IMPROVEMENT_MATRIX = JSON.parse(fs.readFileSync(IMPROVEMENT_MATRIX_URL, 'utf8'));
export const IMPROVEMENT_COMPONENTS = Object.keys(PROJECT_IMPROVEMENT_MATRIX.components);
const COMPONENT_WORKFLOWS = Object.fromEntries(IMPROVEMENT_COMPONENTS.map((component) => [component, PROJECT_IMPROVEMENT_MATRIX.components[component].workflows]));

export const MISSION_WORKFLOWS = {
  migration: ['polyglot-migration-review.yml', 'open-issue-polyglot-deep-scan.yml', 'hybrid-language-pilots.yml'],
  feed_recovery: ['woocommerce-clean-recovery.yml', 'native-google-feed-hunt.yml', 'woocommerce-identified-family-exhaustive-v5.yml'],
  nightly_research: ['nightly-multi-agent-research-v3.yml'],
  audit: ['exhaustive-six-lane-audit.yml', 'cross-repository-contract-drift.yml'],
  runtime_reconciliation: ['provider-fleet-runtime-state.yml', 'live-ai-provider-crossfire.yml', 'nightly-invariants.yml', 'operations-centralized-validation.yml'],
  governance_sweep: [
    'repository-hygiene.yml',
    'repository-hygiene-autofix.yml',
    'family-hygiene-sync.yml',
    'family-integrity-gate.yml',
    'family-full-coverage.yml',
    'cross-repository-contract-drift.yml',
    'exhaustive-six-lane-audit.yml',
    'polyglot-governance-audit.yml',
    'polyglot-migration-review.yml',
    'hybrid-language-pilots.yml',
    'provider-fleet-runtime-state.yml',
    'live-ai-provider-crossfire.yml',
    'browser-engine-runtime-evidence.yml',
    'live-chatbot-production-smoke.yml',
    'live-extractor-benchmark.yml',
    'live-nightly-research-canary.yml',
    'nightly-multi-agent-research-v3.yml',
    'nightly-invariants.yml',
    'operations-centralized-validation.yml',
  ],
  component_improvement: [...new Set(Object.values(COMPONENT_WORKFLOWS).flat())],
};
export const FORBIDDEN_WORKFLOWS = new Set(['heroic-ai-production-release.yml']);

const FINDING_DISPOSITIONS = new Set(['none', 'comment_existing', 'create_issue']);
const FINDING_SEVERITIES = new Set(['info', 'warning', 'error']);
const FINDING_EVIDENCE_RE = /^(?:issue|run|audit|contract):[A-Za-z0-9._:-]{1,100}$/;

function stripFence(value) {
  const text = String(value ?? '').trim();
  const match = text.match(/^```(?:json)?\s*([\s\S]*?)\s*```$/i);
  return match ? match[1].trim() : text;
}

export function parsePlanDocument(document) {
  const raw = typeof document === 'string'
    ? document
    : document?.response?.text ?? document?.plan ?? document;
  if (raw && typeof raw === 'object') return raw;
  return JSON.parse(stripFence(raw));
}

function normalizeFinding(finding, index) {
  if (!finding || typeof finding !== 'object') throw new Error(`invalid finding ${index}`);
  const id = String(finding.id || `f${index + 1}`).trim();
  if (!/^f[0-9a-z._:-]{1,63}$/i.test(id)) throw new Error(`invalid finding id: ${id}`);
  const severity = String(finding.severity || 'info').trim();
  if (!FINDING_SEVERITIES.has(severity)) throw new Error(`invalid finding severity: ${severity}`);
  const disposition = String(finding.disposition || 'none').trim();
  if (!FINDING_DISPOSITIONS.has(disposition)) throw new Error(`invalid finding disposition: ${disposition}`);
  const title = String(finding.title || '').trim();
  const summary = String(finding.summary || '').trim();
  if (!title || title.length > 180) throw new Error(`invalid finding title: ${id}`);
  if (!summary || summary.length > 2000) throw new Error(`invalid finding summary: ${id}`);
  const evidence = Array.isArray(finding.evidence_refs) ? finding.evidence_refs.map((item) => String(item).trim()).filter(Boolean) : [];
  if (evidence.length < 1 || evidence.length > 3 || evidence.some((item) => !FINDING_EVIDENCE_RE.test(item))) throw new Error(`invalid finding evidence: ${id}`);
  const issueNumber = finding.issue_number == null ? null : Number(finding.issue_number);
  if (issueNumber !== null && (!Number.isInteger(issueNumber) || issueNumber < 1)) throw new Error(`invalid finding issue number: ${id}`);
  if (disposition === 'comment_existing' && issueNumber === null) throw new Error(`comment_existing finding requires issue_number: ${id}`);
  if (disposition === 'create_issue' && issueNumber !== null) throw new Error(`create_issue finding cannot target issue_number: ${id}`);
  if (disposition === 'none' && issueNumber !== null) throw new Error(`report-only finding cannot target issue_number: ${id}`);
  return {
    id, severity, disposition, title: title.slice(0, 180), summary: summary.slice(0, 2000),
    evidence_refs: evidence, issue_number: issueNumber,
  };
}

export function validatePlan(plan) {
  if (!plan || typeof plan !== 'object') throw new Error('plan must be an object');
  if (plan.schema !== 'autonomous-mission-plan/v1') throw new Error('invalid schema');
  if (!Object.hasOwn(MISSION_WORKFLOWS, plan.mission_type)) throw new Error('unsupported mission type');
  if (typeof plan.summary !== 'string' || !plan.summary.trim()) throw new Error('summary is required');
  if (plan.mission_type === 'component_improvement' && (typeof plan.target_component !== 'string' || !IMPROVEMENT_COMPONENTS.includes(plan.target_component))) throw new Error('component improvement requires a valid target_component');
  if (!['planned','executing','verifying','retrying','blocked','complete'].includes(plan.next_state)) throw new Error('invalid next_state');
  if (plan.terminal !== null && plan.terminal !== 'complete' && plan.terminal !== 'blocked') throw new Error('invalid terminal state');
  if (!Array.isArray(plan.actions) || plan.actions.length > 3) throw new Error('invalid action count');
  if (plan.terminal === null && plan.actions.length === 0) throw new Error('non-terminal plan requires an action');
  if (plan.terminal !== null && plan.actions.length !== 0) throw new Error('terminal plan cannot contain actions');
  const ids = new Set();
  const workflows = new Set();
  const rawFindings = plan.findings == null ? [] : plan.findings;
  if (!Array.isArray(rawFindings) || rawFindings.length > 5) throw new Error('invalid finding count');
  const findingIds = new Set();
  const findings = rawFindings.map((finding, index) => {
    const normalized = normalizeFinding(finding, index);
    if (findingIds.has(normalized.id)) throw new Error(`duplicate finding id: ${normalized.id}`);
    findingIds.add(normalized.id);
    return normalized;
  });
  for (const action of plan.actions) {
    if (!action || action.kind !== 'dispatch_workflow') throw new Error('unsupported action kind');
    if (typeof action.id !== 'string' || !/^a[0-9a-z._:-]{1,63}$/i.test(action.id)) throw new Error('invalid action id');
    if (ids.has(action.id)) throw new Error('duplicate action id');
    ids.add(action.id);
    if (workflows.has(action.workflow)) throw new Error(`duplicate workflow action: ${action.workflow}`);
    workflows.add(action.workflow);
    if (!MISSION_WORKFLOWS[plan.mission_type].includes(action.workflow) || FORBIDDEN_WORKFLOWS.has(action.workflow)) throw new Error(`workflow not allowlisted: ${action.workflow}`);
    if (plan.mission_type === 'component_improvement' && !COMPONENT_WORKFLOWS[plan.target_component].includes(action.workflow)) throw new Error(`workflow not allowlisted for component: ${plan.target_component}`);
    if (!action.inputs || Object.keys(action.inputs).length !== 0) throw new Error('workflow inputs must be empty');
    if (typeof action.reason !== 'string' || !action.reason.trim()) throw new Error('action reason is required');
    if (!['none','transient_only','bounded'].includes(action.retry_policy)) throw new Error('invalid retry policy');
  }
  return {
    schema: plan.schema,
    mission_type: plan.mission_type,
    target_component: plan.target_component == null ? null : plan.target_component,
    summary: plan.summary.trim().slice(0, 2000),
    terminal: plan.terminal,
    actions: plan.actions.map((action) => ({id:action.id,kind:action.kind,workflow:action.workflow,inputs:{},reason:action.reason.trim().slice(0,2000),retry_policy:action.retry_policy})),
    findings,
    next_state: plan.next_state,
    stop_reason: plan.stop_reason == null ? null : String(plan.stop_reason).slice(0,2000),
  };
}

if (process.argv[1] && process.argv[1].endsWith('autonomous_mission_router.mjs')) {
  const input = fs.readFileSync(process.argv[2] || 0, 'utf8');
  process.stdout.write(JSON.stringify(validatePlan(parsePlanDocument(input)), null, 2) + '\n');
}