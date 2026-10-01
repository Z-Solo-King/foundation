import fs from 'node:fs';

export const MISSION_WORKFLOWS = {
  migration: ['polyglot-migration-review.yml', 'open-issue-polyglot-deep-scan.yml'],
  feed_recovery: ['woocommerce-clean-recovery.yml', 'native-google-feed-hunt.yml', 'woocommerce-identified-family-exhaustive-v5.yml'],
  nightly_research: ['nightly-multi-agent-research-v3.yml'],
  audit: ['exhaustive-six-lane-audit.yml', 'cross-repository-contract-drift.yml'],
  runtime_reconciliation: ['provider-fleet-runtime-state.yml', 'nightly-invariants.yml', 'operations-centralized-validation.yml'],
};
export const FORBIDDEN_WORKFLOWS = new Set(['heroic-ai-production-release.yml']);

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

export function validatePlan(plan) {
  if (!plan || typeof plan !== 'object') throw new Error('plan must be an object');
  if (plan.schema !== 'autonomous-mission-plan/v1') throw new Error('invalid schema');
  if (!Object.hasOwn(MISSION_WORKFLOWS, plan.mission_type)) throw new Error('unsupported mission type');
  if (typeof plan.summary !== 'string' || !plan.summary.trim()) throw new Error('summary is required');
  if (!['planned','executing','verifying','retrying','blocked','complete'].includes(plan.next_state)) throw new Error('invalid next_state');
  if (plan.terminal !== null && plan.terminal !== 'complete' && plan.terminal !== 'blocked') throw new Error('invalid terminal state');
  if (!Array.isArray(plan.actions) || plan.actions.length > 3) throw new Error('invalid action count');
  if (plan.terminal === null && plan.actions.length === 0) throw new Error('non-terminal plan requires an action');
  if (plan.terminal !== null && plan.actions.length !== 0) throw new Error('terminal plan cannot contain actions');
  const ids = new Set();
  for (const action of plan.actions) {
    if (!action || action.kind !== 'dispatch_workflow') throw new Error('unsupported action kind');
    if (typeof action.id !== 'string' || !/^a[0-9a-z._:-]{1,63}$/i.test(action.id)) throw new Error('invalid action id');
    if (ids.has(action.id)) throw new Error('duplicate action id');
    ids.add(action.id);
    if (!MISSION_WORKFLOWS[plan.mission_type].includes(action.workflow) || FORBIDDEN_WORKFLOWS.has(action.workflow)) throw new Error(`workflow not allowlisted: ${action.workflow}`);
    if (!action.inputs || Object.keys(action.inputs).length !== 0) throw new Error('workflow inputs must be empty');
    if (typeof action.reason !== 'string' || !action.reason.trim()) throw new Error('action reason is required');
    if (!['none','transient_only','bounded'].includes(action.retry_policy)) throw new Error('invalid retry policy');
  }
  return {
    schema: plan.schema,
    mission_type: plan.mission_type,
    summary: plan.summary.trim().slice(0, 2000),
    terminal: plan.terminal,
    actions: plan.actions.map((action) => ({id:action.id,kind:action.kind,workflow:action.workflow,inputs:{},reason:action.reason.trim().slice(0,2000),retry_policy:action.retry_policy})),
    next_state: plan.next_state,
    stop_reason: plan.stop_reason == null ? null : String(plan.stop_reason).slice(0,2000),
  };
}

if (process.argv[1] && process.argv[1].endsWith('autonomous_mission_router.mjs')) {
  const input = fs.readFileSync(process.argv[2] || 0, 'utf8');
  process.stdout.write(JSON.stringify(validatePlan(parsePlanDocument(input)), null, 2) + '\n');
}