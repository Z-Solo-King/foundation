import fs from 'node:fs';
import path from 'node:path';
import {exists, fingerprintObject, readText, walkFiles, digestObject} from './evidence_kernel.mjs';

export const LANES = [
  {id:'structure', role:'Structure analyst', objective:'repository topology, ownership, duplicate authorities, shadow surfaces'},
  {id:'contract', role:'Contract analyst', objective:'API/schema/type/config compatibility and canonical boundaries'},
  {id:'behavior', role:'Behavior analyst', objective:'tests, runtime paths, deterministic behavior, regressions'},
  {id:'security', role:'Adversarial security analyst', objective:'secrets, unsafe automation, trust boundaries, injection and mutation paths'},
  {id:'operational', role:'Operations analyst', objective:'budgets, retries, checkpoints, concurrency, provider/runtime reliability'},
  {id:'reconciler', role:'Reconciliation analyst', objective:'cross-repo drift, documentation drift, redundant workflows, smallest deterministic fix'},
];

export const DOMAINS = {
  extractor:['extractor_mapper','extractor','commerce-feed','woocommerce'],
  mapper:['mapper','mapping','product_mapper'],
  chatbot:['private/chatbot','chatbot','heroic'],
  provider:['provider','model','llm','ai-agent'],
  runtime:['worker','runtime','browser','resource','durable'],
  security:['security','secret','auth','trust','moderation','prompt'],
  repository:['REPOSITORY_MAP.json','docs/AI_PROJECT_MAP.json','.github'],
  polyglot:['polyglot','language','migration','rust','typescript'],
  documentation:['docs/','README.md','.md'],
  dependencies:['package.json','requirements','pyproject.toml','uv.lock','poetry.lock'],
  workflows:['.github/workflows/','.github/actions/'],
  tests:['tests/','test_'],
};

const WORKFLOW_CATALOG = {
  extractor:['.github/workflows/extractor-surface-governance.yml','.github/workflows/exhaustive-six-lane-audit.yml','.github/workflows/commerce-feed-product-crawl.yml'],
  mapper:['.github/workflows/exhaustive-six-lane-audit.yml','.github/workflows/coverage-driven-runtime-matrix.yml'],
  chatbot:['.github/workflows/ai-agent-benchmark-contract.yml','.github/workflows/coverage-driven-runtime-matrix.yml','.github/workflows/browser-engine-runtime-evidence.yml'],
  provider:['.github/workflows/ai-agent-benchmark-contract.yml','.github/workflows/coverage-driven-runtime-matrix.yml','.github/workflows/fresh-control-plane-identity-acceptance.yml'],
  runtime:['.github/workflows/coverage-driven-runtime-matrix.yml','.github/workflows/browser-engine-runtime-evidence.yml','.github/workflows/canonical-workflow-dispatch-acceptance.yml'],
  security:['.github/workflows/codeql.yml','.github/workflows/dependency-review.yml','.github/workflows/full-history-secret-scan.yml','.github/workflows/github-app-governance.yml','.github/workflows/required-pr-checks.yml'],
  repository:['.github/workflows/family-integrity-gate.yml','.github/workflows/family-full-coverage.yml','.github/workflows/cross-repository-contract-drift.yml'],
  polyglot:['.github/workflows/family-full-coverage.yml','.github/workflows/exhaustive-six-lane-audit.yml'],
  documentation:['.github/workflows/twice-daily-governance-sweep.yml','.github/workflows/family-hygiene-sync.yml'],
  dependencies:['.github/workflows/dependency-review.yml','.github/workflows/actions-static-analysis.yml'],
  workflows:['.github/workflows/actions-static-analysis.yml','.github/workflows/family-integrity-gate.yml','.github/workflows/required-pr-checks.yml'],
  tests:['.github/workflows/required-pr-checks.yml','.github/workflows/coverage-driven-runtime-matrix.yml'],
};

const PROVIDER_HOSTS = [
  'api.groq.com','generativelanguage.googleapis.com','openrouter.ai','api.cerebras.ai',
  'api.siliconflow.cn','integrate.api.nvidia.com','api.cohere.com','api-inference.huggingface.co',
];

const REQUIRED_FOUNDATION_FILES = [
  'REPOSITORY_MAP.json',
  'docs/AI_PROJECT_MAP.json',
  'docs/CURRENT_SOURCE_OF_TRUTH.md',
  'docs/CROSS_SYSTEM_CROSSFIRE_STANDARD.md',
  '.github/workflows/required-pr-checks.yml',
];

const walk = root => walkFiles(root, {skip:new Set(['.git','node_modules','.venv','__pycache__'])});
const read = readText;

function containsCaseInsensitive(value, needle) {
  return value.toLowerCase().includes(needle.toLowerCase());
}

export function classifyPaths(paths) {
  const domains = new Set();
  for (const rel of paths) {
    for (const [domain, needles] of Object.entries(DOMAINS)) {
      if (needles.some(n => containsCaseInsensitive(rel,n))) domains.add(domain);
    }
  }
  if (!domains.size) domains.add('repository');
  return [...domains].sort();
}

function fingerprint(finding) {
  return fingerprintObject({severity:finding.severity,kind:finding.kind,path:finding.path,message:finding.message});
}

function finding(severity, kind, rel, message, evidence = []) {
  const row = {severity,kind,path:rel || '',message,evidence};
  row.fingerprint = fingerprint(row);
  return row;
}

export function scanFoundation(root) {
  const files = walk(root);
  const findings = [];

  for (const required of REQUIRED_FOUNDATION_FILES) {
    if (!files.includes(required)) findings.push(finding('critical','missing_required_file',required,'Required canonical file is missing: ' + required));
  }

  const workflows = files.filter(f => f.startsWith('.github/workflows/') && f.endsWith('.yml'));
  for (const rel of workflows) {
    const content = read(root,rel,500_000);
    for (const [index,line] of content.split(/\r?\n/).entries()) {
      const match = line.match(/uses:\s*([^\s#]+)@([^\s#]+)/);
      if (!match) continue;
      const ref = match[2];
      if (ref.startsWith('v') || !/^[0-9a-f]{40}$/.test(ref)) {
        findings.push(finding('warning','unpinned_action',rel,'GitHub Action is not pinned to a full commit SHA: ' + ref,[rel + ':' + (index+1)]));
      }
    }
  }

  for (const rel of files.filter(f => /\.(mjs|cjs|js|ts|tsx|py)$/.test(f))) {
    if (/provider_catalog|provider_runtime|provider_configuration|provider_retry/.test(rel)) continue;
    const content = read(root,rel,350_000);
    for (const host of PROVIDER_HOSTS) {
      if (content.includes(host)) findings.push(finding('warning','direct_provider_endpoint',rel,'Direct external provider endpoint outside canonical provider modules: ' + host,[host]));
    }
  }

  const secretLike = /(sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,})/;
  for (const rel of files.filter(f => /\.(mjs|cjs|js|ts|tsx|py|yml|yaml|json|toml)$/.test(f))) {
    if (rel.includes('verification_fabric')) continue;
    if (secretLike.test(read(root,rel,500_000))) {
      findings.push(finding('warning','secret_like_literal',rel,'Credential-shaped literal detected; authoritative secret validation remains with the dedicated secret-scan workflow.',[rel]));
    }
  }

  const names = new Map();
  for (const rel of files) {
    const base = path.basename(rel).toLowerCase();
    if (!names.has(base)) names.set(base,[]);
    names.get(base).push(rel);
  }
  for (const [base, rows] of names) {
    if (rows.length >= 3 && /\.(mjs|cjs|js|ts|py)$/.test(base)) {
      findings.push(finding('info','duplicate_filename_cluster',rows[0],'Multiple implementation files share basename "' + base + '". Review for duplicate authority.',rows.slice(0,8)));
    }
  }

  const workflowBases = workflows.map(rel => {
    const base = path.basename(rel).replace(/\.ya?ml$/,'').replace(/-v\d+(?:-v\d+)*$/,'').replace(/\d+$/,'').replace(/[-_]+/g,' ');
    return [base,rel];
  });
  const byName = new Map();
  for (const [base,rel] of workflowBases) {
    if (!byName.has(base)) byName.set(base,[]);
    byName.get(base).push(rel);
  }
  for (const [base,rows] of byName) {
    if (rows.length > 1) findings.push(finding('info','workflow_overlap_cluster',rows[0],'Potentially overlapping workflow family: "' + base + '".',rows.slice(0,10)));
  }

  const operationsPath = path.join(root,'..','operations-repo');
  if (exists(root,'../operations-repo/.github/workflows')) {
    const opsWorkflows = walk(path.join(operationsPath,'.github','workflows'));
    if (opsWorkflows.some(f=>f.endsWith('.yml')||f.endsWith('.yaml'))) {
      findings.push(finding('critical','operations_workflow_authority','../operations-repo/.github/workflows','Operations contains GitHub Actions workflows despite Foundation ownership contract.'));
    }
  }

  const docs = read(root,'README.md',150_000);
  if (!/Operations deliberately contains \*\*no GitHub Actions workflows\*\*/.test(docs)) {
    findings.push(finding('warning','ownership_documentation_drift','README.md','README no longer states the canonical GitHub Actions ownership boundary for Operations.'));
  }

  const changed = process.env.VERIFICATION_CHANGED_FILES ? process.env.VERIFICATION_CHANGED_FILES.split('\n').filter(Boolean) : files;
  return {files,findings,domains:classifyPaths(changed),workflow_count:workflows.length};
}

export function planVerification({domains, mode='pr'}) {
  const unique = new Set();
  const checks = [];
  for (const domain of domains) {
    for (const workflow of WORKFLOW_CATALOG[domain] || []) {
      if (unique.has(workflow)) continue;
      unique.add(workflow);
      checks.push({workflow,domain,lanes:LANES.map(x=>x.id)});
    }
  }
  return {
    schema:'verification-fabric-plan/v1',
    mode,
    domains:[...domains].sort(),
    lanes:LANES.map(lane => ({...lane,domains:[...domains],mode})),
    checks:checks.slice(0,12),
    bounded:true,
    authority:'deterministic scanner and existing canonical workflows; AI is advisory',
    forbidden_actions:['production_release','secret_mutation','policy_mutation','cloudflare_destructive_mutation','access_control_bypass'],
  };
}

export function assertPlanSafe(plan) {
  if (!plan || !Array.isArray(plan.checks) || !Array.isArray(plan.lanes)) throw new Error('invalid_verification_plan');
  const keys = new Set();
  for (const check of plan.checks) {
    if (keys.has(check.workflow)) throw new Error('duplicate_workflow:' + check.workflow);
    keys.add(check.workflow);
  }
  if (plan.checks.some(x => !x.workflow.startsWith('.github/workflows/'))) throw new Error('non_canonical_workflow');
  return true;
}

export function summarize(report, plan) {
  const critical = report.findings.filter(f=>f.severity==='critical');
  const warning = report.findings.filter(f=>f.severity==='warning');
  return {
    schema:'verification-fabric-summary/v1',
    domains:plan.domains,
    lane_count:plan.lanes.length,
    planned_checks:plan.checks.length,
    findings:report.findings.length,
    critical_count:critical.length,
    warning_count:warning.length,
    status:critical.length ? 'blocked' : warning.length ? 'review' : 'clean',
    security_authority:'dedicated full-history secret scan',
    critical_findings:critical.map(f=>({kind:f.kind,path:f.path,message:f.message,evidence:f.evidence})),
    report_sha256:digestObject(report),
  };
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname)) {
  const root = process.env.VERIFICATION_ROOT || process.cwd();
  const mode = process.env.VERIFICATION_MODE || 'manual';
  const report = scanFoundation(root);
  const plan = planVerification({domains:report.domains,mode});
  assertPlanSafe(plan);
  const summary = summarize(report,plan);
  const out = {report:{...report,summary},plan,generated_at:new Date().toISOString()};
  fs.writeFileSync(path.join(root,'.runtime-verification-fabric.json'),JSON.stringify(out,null,2) + '\n');
  console.log(JSON.stringify(summary,null,2));
  if (summary.critical_count) process.exitCode=1;
}