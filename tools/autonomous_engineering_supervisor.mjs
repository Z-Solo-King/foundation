import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { validatePlan } from './autonomous_mission_router.mjs';

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

async function createMission(missionId, foundationSha) {
  const state = {
    schema:'autonomous-mission-state/v1', mission_id:missionId, mission_type:null, state:'planning',
    foundation_sha:foundationSha, cycle:0, workflow_attempts:{}, child_runs:[], last_plan_digest:null,
    last_provider:null, last_summary:'mission created by autonomous supervisor', terminal_reason:null,
    failure_class:null, retriable:true
  };
  const issue = await github(`/repos/${owner}/${repo}/issues`, {method:'POST', body:{
    title:`[autonomous-mission] ${missionId}`, body:missionBody(state,'Waiting for governed AI planning.')
  }});
  return {issue, state};
}

async function dispatchWorkflow(workflow) {
  await github(`/repos/${owner}/${repo}/actions/workflows/${encodeURIComponent(workflow)}/dispatches`, {
    method:'POST', body:{ref:'main'}
  });
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

async function callPlanner(missionId, cycle, context) {
  const serializedContext = JSON.stringify(context);
  if (serializedContext.length > 12000) throw new Error('planner_context_size_exceeded');
  const payload = {
    chat_id: missionId,
    request_id: `autonomous-plan:${missionId}:${cycle}`,
    message: 'AUTONOMOUS_ENGINEERING_PLAN_V1\nReturn JSON only. You are a bounded planner, not an execution authority. Choose one next step that maximizes useful evidence while avoiding repeated known failures. '+JSON.stringify(context),
    mode:'chat', operation:'knowledge', strict_zero_cost_only:true, require_model_generation:true,
    metadata:{autonomous:'true',plan_version:'v1'},
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

async function main() {
  if (!process.env.AUTH_TOKEN) throw new Error('AUTH_TOKEN is required for autonomous planner');
  if (!process.env.AUTH_TOKEN) throw new Error('AUTH_TOKEN is required for autonomous planner');
  if (!owner || !repo || !token) throw new Error('GitHub repository/token environment is required');
  if (!process.env.AUTH_TOKEN) throw new Error('AUTH_TOKEN is required for autonomous planner');
  const foundationSha = process.env.FOUNDATION_SHA || (await new Promise((resolve, reject) => {
    import('node:child_process').then(({ execFile }) => execFile('git', ['rev-parse', 'HEAD'], {encoding:'utf8'}, (error, stdout) => error ? reject(error) : resolve(stdout.trim()))).catch(reject);
  }));
  if (!foundationSha) throw new Error('FOUNDATION_SHA is required');
  const allIssues = await listIssues('open', 50);
  const activeMissions = allIssues.filter((i) => !i.pull_request && String(i.title || '').startsWith('[autonomous-mission]'));
  const openIssues = allIssues.filter((i) => !i.pull_request && !String(i.title || '').startsWith('[autonomous-mission]')).slice(0,20);
  const recentRuns = (await listRuns(35)).slice(0,35);

  let missionIssue = activeMissions[0] || null;
  let state = missionIssue ? parseState(missionIssue.body) : null;
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
    await updateIssue(missionIssue.number, {body:missionBody(state,`Child workflow ${activeChild.name || activeChild.database_id} is still ${activeChild.status}.`)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'executing',child_run:activeChild.database_id}));
    return;
  }

  const cycle = Number(state.cycle || 0) + 1;
  if (cycle > maxCycles) {
    state = {...state, state:'blocked', cycle, terminal_reason:'planning_cycle_bound_exceeded', failure_class:'policy_blocked', retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,'Planning cycle bound exceeded; human review required.')});
    return;
  }

  const context = {
    mission:state,
    foundation_sha:foundationSha,
    open_issues:openIssues.slice(0,10).map((i)=>({number:i.number,title:sanitize(i.title).slice(0,240),body:sanitize(i.body).slice(0,650),updatedAt:i.updated_at})),
    recent_runs:recentRuns.slice(0,20).map((r)=>({id:r.id,name:sanitize(r.name).slice(0,160),status:r.status,conclusion:r.conclusion,head_sha:r.head_sha,event:r.event,created_at:r.created_at})),
    child_runs:childResults.map((r)=>({id:r.id,name:r.name,status:r.status,conclusion:r.conclusion,head_sha:r.head_sha,event:r.event,url:r.html_url})),
    hard_constraints:{production_release_allowed:false,secrets_or_credentials_mutation:false,policy_changes:false,workflow_inputs:{},max_same_workflow_dispatches:maxWorkflowAttempts},
  };

  let planner;
  try { planner = await callPlanner(state.mission_id, cycle, context); }
  catch (error) {
    state = {...state,state:'blocked',cycle,terminal_reason:'planner_unavailable',failure_class:'transient_provider',retriable:true,last_summary:String(error)};
    await updateIssue(missionIssue.number,{body:missionBody(state,'Planner unavailable. The next scheduled supervisor run will retry without requiring ChatGPT.')});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'blocked',reason:'planner_unavailable'}));
    return;
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

  const digest = crypto.createHash('sha256').update(JSON.stringify(plan)).digest('hex');
  state = {...state, mission_type:plan.mission_type, cycle, last_plan_digest:digest, last_provider:planner?.response?.provider || null, last_summary:plan.summary, failure_class:null};

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

  const action = plan.actions[0];
  const attempts = {...(state.workflow_attempts || {})};
  if (!dryRun) attempts[action.workflow] = Number(attempts[action.workflow] || 0) + 1;
  if (!dryRun && attempts[action.workflow] > maxWorkflowAttempts) {
    state = {...state,state:'blocked',workflow_attempts:attempts,terminal_reason:'same_workflow_attempt_bound_exceeded',failure_class:'policy_blocked',retriable:false};
    await updateIssue(missionIssue.number,{body:missionBody(state,`Workflow attempt bound exceeded for ${action.workflow}.`)});
    return;
  }
  if (dryRun) {
    state = {...state,state:'planned',workflow_attempts:attempts};
    await updateIssue(missionIssue.number,{body:missionBody(state,`DRY RUN: would dispatch ${action.workflow}.`)});
    console.log(JSON.stringify({mission_id:state.mission_id,state:'planned',workflow:action.workflow,dry_run:true}));
    return;
  }

  const startedMs = Date.now();
  await dispatchWorkflow(action.workflow);
  const child = await findRecentWorkflowRun(action.workflow, foundationSha, startedMs);
  state = {...state,state:'executing',workflow_attempts:attempts,child_runs:[...new Set([...(state.child_runs || []), child?.id].filter(Boolean))],retriable:true,terminal_reason:null};
  const note = child ? `Dispatched ${action.workflow} as child run ${child.id}.` : `Dispatched ${action.workflow}; child run identity will be reconciled on the next wake-up.`;
  await updateIssue(missionIssue.number,{body:missionBody(state,`${plan.summary}\n\n${note}`)});
  console.log(JSON.stringify({mission_id:state.mission_id,state:'executing',workflow:action.workflow,child_run:child?.id || null}));
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) await main();