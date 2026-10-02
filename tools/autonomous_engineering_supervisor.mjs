import crypto from 'node:crypto';
import fs from 'node:fs';
import { pathToFileURL } from 'node:url';
import { IMPROVEMENT_COMPONENTS, MISSION_WORKFLOWS, PROJECT_IMPROVEMENT_MATRIX, validatePlan } from './autonomous_mission_router.mjs';

const owner = process.env.GITHUB_REPOSITORY?.split('/')[0];
const repo = process.env.GITHUB_REPOSITORY?.split('/')[1];
const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN;
const workerUrl = (process.env.PUBLIC_WORKER_URL || 'https://ai-cio.pages.dev').replace(/\/$/, '');
const dryRun = process.env.DRY_RUN === 'true';
const maxCycles = Number(process.env.MAX_PLANNING_CYCLES || 6);
const maxWorkflowAttempts = Number(process.env.MAX_WORKFLOW_ATTEMPTS || 3);

async function github(path, options = {}) {
  const response = await fetch(`https://api.github.com${path}`, {
    method: options.method || 'GET',
    headers: {
      'Accept': 'application/vnd.github+json',
      'Authorization': `Bearer ${token}`,
      'X-GitHub-Api-Version': '2022-11-28',
      ...(options.body ? {'Content-Type':'application/json'} : {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });
  const text = await response.text();
  let body = null;
  try { body = text ? JSON.parse(text) : null; } catch { body = {raw:text}; }
  if (!response.ok) throw new Error(`GitHub ${response.status} ${path}: ${JSON.stringify(body).slice(0,1200)}`);
  return body;
}

export function sanitize(value) {
  return String(value ?? '')
    .replace(/(?:API[_ -]?KEY|PRIVATE[_ -]?KEY|ACCESS[_ -]?TOKEN|AUTH[_ -]?TOKEN|SECRET)\s*[:=]\s*[^\s,;]+/gi, '[REDACTED]')
    .replace(/-----BEGIN [^-]+-----[\s\S]*?-----END [^-]+-----/g, '[REDACTED_KEY]')
    .replace(/\s+/g, ' ')
    .slice(0, 1200);
}

export function parseState(body) {
  const match = String(body || '').match(/<!-- autonomous-mission-state:start -->\s*```json\s*([\s\S]*?)\s*```\s*<!-- autonomous-mission-state:end -->/);
  if (!match) return null;
  try { return JSON.parse(match[1]); } catch { return null; }
}

export function stateBlock(state) {
  return `<!-- autonomous-mission-state:start -->\n\`\`\`json\n${JSON.stringify(state, null, 2)}\n\`\`\`\n<!-- autonomous-mission-state:end -->`;
}

function missionBody(state, summary, contextNote = '') {
  return ['# Autonomous engineering mission', '', `## Current action\n${summary}`, contextNote, '', stateBlock(state), ''].filter(Boolean).join('\n');
}

async function listIssues(state = 'open', limit = 50) {
  return github(`/repos/${owner}/${repo}/issues?state=${state}&per_page=${limit}&sort=updated&direction=desc`);
}

async function listRuns(limit = 40) {
  const data = await github(`/repos/${owner}/${repo}/actions/runs?per_page=${limit}`);
  return data.workflow_runs || [];
}

async function readRun(id) {
  return github(`/repos/${owner}/${repo}/actions/runs/${id}`);
}

async function updateIssue(number, patch) {
  return github(`/repos/${owner}/${repo}/issues/${number}`, {method:'PATCH', body:patch});
}

async function addIssueComment(number, body) {
  return github(`/repos/${owner}/${repo}/issues/${number}/comments`, {method:'POST', body:{body}});
}

function loadGovernanceAudit() {
  const filename = process.env.GOVERNANCE_AUDIT_FILE;
  if (!filename) return null;
  try {
    const raw = fs.readFileSync(filename, 'utf8');
    if (raw.length > 16000) throw new Error('governance audit context too large');
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === 'object' ? parsed : null;
  } catch (error) {
    console.warn(`governance audit context unavailable: ${String(error).slice(0,240)}`);
    return null;
  }
}

function findingFingerprint(finding) {
  return crypto.createHash('sha256').update(JSON.stringify({title:finding.title,summary:finding.summary,evidence_refs:finding.evidence_refs})).digest('hex').slice(0,16);
}

async function applyFindings({findings, missionIssue, openIssues}) {
  if (!Array.isArray(findings) || !findings.length) return [];
  const applied = [];
  for (const finding of findings) {
    const fingerprint = findingFingerprint(finding);
    const marker = `<!-- autonomous-governance-finding:${fingerprint} -->`;
    const evidence = finding.evidence_refs.join(', ');
    const message = `${marker}\n### ${finding.severity.toUpperCase()} — ${sanitize(finding.title)}\n${sanitize(finding.summary)}\n\nEvidence references: ${evidence}`;
    if (finding.disposition === 'comment_existing') {
      const comments = await github(`/repos/${owner}/${repo}/issues/${finding.issue_number}/comments?per_page=100`);
      if (!Array.isArray(comments) || !comments.some((comment) => String(comment.body || '').includes(marker))) {
        await addIssueComment(finding.issue_number, message);
        applied.push({id:finding.id, disposition:'comment_existing', issue_number:finding.issue_number, fingerprint});
      }
    } else if (finding.disposition === 'create_issue') {
      const duplicate = openIssues.find((issue) => String(issue.body || '').includes(marker));
      if (duplicate) {
        applied.push({id:finding.id, disposition:'existing_issue', issue_number:duplicate.number, fingerprint});
        continue;
      }
      const created = await github(`/repos/${owner}/${repo}/issues`, {method:'POST', body:{
        title:`[ai-governance] ${sanitize(finding.title).slice(0,160)}`,
        body:`# Autonomous governance finding\n\n${message}\n\n**Policy:** AI output is candidate assistance only; acceptance, policy, credential, deployment and production authority remain with the canonical owners.`,
      }});
      applied.push({id:finding.id, disposition:'created_issue', issue_number:created.number, fingerprint});
    }
  }
  if (applied.length) await addIssueComment(missionIssue.number, `Governance findings processed: ${applied.map((item)=>`${item.id}->${item.disposition}${item.issue_number ? ` #${item.issue_number}` : ''}`).join(', ')}.`);
  return applied;
}

export function selectResumableMission(activeMissions, mode = 'standard') {
  if (mode === 'governance_sweep') return {issue:null,state:null};
  for (const item of Array.isArray(activeMissions) ? activeMissions : []) {
    const state = item?.state || parseState(item?.issue?.body);
    if (state && !(state.state === 'blocked' && state.retriable === false)) {
      return {issue:item.issue || null,state};
    }
  }
  return {issue:null,state:null};
}

function improvementComponentForRun() {
  const digits = String(process.env.GITHUB_RUN_NUMBER || process.env.GITHUB_RUN_ID || '0').replace(/[^0-9]/g, '') || '0';
  return IMPROVEMENT_COMPONENTS[Number(BigInt(digits) % BigInt(IMPROVEMENT_COMPONENTS.length))];
}

async function createMission(missionId, foundationSha) {
  const mode = process.env.MISSION_MODE || 'standard';
  const targetComponent = mode === 'component_improvement' ? improvementComponentForRun() : null;
  const state = {
    schema:'autonomous-mission-state/v1', mission_id:missionId, mission_type:null, target_component:targetComponent, mode, state:'planning',
    foundation_sha:foundationSha, cycle:0, workflow_attempts:{}, child_runs:[], last_plan_digest:null,
    last_provider:null, last_summary:'mission created by autonomous supervisor', terminal_reason:null,
    failure_class:null, retriable:true
  };
  const issue = await github(`/repos/${owner}/${repo}/issues`, {method:'POST', body:{
    title:`[${mode === 'component_improvement' ? 'autonomous-improvement' : mode === 'governance_sweep' ? 'autonomous-governance' : 'autonomous-mission'}] ${missionId}`, body:missionBody(state,'Waiting for governed AI planning.')
  }});
  return {issue, state};
}

async function dispatchWorkflow(workflow) {
  await github(`/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`, {
    method:'POST', body:{ref:'main'}
  });
}


export async function dispatchPlanActions({plan, state, dryRun, maxWorkflowAttempts: attemptBound, foundationSha, dispatchWorkflowFn = dispatchWorkflow, findRecentWorkflowRunFn = findRecentWorkflowRun}) {
  if (!plan || !Array.isArray(plan.actions)) throw new Error('invalid_plan_actions');
  const attempts = {...(state?.workflow_attempts || {})};
  for (const action of plan.actions) {
    if (!dryRun) attempts[action.workflow] = Number(attempts[action.workflow] || 0) + 1;
    if (!dryRun && attempts[action.workflow] > attemptBound) {
      throw new Error(`same_workflow_attempt_bound_exceeded:${action.workflow}`);
    }
  }
  if (dryRun) return {attempts, children: []};
  const children = await Promise.all(plan.actions.map(async (action) => {
    const startedMs = Date.now();
    await dispatchWorkflowFn(action.workflow);
    const child = await findRecentWorkflowRunFn(action.workflow, foundationSha, startedMs);
    return {workflow: action.workflow, run: child};
  }));
  return {attempts, children};
}

async function findRecentWorkflowRun(workflow, foundationSha, startedMs) {
  const path = `/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflow)}/runs?branch=main&event=workflow_dispatch&per_page=20`;
  for (let i=0;i<5;i++) {
    const data = await github(path);
    const runs = data.workflow_runs || [];
    const match = runs.find((r) => r.head_sha === foundationSha && Date.parse(r.created_at || 0) >= startedMs - 5000);
    if (match) return match;
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }
  return null;
}

export function deterministicFallbackPlan(context) {
  const mode = context?.mode || 'standard';
  const issues = Array.isArray(context?.open_issues) ? context.open_issues : [];
  let missionType = 'runtime_reconciliation';
  let targetComponent = null;
  let workflows = MISSION_WORKFLOWS.runtime_reconciliation;
  if (mode === 'governance_sweep') {
    missionType = 'governance_sweep';
    workflows = MISSION_WORKFLOWS.governance_sweep;
    const audit = context?.governance_audit || {};
    if (audit?.foundation?.hygiene?.passed === false) {
      workflows = ['repository-hygiene-autofix.yml', ...workflows.filter((item) => item !== 'repository-hygiene-autofix.yml')];
    }
  } else if (mode === 'component_improvement') {
    targetComponent = context?.target_component;
    if (!targetComponent || !PROJECT_IMPROVEMENT_MATRIX.components[targetComponent]) throw new Error('fallback_component_unavailable');
    missionType = 'component_improvement';
    workflows = PROJECT_IMPROVEMENT_MATRIX.components[targetComponent].workflows;
  } else {
    const issueText = issues.map((item) => String(item.title || '') + ' ' + String(item.body || '')).join(' ').toLowerCase();
    if (/woocommerce|feed|merchant/.test(issueText)) { missionType = 'feed_recovery'; workflows = MISSION_WORKFLOWS.feed_recovery; }
    else if (/migration|polyglot|mapper/.test(issueText)) { missionType = 'migration'; workflows = MISSION_WORKFLOWS.migration; }
    else if (/research|nightly|provider/.test(issueText)) { missionType = 'nightly_research'; workflows = MISSION_WORKFLOWS.nightly_research; }
    else if (/audit|security|integrity|governance/.test(issueText)) { missionType = 'audit'; workflows = MISSION_WORKFLOWS.audit; }
  }
  const workflowKey = (run) => String(run.path || '').split('/').pop() || String(run.name || '');
  const active = new Set((context?.recent_runs || []).filter((run) => ['queued','in_progress','waiting','requested','pending'].includes(run.status)).map(workflowKey));
  const recentSuccess = new Set((context?.recent_runs || []).filter((run) => run.conclusion === 'success' && run.created_at && (Date.now() - Date.parse(run.created_at)) < 24 * 60 * 60 * 1000).map(workflowKey));
  const recentlyFailed = new Set((context?.recent_runs || []).filter((run) => run.conclusion === 'failure' && run.created_at && (Date.now() - Date.parse(run.created_at)) < 24 * 60 * 60 * 1000).map(workflowKey));
  const attemptCounts = context?.workflow_attempts && typeof context.workflow_attempts === 'object' ? context.workflow_attempts : {};
  const withinBudget = (candidate) => Number(attemptCounts[candidate] || 0) < maxWorkflowAttempts;
  const candidates = workflows.filter((candidate) => withinBudget(candidate) && !active.has(candidate) && !recentlyFailed.has(candidate) && !recentSuccess.has(candidate));
  const selected = candidates.slice(0, 3);
  if (!selected.length) throw new Error('fallback_workflow_unavailable');
  return {
    schema:'autonomous-mission-plan/v1',
    mission_type:missionType,
    target_component:targetComponent,
    summary:'Deterministic fallback selected untouched bounded evidence workflows after planner unavailability.',
    terminal:null,
    actions:selected.map((workflow,index)=>({id:`a${index+1}`,kind:'dispatch_workflow',workflow,inputs:{},reason:'Maintain autonomous progress using an existing allowlisted evidence workflow without changing authority.',retry_policy:'bounded'})),
    next_state:'executing',
    stop_reason:null
  };
}

async function callPlanner(missionId, cycle, context) {
  const serializedContext = JSON.stringify(context);
  if (serializedContext.length > 12000) throw new Error('planner_context_size_exceeded');
  const payload = {
    chat_id: missionId,
    request_id: `autonomous-plan:${missionId}:${cycle}`,
    message: 'AUTONOMOUS_ENGINEERING_PLAN_V1\nReturn JSON only. You are a bounded planner, not an execution authority. For component_improvement, target_component is mandatory and every action must come from that component allowlist. For governance_sweep, inspect every provided vertical/control summary and prioritize independent cross-fire lanes. Governance findings are already published by the deterministic governance publisher, so return zero findings; only select bounded allowlisted remediation workflows. Never assert runtime/production truth beyond the provided evidence. Do not duplicate workflows, do not dispatch production release, do not mutate credentials/policy/Cloudflare, and never use a second action merely to duplicate the first. Prefer 2-3 independent allowlisted workflows when they are non-overlapping; otherwise return the single highest-value action. '+JSON.stringify(context),
    mode:'chat', operation:'knowledge', task_family:'audit_assist', strict_zero_cost_only:true, require_model_generation:true,
    metadata:{autonomous:'true',plan_version:'v1',task_family:'audit_assist'},
  };
  const response = await fetch(`${workerUrl}/api/v1/chat`, {
    method:'POST',
    headers:{'Authorization':`Bearer ${process.env.AUTH_TOKEN}`,'Content-Type':'application/json','Idempotency-Key':payload.request_id},
    body:JSON.stringify(payload),
  });
  const text = await response.text();
  let body; try { body=JSON.parse(text); } catch { body={}; }
  if (!response.ok || body?.ok === false) throw new Error(`planner_http_${response.status}`);
  return body;
}

export function reconcileChildState(state, childResults) {
  if (!state || state.state !== 'executing' || !Array.isArray(state.child_runs) || state.child_runs.length === 0) return state;
  if (!Array.isArray(childResults) || childResults.length === 0) return state;
  const active = childResults.some((run) => ['queued','in_progress','waiting','requested','pending'].includes(run.status));
  if (active) return state;
  const terminalKnown = childResults.filter((run) => ['completed','cancelled'].includes(run.status) || ['success','failure','cancelled','skipped','timed_out','action_required','neutral'].includes(run.conclusion));
  const allKnown = terminalKnown.length === childResults.length && terminalKnown.length === state.child_runs.length;
  if (!allKnown) return state;
  return { ...state, state: 'verifying', last_summary: 'Child workflow execution finished; verification and next-step planning are now required.', terminal_reason: null, retriable: true };
}
async function main() {
  if (!process.env.AUTH_TOKEN) throw new Error('AUTH_TOKEN is required for autonomous planner');
  if (!owner || !repo || !token) throw new Error('GitHub repository/token environment is required');
  const foundationSha = process.env.FOUNDATION_SHA || (await new Promise((resolve, reject) => {
    import('node:child_process').then(({ execFile }) => execFile('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}, (error, stdout) => error ? reject(error) : resolve(stdout.trim()))).catch(reject);
  }));
  if (!foundationSha) throw new Error('FOUNDATION_SHA is required');
  const allIssues = await listIssues('open', 50);
  const mode = process.env.MISSION_MODE || 'standard';
  const missionPrefix = mode === 'component_improvement' ? '[autonomous-improvement]' : '[autonomous-mission]';
  const activeMissions = allIssues
    .filter((i) => !i.pull_request && String(i.title || '').startsWith(missionPrefix))
    .map((issue) => ({issue, state:parseState(issue.body)}));
  const openIssues = allIssues
    .filter((i) => !i.pull_request && !String(i.title || '').startsWith('[autonomous-mission]') && !String(i.title || '').startsWith('[autonomous-improvement]'))
    .slice(0,20);
  const recentRuns = (await listRuns(35)).slice(0,35);

  const resumable = selectResumableMission(activeMissions, mode);
  let missionIssue = resumable.issue;
  let state = resumable.state;
  if (!missionIssue || !state) {
    const missionId = `mission-${process.env.GITHUB_RUN_ID}`;
    const created = await createMission(missionId, foundationSha);
    missionIssue = created.issue; state = created.state;
  }

  const childResults = [];
  if (state.state === 'blocked' && state.retriable !== true) {
    console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked',reason:state.terminal_reason || 'human_or_policy_gate'}));
    return;
  }
  for (const id of state.child_runs || []) {
    try { childResults.push(await readRun(id)); }
    catch (error) { childResults.push({database_id:id,status:'unknown',conclusion:'unavailable',error:String(error)}); }
  }
  const activeChild = childResults.find((r) => ['queued','in_progress','waiting','requested','pending'].includes(r.status));
  if (state.state === 'executing' && activeChild) {
    await updateIssue(missionIssue.number, {body:missionBody(state, `Child workflow ${activeChild.name || activeChild.database_id} is still ${activeChild.status}.`)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'executing',child_run:activeChild.database_id}));
    return;
  }
  const reconciledState = reconcileChildState(state, childResults);
  if (reconciledState !== state) {
    state = reconciledState;
    await updateIssue(missionIssue.number, {body:missionBody(state, state.last_summary)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'verifying',child_runs:state.child_runs}));
  }

  const cycle = Number(state.cycle || 0) + 1;
  if (cycle > maxCycles) {
    state = {...state, state:'blocked', cycle, terminal_reason:'planning_cycle_bound_exceeded', failure_class:'policy_blocked', retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,'Planning cycle bound exceeded; human review required.')});
    return;
  }

  const governanceAudit = mode === 'governance_sweep' ? loadGovernanceAudit() : null;
  const context = {
    mission:state,
    foundation_sha:foundationSha,
    mode,
    target_component:state.target_component,
    target_component_definition:state.target_component ? PROJECT_IMPROVEMENT_MATRIX.components[state.target_component] : null,
    open_issues:openIssues.slice(0,10).map((i)=>({number:i.number,title:sanitize(i.title).slice(0,240),body:sanitize(i.body).slice(0,650),updatedAt:i.updated_at})),
    recent_runs:recentRuns.slice(0,20).map((r)=>({id:r.id,name:sanitize(r.name).slice(0,160),path:sanitize(r.path).slice(0,240),status:r.status,conclusion:r.conclusion,head_sha:r.head_sha,event:r.event,created_at:r.created_at})),
    workflow_attempts:state.workflow_attempts || {},
    child_runs:childResults.map((r)=>({id:r.id,name:r.name,status:r.status,conclusion:r.conclusion,head_sha:r.head_sha,event:r.event,url:r.html_url})),
    governance_audit: governanceAudit,
    hard_constraints:{production_release_allowed:false,secrets_or_credentials_mutation:false,policy_changes:false,workflow_inputs:{},max_same_workflow_dispatches:maxWorkflowAttempts,cloudflare_destructive_mutation_allowed:false},
  };

  let planner;
  let plannerFallback = false;
  try { planner = await callPlanner(state.mission_id, cycle, context); }
  catch (error) {
    try {
      const fallbackPlan = deterministicFallbackPlan(context);
      planner = {response:{provider:'deterministic-fallback'},plan:fallbackPlan};
      plannerFallback = true;
      state = {...state,cycle,last_provider:'deterministic-fallback',last_summary:'Governed planner unavailable; deterministic fallback selected an existing evidence workflow.',failure_class:'transient_provider',retriable:true};
      await updateIssue(missionIssue.number,{body:missionBody(state,state.last_summary)});
    } catch (fallbackError) {
      state = {...state,state:'blocked',cycle,terminal_reason:'planner_and_fallback_unavailable',failure_class:'transient_provider',retriable:true,last_summary:String(fallbackError).slice(0,240)};
      await updateIssue(missionIssue.number,{body:missionBody(state,'Planner unavailable and deterministic fallback could not be constructed; the next scheduled run will retry.')});
      console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked',reason:'planner_and_fallback_unavailable'}));
      return;
    }
  }

  const rawPlan = planner?.response?.text ?? planner?.plan ?? planner;
  let plan;
  try { plan = validatePlan(typeof rawPlan === 'string' ? JSON.parse(rawPlan.replace(/^```json\s*/i,'').replace(/\s*```$/,'')) : rawPlan); }
  catch (error) {
    state = {...state,state:'blocked',cycle,last_summary:'AI plan failed deterministic validation',terminal_reason:'planner_output_invalid',failure_class:'policy_blocked',retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,`Planner output rejected: ${String(error).slice(0,500)}`)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked',reason:'planner_output_invalid'}));
    return;
  }

  if (mode === 'component_improvement' && (plan.mission_type !== 'component_improvement' || plan.target_component !== state.target_component)) {
    state = {...state,state:'blocked',cycle,last_summary:'AI plan targeted the wrong component or mission class',terminal_reason:'improvement_component_mismatch',failure_class:'policy_blocked',retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,'Improvement plan rejected: component target mismatch.')});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked',reason:'improvement_component_mismatch'}));
    return;
  }

  const digest = crypto.createHash('sha256').update(JSON.stringify(plan)).digest('hex');
  state = {...state, mission_type:plan.mission_type, target_component:plan.target_component || state.target_component || null, cycle, last_plan_digest:digest, last_provider:planner?.response?.provider || null, last_summary:plan.summary, failure_class:plannerFallback ? 'transient_provider' : null};

  const appliedFindings = mode === 'governance_sweep' ? [] : await applyFindings({findings:plan.findings || [], missionIssue, openIssues:allIssues.filter((i)=>!i.pull_request)});
  if (appliedFindings.length) state = {...state, last_summary:`${plan.summary} Findings processed: ${appliedFindings.length}.`};

  if (plan.terminal === 'complete') {
    state = {...state,state:'complete',terminal_reason:plan.stop_reason || 'planner_closed_mission',retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,plan.summary)});
    await updateIssue(missionIssue.number,{state:'closed',state_reason:'completed'});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'complete'}));
    return;
  }
  if (plan.terminal === 'blocked') {
    state = {...state,state:'blocked',terminal_reason:plan.stop_reason || 'planner_blocked',failure_class:'external_admin_required',retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,plan.summary)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked'}));
    return;
  }

  let dispatched;
  try {
    dispatched = await dispatchPlanActions({plan,state,dryRun,maxWorkflowAttempts,foundationSha});
  } catch (error) {
    const message = String(error);
    if (message.includes('same_workflow_attempt_bound_exceeded:')) {
      const workflow = message.split(':').slice(1).join(':');
      state = {...state,state:'blocked',workflow_attempts:{...(state.workflow_attempts || {})},terminal_reason:'same_workflow_attempt_bound_exceeded',failure_class:'policy_blocked',retriable:false};
      await updateIssue(missionIssue.number,{body:missionBody(state,`Workflow attempt bound exceeded for ${workflow}.`)});
      return;
    }
    state = {...state,state:'retrying',last_summary:`Parallel workflow dispatch failed: ${sanitize(message)}`,failure_class:'transient_workflow',retriable:true};
    await updateIssue(missionIssue.number,{body:missionBody(state,state.last_summary)});
    throw error;
  }
  if (dryRun) {
    state = {...state,state:'planned',workflow_attempts:dispatched.attempts};
    await updateIssue(missionIssue.number,{body:missionBody(state,`DRY RUN: would dispatch ${plan.actions.map((a)=>a.workflow).join(', ')} in parallel.`)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'planned',workflows:plan.actions.map((a)=>a.workflow),dry_run:true}));
    return;
  }

  const childIds = dispatched.children.map((item)=>item.run?.id).filter(Boolean);
  state = {...state,state:'executing',workflow_attempts:dispatched.attempts,child_runs:[...new Set([...(state.child_runs || []), ...childIds])],retriable:true,terminal_reason:null};
  const notes = dispatched.children.map(({workflow,run}) => run ? `Dispatched ${workflow} as child run ${run.id}.` : `Dispatched ${workflow}; child run identity will be reconciled on the next wake-up.`);
  await updateIssue(missionIssue.number,{body:missionBody(state,`${plan.summary}\n\n${notes.join('\n')}`)});
  console.log(JSON.stringify({mission_id:state.mission_id,state:'executing',workflows:plan.actions.map((a)=>a.workflow),child_runs:childIds}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();