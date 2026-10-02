#!/usr/bin/env node
/** Comprehensive cross-fire governance scanner; report only. */
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const SOURCE = new Set([".py",".pyi",".js",".mjs",".cjs",".ts",".tsx",".jsx",".rs",".go",".php",".rb",".java",".kt",".swift",".c",".cpp",".h",".hpp",".sh",".ps1"]);
const TEXT = new Set([...SOURCE, ".md",".rst",".txt",".json",".jsonc",".yaml",".yml",".toml",".ini",".cfg",".xml",".html",".css",".scss",".sql"]);
const HIST = ["/history/","/feed-lab/","/runtime/"];
const LANES = ["structure_hygiene","migration_boundary","research_feed","provider_runtime","work_items_workflow","maps_docs_policy","quality_learning_evolution","performance_resources"];

function sha256(value) { return crypto.createHash("sha256").update(value).digest("hex"); }
function sh(cmd, cwd) { const r = spawnSync(cmd[0], cmd.slice(1), {cwd, encoding:"utf8", stdio:["ignore","pipe","pipe"]}); if (r.status !== 0) throw new Error(String(r.stderr || "command failed").trim()); return String(r.stdout || ""); }
export function tracked(root) {
  try {
    return sh(["git","ls-files","-z"], root).split("\0").filter(Boolean);
  } catch {
    const files = [];
    const visit = dir => {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if ([".git","node_modules","dist","build","target","__pycache__"].includes(entry.name)) continue;
        const full = path.join(dir, entry.name);
        if (entry.isDirectory()) visit(full);
        else if (entry.isFile()) files.push(path.relative(root, full).replaceAll("\\","/"));
      }
    };
    visit(root);
    return files.sort();
  }
}
export function inventory(root) {
  const out = [];
  for (const rel of tracked(root)) {
    const p = path.join(root, rel);
    if (!fs.statSync(p,{throwIfNoEntry:false})?.isFile()) continue;
    const b = fs.readFileSync(p); let text = null;
    if (TEXT.has(path.extname(p).toLowerCase()) || ["README.md","AGENTS.md","Dockerfile","Containerfile","Makefile","Caddyfile"].includes(path.basename(p))) text = b.toString("utf8");
    out.push({path:rel, bytes:b.length, lines:text===null?null:text.split("\n").length, sha:sha256(b), text});
  }
  return out;
}
function historical(rel) { const normalized="/"+rel.toLowerCase(); return HIST.some(token => normalized.includes(token)); }
function addFinding(findings,lane,category,severity,code,summary,details=null,paths=null) {
  const finding={lane,category,severity,code,summary}; if(details!==null) finding.details=details; if(paths?.length) finding.paths=paths.slice(0,25);
  finding.finding_id=sha256(JSON.stringify(finding)).slice(0,16); findings.push(finding);
}
function loadJson(file) { try { return JSON.parse(fs.readFileSync(file,"utf8")); } catch { return null; } }
function globExists(root, pattern) {
  if (!/[?*]/.test(pattern)) return fs.existsSync(path.join(root,pattern));
  const base = pattern.split(/[?*]/)[0]; const start = path.join(root,base); if (!fs.existsSync(start)) return false;
  const escapeRe = value => value.replace(/[|\\^$+.()]/g, "\\$&");
  const regex = new RegExp("^" + pattern.split("*").map(escapeRe).join(".*").replaceAll("?","[^/]") + "$");
  const visit = dir => { for (const e of fs.readdirSync(dir,{withFileTypes:true})) { const full=path.join(dir,e.name); if(e.isDirectory() && visit(full)) return true; if(e.isFile()) { const rel=path.relative(root,full).replaceAll("\\","/"); if(regex.test(rel)) return true; } } return false; };
  return visit(start);
}
function argMap(argv) { const out={}; for(let i=0;i<argv.length;i++){ const t=argv[i]; if(t.startsWith("--")) out[t.slice(2)]=argv[i+1]||""; } return out; }
function ageDays(value, now) { const ms=Date.parse(String(value)); return Number.isFinite(ms)?Math.floor((now-ms)/86400000):0; }
export function buildScan(foundationRoot, operationsRoot, snapshot={}, lane="all") {
  const now=Date.now(), findings=[], F=inventory(foundationRoot), O=inventory(operationsRoot), rows={foundation:F,operations:O};

  if(["all","structure_hygiene"].includes(lane)){
    for(const [repo,records] of Object.entries(rows)){
      const dup=new Map(), big=[], attention=[], basenames=new Map();
      for(const r of records){ const d=dup.get(r.sha)||[]; d.push(r.path); dup.set(r.sha,d);
        if(SOURCE.has(path.extname(r.path).toLowerCase())&&!historical(r.path)){
          if((r.lines||0)>1000||r.bytes>50000) big.push(r); if((r.lines||0)>500||r.bytes>25000) attention.push(r);
          if(path.basename(r.path)!=="__init__.py"){ const b=path.basename(r.path); const list=basenames.get(b)||[]; list.push(r.path); basenames.set(b,list); }
        }}
      for(const paths of dup.values()){ const live=paths.filter(p=>(SOURCE.has(path.extname(p).toLowerCase())||path.extname(p).toLowerCase()===".md")&&!historical(p)); if(live.length>1) addFinding(findings,"structure_hygiene","duplicate","attention","exact_duplicate_content",repo+" has exact duplicate tracked content.",null,live); }
      if(big.length) addFinding(findings,"structure_hygiene","large_code","critical","critical_source_size",repo+" has source beyond the critical size threshold.",{count:big.length},big.map(x=>x.path));
      else if(attention.length) addFinding(findings,"structure_hygiene","large_code","attention","attention_source_size",repo+" has source beyond the attention size threshold.",{count:attention.length},attention.slice(0,50).map(x=>x.path));
      for(const [name,paths] of basenames) if(paths.length>=3) addFinding(findings,"structure_hygiene","scattering","attention","duplicate_basename_family",repo+" has a source basename scattered across multiple live directories.",{basename:name},paths);
    }
    for(const r of F){ if(!r.path.startsWith(".github/workflows/")||![".yml",".yaml"].includes(path.extname(r.path).toLowerCase())) continue; const t=r.text||"";
      if(!t.includes("permissions:")) addFinding(findings,"structure_hygiene","workflow","attention","missing_permissions_block","Workflow "+r.path+" has no explicit permissions block.",null,[r.path]);
      for(const m of t.matchAll(/^\s*-\s*uses:\s*([^@\s]+)@([^\s#]+)/gm)) if(!/^[0-9a-fA-F]{40}$/.test(m[2])) addFinding(findings,"structure_hygiene","workflow","critical","unpinned_action","Workflow "+r.path+" contains an unpinned action.",{action:m[1],ref:m[2]},[r.path]);
      if(/cron:\s*["\x27]?0(?:\s|$)/m.test(t)) addFinding(findings,"structure_hygiene","workflow","attention","hour_boundary_schedule","Workflow "+r.path+" is scheduled at the top of an hour.",null,[r.path]);
    }
    const allow=new Set([".editorconfig",".gitattributes",".prettierrc.json",".prettierignore",".markdownlint.json","docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json"]), fBy=new Map(), oBy=new Map();
    for(const r of F) if(SOURCE.has(path.extname(r.path).toLowerCase())&&!historical(r.path)&&!allow.has(r.path)){ const a=fBy.get(r.sha)||[]; a.push(r.path); fBy.set(r.sha,a); }
    for(const r of O) if(SOURCE.has(path.extname(r.path).toLowerCase())&&!historical(r.path)&&!allow.has(r.path)){ const a=oBy.get(r.sha)||[]; a.push(r.path); oBy.set(r.sha,a); }
    for(const [sharedSha,paths] of fBy) if(oBy.has(sharedSha)) addFinding(findings,"structure_hygiene","duplicate","attention","cross_repo_duplicate_content","Foundation and Operations contain identical live source content, creating possible duplicate authority.",{hash:sharedSha},paths.slice(0,12).concat(oBy.get(sharedSha).slice(0,12)));
    const registry=loadJson(path.join(foundationRoot,"docs/WORKFLOW_AUTHORITY_REGISTRY.json"))||{}, registered=new Set((registry.explicit_privileged_workflows||[]).filter(Array.isArray).map(x=>x[0]));
    for(const r of F){ if(!r.path.startsWith(".github/workflows/")||![".yml",".yaml"].includes(path.extname(r.path).toLowerCase())) continue; const t=r.text||""; if((t.includes("secrets.")||t.includes("actions/create-github-app-token")||t.includes("Z-Solo-King/operations"))&&!registered.has(r.path)) addFinding(findings,"structure_hygiene","workflow","critical","unregistered_privileged_workflow","Privileged workflow is not present in the machine-checkable authority registry.",null,[r.path]); }
  }

  if(["all","migration_boundary"].includes(lane)){
    const registry=loadJson(path.join(operationsRoot,"polyglot/REGISTRY.json"))||{}, matrix=loadJson(path.join(operationsRoot,"docs/MIGRATION_EVIDENCE_MATRIX.json"))||{}, required=Array.isArray(matrix.required_gates)?matrix.required_gates:[], evidenceBy=new Map((matrix.candidates||[]).filter(x=>x&&x.id).map(x=>[x.id,x]));
    for(const candidate of registry.candidates||[]){ if(!candidate?.id) continue; const item=evidenceBy.get(candidate.id); if(!item){addFinding(findings,"migration_boundary","evidence","critical","migration_candidate_missing_evidence","Registered migration candidate has no matching evidence-matrix record.",{candidate_id:candidate.id});continue;} const missing=required.filter(g=>item.evidence?.[g]!==true&&g!=="frozen corpus"); if(missing.length&&["evidence_complete","candidate_ready","recorded"].includes(String(item.status||"").toLowerCase())) addFinding(findings,"migration_boundary","evidence","attention","migration_gate_incomplete","Migration candidate is marked active/recorded while required promotion gates remain incomplete.",{candidate_id:item.id,status:item.status,missing_gates:missing.slice(0,20)}); }
    const runtimeSet=registry.registry_policy?.active_diversity?.current_runtime_set||[]; if(!runtimeSet.includes("python")) addFinding(findings,"migration_boundary","authority","critical","python_runtime_authority_missing","Migration registry no longer declares Python in the protected current runtime set.",{current_runtime_set:runtimeSet});
    const counters={}; for(const [repo,records] of Object.entries(rows)){ counters[repo]={}; for(const r of records) if(SOURCE.has(path.extname(r.path).toLowerCase())&&!historical(r.path)) counters[repo][path.extname(r.path).toLowerCase()]=(counters[repo][path.extname(r.path).toLowerCase()]||0)+1; }
    addFinding(findings,"migration_boundary","language","info","language_distribution","Current source-language distribution captured.",counters);
    const priv=F.filter(r=>r.path.startsWith("private/")).map(r=>r.path); if(priv.length) addFinding(findings,"migration_boundary","public_private","critical","private_tree_in_public_repo","Foundation still tracks private-tree paths.",null,priv);
    const secret=F.filter(r=>/(^|\/)[^/]*(API[_-]?KEY|PRIVATE[_-]?KEY|SECRET|TOKEN)[^/]*$/i.test(r.path)).map(r=>r.path); if(secret.length) addFinding(findings,"migration_boundary","public_private","critical","secret_like_filename_public","Foundation contains secret-like tracked filenames.",null,secret);
    if(!fs.existsSync(path.join(operationsRoot,"private/runtime_language_policy.py"))) addFinding(findings,"migration_boundary","policy","critical","language_authority_missing","Runtime language authority policy is missing.");
    if(!fs.existsSync(path.join(operationsRoot,"polyglot/REGISTRY.json"))) addFinding(findings,"migration_boundary","registry","attention","migration_registry_missing","Migration candidate registry is missing.");
  }

  if(["all","research_feed"].includes(lane)){
    const wf=new Set(F.filter(r=>r.path.startsWith(".github/workflows/")).map(r=>r.path)), need=[".github/workflows/nightly-multi-agent-research-v3.yml",".github/workflows/nightly-research-provider-preflight.yml",".github/workflows/native-google-feed-hunt.yml",".github/workflows/woocommerce-clean-recovery.yml",".github/workflows/woocommerce-identified-family-exhaustive-v5.yml"], miss=need.filter(p=>!wf.has(p));
    if(miss.length) addFinding(findings,"research_feed","authority","critical","canonical_research_feed_workflow_missing","Canonical research/feed workflow is missing.",null,miss);
    const titles=Object.values(snapshot).flatMap(x=>x?.issues||[]).map(x=>String(x.title||"")).join(" ").toLowerCase(); if(!titles.includes("24-program")) addFinding(findings,"research_feed","work_items","attention","nightly_research_issue_not_visible","Live metadata did not expose the 24-program research tracker."); if(!titles.includes("google feed")) addFinding(findings,"research_feed","work_items","attention","feed_issue_not_visible","Live metadata did not expose a Google-feed tracker.");
  }

  if(["all","provider_runtime"].includes(lane)){
    const fabric=loadJson(path.join(operationsRoot,"docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.json"))||{}, providers=new Set(fabric.external_providers||[]);
    if(!fs.existsSync(path.join(operationsRoot,"tools/provider_fleet_runtime_probe.py"))) addFinding(findings,"provider_runtime","provider","critical","provider_probe_missing","Canonical provider runtime probe is missing.");
    for(const p of ["private/search_provider_catalog.py","private/search_provider_capabilities.py","private/search_rate_limit.py","private/search_route_policy.py","private/search_provider_execution.py"]) if(!fs.existsSync(path.join(operationsRoot,p))) addFinding(findings,"provider_runtime","search","critical","search_authority_missing","Search/evidence authority missing: "+p,null,[p]);
    if(!fs.existsSync(path.join(operationsRoot,"private/chatbot/chat_endpoint.py"))) addFinding(findings,"provider_runtime","chatbot","critical","chatbot_boundary_missing","Canonical chatbot endpoint is missing.");
    for(const p of [".github/workflows/provider-fleet-runtime-state.yml",".github/workflows/browser-engine-runtime-evidence.yml",".github/workflows/live-chatbot-production-smoke.yml",".github/workflows/live-extractor-benchmark.yml",".github/workflows/b2-repository-backup.yml",".github/workflows/b2-restore-verification.yml"]) if(!fs.existsSync(path.join(foundationRoot,p))) addFinding(findings,"provider_runtime","integration","attention","canonical_runtime_surface_missing","One or more declared runtime surfaces are missing.",null,[p]);
    for(const p of ["private/search_provider_catalog.py","private/search_provider_capabilities.py","private/search_rate_limit.py","private/audit_rule_catalog.py","private/language_governance_policy.py","private/runtime_language_policy.py"]) if(!fs.existsSync(path.join(operationsRoot,p))) addFinding(findings,"provider_runtime","policy","critical","canonical_policy_surface_missing","Canonical policy surface is missing.",null,[p]);
    for(const [label,tokens] of Object.entries({cloudflare:["cloudflare","workers ai","browser run","d1"],b2:["backblaze","b2"],api:["api_provider","provider_runtime"],search:["search_provider","search_rate_limit"]})){ const hits=O.filter(r=>r.text&&tokens.some(q=>r.text.toLowerCase().includes(q))).map(r=>r.path); if(!hits.length) addFinding(findings,"provider_runtime",label,"attention","runtime_surface_missing","No tracked Operations text surface references the "+label+" plane."); }
    addFinding(findings,"provider_runtime","provider","info","provider_fleet_inventory","Provider task-fabric provider families observed.",{count:providers.size,providers:[...providers].sort()});
  }

  if(["all","work_items_workflow"].includes(lane)){
    for(const repo of ["foundation","operations"]){ const issues=snapshot[repo]?.issues||[], prs=snapshot[repo]?.prs||[], staleI=issues.filter(x=>x.updatedAt&&ageDays(x.updatedAt,now)>=30), staleP=prs.filter(x=>x.updatedAt&&ageDays(x.updatedAt,now)>=7); if(staleI.length) addFinding(findings,"work_items_workflow","issues","attention","stale_open_issues",repo+" has open issues unchanged for at least 30 days.",{count:staleI.length,issues:staleI.slice(0,20).map(x=>x.number)}); if(staleP.length) addFinding(findings,"work_items_workflow","prs","attention","stale_open_prs",repo+" has open PRs unchanged for at least 7 days.",{count:staleP.length,prs:staleP.slice(0,20).map(x=>x.number)}); const auto=issues.filter(x=>String(x.title||"").startsWith("[autonomous-")); if(auto.length) addFinding(findings,"work_items_workflow","autonomy","info","autonomous_issue_inventory",repo+" has active autonomous mission issues.",{count:auto.length}); }
    const wf=F.filter(r=>r.path.startsWith(".github/workflows/")).map(r=>r.path), feed=wf.filter(x=>/woocommerce|feed/i.test(x)); if(feed.length>=8) addFinding(findings,"work_items_workflow","workflow_sprawl","attention","feed_workflow_scatter","Large feed workflow family requires canonical-vs-historical reconciliation.",{workflow_count:feed.length});
  }

  if(["all","maps_docs_policy"].includes(lane)){
    const matrix=loadJson(path.join(foundationRoot,"docs/PROJECT_IMPROVEMENT_MATRIX.json"))||{}, contract=loadJson(path.join(foundationRoot,"docs/SYSTEM_INTEGRATION_CONTRACT.json"))||{}, comps=matrix.components||{}, controls=Object.keys(contract.cross_cutting_controls||{}).sort();
    const required=["owner","canonical_paths","workflows","ai_task_families","evidence","cross_cutting_controls","evidence_contract"];
    for(const [name,component] of Object.entries(comps)){ const missing=required.filter(k=>!component?.[k]); if(missing.length) addFinding(findings,"maps_docs_policy","matrix","critical","component_contract_incomplete","Project component "+name+" is missing required improvement-matrix fields.",{missing_fields:missing}); }
    const fabric=loadJson(path.join(operationsRoot,"docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.json"))||{}, fabricTasks=new Set(fabric.task_families||[]), matrixTasks=new Set(Object.values(comps).flatMap(v=>v.ai_task_families||[])), missingTasks=[...matrixTasks].filter(x=>!fabricTasks.has(x)).sort(); if(missingTasks.length) addFinding(findings,"maps_docs_policy","ai_task_family","critical","task_family_parity","Project matrix task families are missing from the Operations task fabric.",{missing:missingTasks});
    const reviewCells=Object.keys(comps).length*controls.length*Math.max(fabricTasks.size,1); addFinding(findings,"maps_docs_policy","cross_product","info","bounded_feature_policy_cross_product","Bounded component×control×task-family review space.",{components:Object.keys(comps).length,controls:controls.length,task_families:fabricTasks.size,review_cells:reviewCells});
    let pairs=0,covered=0; for(const [name,d] of Object.entries(comps)){ for(const p of d.canonical_paths||[]){ let pp=p, roots=[foundationRoot,operationsRoot]; if(pp.startsWith("private/")) roots=[operationsRoot]; if(pp.startsWith("foundation/")){roots=[foundationRoot];pp=pp.slice(11);} if(pp.startsWith("operations/")){roots=[operationsRoot];pp=pp.slice(11);} if(!roots.some(root=>globExists(root,pp))) addFinding(findings,"maps_docs_policy","directory","attention","dangling_canonical_path","Component "+name+" declares a missing canonical path.",{path:p}); } const dc=new Set(d.cross_cutting_controls||[]); for(const control of controls){pairs++; if(dc.has(control)) covered++;} }
    addFinding(findings,"maps_docs_policy","cross_product","info","component_control_pair_coverage","Declared component×cross-cutting-control coverage.",{pairs,covered,coverage_percent:pairs?Number((covered/pairs*100).toFixed(1)):100});
    for(const p of contract.required_cross_repo_anchors?.foundation||[]) if(!fs.existsSync(path.join(foundationRoot,p))) addFinding(findings,"maps_docs_policy","integration","critical","missing_foundation_anchor","Required Foundation anchor is missing.",null,[p]);
    for(const p of contract.required_cross_repo_anchors?.operations||[]) if(!globExists(operationsRoot,p)) addFinding(findings,"maps_docs_policy","integration","critical","missing_operations_anchor","Required Operations anchor is missing.",null,[p]);
  }

  if(["all","quality_learning_evolution"].includes(lane)){
    const contract=loadJson(path.join(foundationRoot,"docs/SYSTEM_INTEGRATION_CONTRACT.json"))||{}, gates=new Set(contract.cross_cutting_controls?.quality?.hard_gates||[]);
    if(!gates.has("security_policy")||!gates.has("provenance")) addFinding(findings,"quality_learning_evolution","quality","critical","quality_hard_gate_incomplete","Quality authority is missing the required security_policy/provenance hard gates.",{hard_gates:[...gates].sort()});
    for(const p of ["private/evolution_score.py","private/evolution_engine.py","private/evolution_integration.py","private/self_evolution_boundary.py","private/strategy_matrix.py","private/ai_maintainability_policy.py","private/language_fit_policy.py","private/migration_artifact_policy.py","private/audit_rule_catalog.py","private/chatbot/chat_learning.py","private/chatbot/chat_learning_index.py","private/chatbot/feedback_evaluation_bridge.py","docs/PROJECT_OBSERVABILITY_AND_EVOLUTION.md","docs/FEATURE_SURFACE_GOVERNANCE_POLICY.json"]) if(!fs.existsSync(path.join(operationsRoot,p))) addFinding(findings,"quality_learning_evolution","evolution","critical","missing_evolution_policy_anchor","Canonical evolution/learning/score policy anchor is missing.",null,[p]);
  }

  if(["all","performance_resources"].includes(lane)){
    const runs=[]; for(const repo of ["foundation","operations"]) for(const r of snapshot[repo]?.runs||[]){ const start=r.run_started_at||r.created_at,end=r.updated_at; if(!start||!end) continue; const seconds=(Date.parse(String(end))-Date.parse(String(start)))/1000; if(Number.isFinite(seconds)) runs.push({seconds,repo,name:r.name,id:r.id}); }
    if(runs.length) addFinding(findings,"performance_resources","execution","info","workflow_duration_inventory","Recent workflow duration inventory captured.",{sampled_runs:runs.length,max_seconds:Number(Math.max(...runs.map(x=>x.seconds)).toFixed(1))});
    const slow=runs.filter(x=>x.seconds>=600); if(slow.length) addFinding(findings,"performance_resources","execution","attention","slow_workflow_runs","Recent workflow runs include executions of ten minutes or more.",{count:slow.length,runs:slow.sort((a,b)=>b.seconds-a.seconds).slice(0,15).map(x=>({...x,seconds:Number(x.seconds.toFixed(1))}))});
  }
  if(lane==="all"){ const canonical=[".github/workflows/family-full-coverage.yml",".github/workflows/cross-repository-contract-drift.yml",".github/workflows/exhaustive-six-lane-audit.yml",".github/workflows/polyglot-migration-review.yml",".github/workflows/project-improvement-supervisor.yml",".github/workflows/autonomous-engineering-supervisor.yml"], miss=canonical.filter(p=>!fs.existsSync(path.join(foundationRoot,p))); if(miss.length) addFinding(findings,"automation","coverage","critical","canonical_automation_missing","Existing canonical automation is missing.",null,miss); }
  return {schema:"comprehensive-governance-scan/v1",generated_at:new Date(now).toISOString(),lane,repos:{foundation:{tracked_files:F.length},operations:{tracked_files:O.length}},coverage:{finding_count:findings.length,critical_findings:findings.filter(x=>x.severity==="critical").length,attention_findings:findings.filter(x=>x.severity==="attention").length,telemetry_status:"descriptive_only"},findings,cross_fire_lanes:LANES,authority_note:"Observation/governance overlay only. Existing component, policy, evidence, promotion and release authorities remain canonical."};
}
if(fileURLToPath(import.meta.url)===process.argv[1]){
  const a=argMap(process.argv.slice(2)); if(!a.foundation||!a.operations||!a.output) throw new Error("--foundation --operations --output are required");
  const result=buildScan(path.resolve(a.foundation),path.resolve(a.operations),a.snapshot?loadJson(path.resolve(a.snapshot))||{}:{} ,a.lane||"all");
  fs.mkdirSync(path.dirname(path.resolve(a.output)),{recursive:true}); fs.writeFileSync(path.resolve(a.output),JSON.stringify(result,null,2)+"\n"); console.log(JSON.stringify(result.coverage));
}
