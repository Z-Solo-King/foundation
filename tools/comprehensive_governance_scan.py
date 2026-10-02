#!/usr/bin/env python3
"""Comprehensive cross-fire governance scanner; report only."""
from __future__ import annotations
import argparse, collections, hashlib, json, re, subprocess
from datetime import datetime, timezone
from pathlib import Path

SOURCE={".py",".pyi",".js",".mjs",".cjs",".ts",".tsx",".jsx",".rs",".go",".php",".rb",".java",".kt",".swift",".c",".cpp",".h",".hpp",".sh",".ps1"}
TEXT=SOURCE|{".md",".rst",".txt",".json",".jsonc",".yaml",".yml",".toml",".ini",".cfg",".xml",".html",".css",".scss",".sql"}
HIST=("/history/","/feed-lab/","/runtime/")
LANES=("structure_hygiene","migration_boundary","research_feed","provider_runtime","work_items_workflow","maps_docs_policy","quality_learning_evolution","performance_resources")

def sh(cmd,cwd): return subprocess.run(cmd,cwd=cwd,text=True,capture_output=True,check=True).stdout
def tracked(root): return [x for x in sh(["git","ls-files","-z"],root).split("\0") if x]
def inv(root):
    out=[]
    for rel in tracked(root):
        p=root/rel
        if not p.is_file(): continue
        b=p.read_bytes(); t=None
        if p.suffix.lower() in TEXT or p.name in {"README.md","AGENTS.md","Dockerfile","Containerfile","Makefile","Caddyfile"}:
            try:t=b.decode()
            except UnicodeDecodeError: pass
        out.append({"path":rel,"bytes":len(b),"lines":(t.count("\n")+1 if t else None),"sha":hashlib.sha256(b).hexdigest(),"text":t})
    return out
def hist(p): return any(x in ("/"+p.lower()) for x in HIST)
def add(fs,lane,cat,sev,code,summary,details=None,paths=None):
    x={"lane":lane,"category":cat,"severity":sev,"code":code,"summary":summary}
    if details is not None:x["details"]=details
    if paths:x["paths"]=paths[:25]
    x["finding_id"]=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()[:16]
    fs.append(x)
def j(path):
    try:return json.loads(path.read_text(encoding="utf-8"))
    except Exception:return None
def exists(root,p):
    if any(c in p for c in "*?["): return bool(list(root.glob(p)))
    return (root/p).exists()
def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--foundation",type=Path,required=True); ap.add_argument("--operations",type=Path,required=True)
    ap.add_argument("--snapshot",type=Path); ap.add_argument("--lane",choices=("all",)+LANES,default="all"); ap.add_argument("--output",type=Path,required=True)
    a=ap.parse_args(); fs=[]; lane=a.lane; now=datetime.now(timezone.utc)
    F,O=inv(a.foundation),inv(a.operations); snap=j(a.snapshot) if a.snapshot and a.snapshot.exists() else {}
    rows={"foundation":F,"operations":O}

    if lane in ("all","structure_hygiene"):
        for repo,rs in rows.items():
            dup=collections.defaultdict(list); big=[]
            for r in rs:
                dup[r["sha"]].append(r["path"])
                if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"]) and ((r["lines"] or 0)>1000 or r["bytes"]>50000): big.append(r)
            attention_big=[r for r in rs if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"]) and ((r["lines"] or 0)>500 or r["bytes"]>25000)]
            for paths in dup.values():
                paths=[p for p in paths if Path(p).suffix.lower() in SOURCE|{".md"} and not hist(p)]
                if len(paths)>1:add(fs,"structure_hygiene","duplicate","attention","exact_duplicate_content",f"{repo} has exact duplicate tracked content.",paths=paths)
            if big:add(fs,"structure_hygiene","large_code","critical","critical_source_size",f"{repo} has source beyond the critical size threshold.",{"count":len(big)},[x["path"] for x in big])
            if attention_big and not big:add(fs,"structure_hygiene","large_code","attention","attention_source_size",f"{repo} has source beyond the attention size threshold.",{"count":len(attention_big)},[x["path"] for x in attention_big[:50]])
            names=collections.defaultdict(list)
            for r in rs:
                if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"]) and Path(r["path"]).name!="__init__.py":names[Path(r["path"]).name].append(r["path"])
            for n,ps in names.items():
                if len(ps)>=3:add(fs,"structure_hygiene","scattering","attention","duplicate_basename_family",f"{repo} has a source basename scattered across multiple live directories.",{"basename":n},ps)
        for r in F:
            if r["path"].startswith(".github/workflows/") and r["path"].endswith((".yml",".yaml")):
                t=r["text"] or ""
                if "permissions:" not in t:add(fs,"structure_hygiene","workflow","attention","missing_permissions_block",f"Workflow {r['path']} has no explicit permissions block.",paths=[r["path"]])
                for m in re.finditer(r"^\s*-\s*uses:\s*([^@\s]+)@([^\s#]+)",t,re.M):
                    if not re.fullmatch(r"[0-9a-fA-F]{40}",m.group(2)):add(fs,"structure_hygiene","workflow","critical","unpinned_action",f"Workflow {r['path']} contains an unpinned action.",{"action":m.group(1),"ref":m.group(2)},[r["path"]])
                if re.search(r"cron:\s*[\"']?0(?:\s|$)",t):add(fs,"structure_hygiene","workflow","attention","hour_boundary_schedule",f"Workflow {r['path']} is scheduled at the top of an hour.",paths=[r["path"]])

    if lane in ("all","structure_hygiene"):
        allow = {".editorconfig",".gitattributes",".prettierrc.json",".prettierignore",".markdownlint.json","docs/REPOSITORY_HYGIENE_FORMAT_CONTRACT.json"}
        f_by_sha=collections.defaultdict(list); o_by_sha=collections.defaultdict(list)
        for r in F:
            if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"]) and r["path"] not in allow:f_by_sha[r["sha"]].append(r["path"])
        for r in O:
            if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"]) and r["path"] not in allow:o_by_sha[r["sha"]].append(r["path"])
        for shared_sha in sorted(set(f_by_sha) & set(o_by_sha)):
            add(fs,"structure_hygiene","duplicate","attention","cross_repo_duplicate_content","Foundation and Operations contain identical live source content, creating possible duplicate authority.",{"hash":shared_sha},f_by_sha[shared_sha][:12]+o_by_sha[shared_sha][:12])
        registry=j(a.foundation/"docs/WORKFLOW_AUTHORITY_REGISTRY.json") or {}
        registered={pair[0] for pair in registry.get("explicit_privileged_workflows",[]) if isinstance(pair,list) and pair}
        for r in F:
            if not r["path"].startswith(".github/workflows/") or not r["path"].endswith((".yml",".yaml")): continue
            t=r["text"] or ""
            if ("secrets." in t or "actions/create-github-app-token" in t or "Z-Solo-King/operations" in t) and r["path"] not in registered:
                add(fs,"structure_hygiene","workflow","critical","unregistered_privileged_workflow","Privileged workflow is not present in the machine-checkable authority registry.",paths=[r["path"]])
    if lane in ("all","migration_boundary"):
        registry=j(a.operations/"polyglot/REGISTRY.json") or {}
        evidence_matrix=j(a.operations/"docs/MIGRATION_EVIDENCE_MATRIX.json") or {}
        required=list(evidence_matrix.get("required_gates") or [])
        evidence_by_id={item.get("id"):item for item in evidence_matrix.get("candidates",[]) if isinstance(item,dict) and item.get("id")}
        for candidate in registry.get("candidates",[]):
            cid=candidate.get("id") if isinstance(candidate,dict) else None
            if not cid: continue
            item=evidence_by_id.get(cid)
            if not item:
                add(fs,"migration_boundary","evidence","critical","migration_candidate_missing_evidence","Registered migration candidate has no matching evidence-matrix record.",{"candidate_id":cid})
                continue
            evidence=item.get("evidence") or {}
            missing=[gate for gate in required if evidence.get(gate) is not True and gate not in {"frozen corpus"}]
            if missing and str(item.get("status","")).lower() in {"evidence_complete","candidate_ready","recorded"}:
                add(fs,"migration_boundary","evidence","attention","migration_gate_incomplete","Migration candidate is marked active/recorded while required promotion gates remain incomplete.",{"candidate_id":cid,"status":item.get("status"),"missing_gates":missing[:20]})
        runtime_set=((registry.get("registry_policy") or {}).get("active_diversity") or {}).get("current_runtime_set") or []
        if "python" not in runtime_set:
            add(fs,"migration_boundary","authority","critical","python_runtime_authority_missing","Migration registry no longer declares Python in the protected current runtime set.",{"current_runtime_set":runtime_set})
        cnt={repo:collections.Counter(Path(r["path"]).suffix.lower() for r in rs if Path(r["path"]).suffix.lower() in SOURCE and not hist(r["path"])) for repo,rs in rows.items()}
        add(fs,"migration_boundary","language","info","language_distribution","Current source-language distribution captured.",{k:dict(v) for k,v in cnt.items()})
        priv=[r["path"] for r in F if r["path"].startswith("private/")]
        if priv:add(fs,"migration_boundary","public_private","critical","private_tree_in_public_repo","Foundation still tracks private-tree paths.",paths=priv)
        secret=[r["path"] for r in F if re.search(r"(^|/)[^/]*(API[_-]?KEY|PRIVATE[_-]?KEY|SECRET|TOKEN)[^/]*$",r["path"],re.I)]
        if secret:add(fs,"migration_boundary","public_private","critical","secret_like_filename_public","Foundation contains secret-like tracked filenames.",paths=secret)
        if not exists(a.operations,"private/runtime_language_policy.py"):add(fs,"migration_boundary","policy","critical","language_authority_missing","Runtime language authority policy is missing.")
        if not (a.operations/"polyglot/REGISTRY.json").exists():add(fs,"migration_boundary","registry","attention","migration_registry_missing","Migration candidate registry is missing.")

    if lane in ("all","research_feed"):
        WF={r["path"] for r in F}
        need=[".github/workflows/nightly-multi-agent-research-v3.yml",".github/workflows/nightly-research-provider-preflight.yml",".github/workflows/native-google-feed-hunt.yml",".github/workflows/woocommerce-clean-recovery.yml",".github/workflows/woocommerce-identified-family-exhaustive-v5.yml"]
        miss=[p for p in need if p not in WF]
        if miss:add(fs,"research_feed","authority","critical","canonical_research_feed_workflow_missing","Canonical research/feed workflow is missing.",paths=miss)
        titles=" ".join(x.get("title","") for repo in ("foundation","operations") for x in (snap.get(repo,{}).get("issues") or [])).lower()
        if "24-program" not in titles:add(fs,"research_feed","work_items","attention","nightly_research_issue_not_visible","Live metadata did not expose the 24-program research tracker.")
        if "google feed" not in titles:add(fs,"research_feed","work_items","attention","feed_issue_not_visible","Live metadata did not expose a Google-feed tracker.")

    if lane in ("all","provider_runtime"):
        fabric=j(a.operations/"docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.json") or {}
        providers=set(fabric.get("external_providers") or [])
        if not (a.operations/"tools/provider_fleet_runtime_probe.py").exists():add(fs,"provider_runtime","provider","critical","provider_probe_missing","Canonical provider runtime probe is missing.")
        for p in ("private/search_provider_catalog.py","private/search_provider_capabilities.py","private/search_rate_limit.py","private/search_route_policy.py","private/search_provider_execution.py"):
            if not (a.operations/p).exists():add(fs,"provider_runtime","search","critical","search_authority_missing",f"Search/evidence authority missing: {p}",paths=[p])
        if not (a.operations/"private/chatbot/chat_endpoint.py").exists():add(fs,"provider_runtime","chatbot","critical","chatbot_boundary_missing","Canonical chatbot endpoint is missing.")
        required_runtime_surfaces=[
            ".github/workflows/provider-fleet-runtime-state.yml",
            ".github/workflows/browser-engine-runtime-evidence.yml",
            ".github/workflows/live-chatbot-production-smoke.yml",
            ".github/workflows/live-extractor-benchmark.yml",
            ".github/workflows/b2-repository-backup.yml",
            ".github/workflows/b2-restore-verification.yml",
        ]
        missing_runtime_surfaces=[path for path in required_runtime_surfaces if not (a.foundation/path).exists()]
        if missing_runtime_surfaces:add(fs,"provider_runtime","integration","attention","canonical_runtime_surface_missing","One or more declared Cloudflare/B2/browser/chatbot/extractor runtime surfaces are missing.",paths=missing_runtime_surfaces)
        required_policy_surfaces=[
            "private/search_provider_catalog.py",
            "private/search_provider_capabilities.py",
            "private/search_rate_limit.py",
            "private/audit_rule_catalog.py",
            "private/language_governance_policy.py",
            "private/runtime_language_policy.py",
        ]
        missing_policy_surfaces=[path for path in required_policy_surfaces if not (a.operations/path).exists()]
        if missing_policy_surfaces:add(fs,"provider_runtime","policy","critical","canonical_policy_surface_missing","Canonical search/rules/language policy surfaces are missing.",paths=missing_policy_surfaces)
        for label,tokens in {"cloudflare":["cloudflare","workers ai","browser run","d1"],"b2":["backblaze","b2"],"api":["api_provider","provider_runtime"],"search":["search_provider","search_rate_limit"]}.items():
            hits=[r["path"] for r in O if r["text"] and any(q in r["text"].lower() for q in tokens)]
            if not hits:add(fs,"provider_runtime",label,"attention","runtime_surface_missing",f"No tracked Operations text surface references the {label} plane.")
        add(fs,"provider_runtime","provider","info","provider_fleet_inventory","Provider task-fabric provider families observed.",{"count":len(providers),"providers":sorted(providers)})

    if lane in ("all","work_items_workflow"):
        for repo in ("foundation","operations"):
            issues=snap.get(repo,{}).get("issues") or []; prs=snap.get(repo,{}).get("prs") or []
            def age(x):
                try:return (now-datetime.fromisoformat(x.replace("Z","+00:00"))).days
                except Exception:return 0
            stale_i=[x for x in issues if x.get("updatedAt") and age(x["updatedAt"])>=30]
            stale_p=[x for x in prs if x.get("updatedAt") and age(x["updatedAt"])>=7]
            if stale_i:add(fs,"work_items_workflow","issues","attention","stale_open_issues",f"{repo} has open issues unchanged for at least 30 days.",{"count":len(stale_i),"issues":[x.get("number") for x in stale_i[:20]]})
            if stale_p:add(fs,"work_items_workflow","prs","attention","stale_open_prs",f"{repo} has open PRs unchanged for at least 7 days.",{"count":len(stale_p),"prs":[x.get("number") for x in stale_p[:20]]})
            auto=[x for x in issues if str(x.get("title","")).startswith("[autonomous-")]
            if auto:add(fs,"work_items_workflow","autonomy","info","autonomous_issue_inventory",f"{repo} has active autonomous mission issues.",{"count":len(auto)})
        wf=[r["path"] for r in F if r["path"].startswith(".github/workflows/") and r["path"].endswith((".yml",".yaml"))]
        feed=[x for x in wf if "woocommerce" in x.lower() or "feed" in x.lower()]
        if len(feed)>=8:add(fs,"work_items_workflow","workflow_sprawl","attention","feed_workflow_scatter","Large feed workflow family requires canonical-vs-historical reconciliation.",{"workflow_count":len(feed)})

    if lane in ("all","maps_docs_policy"):
        matrix=j(a.foundation/"docs/PROJECT_IMPROVEMENT_MATRIX.json") or {}; contract=j(a.foundation/"docs/SYSTEM_INTEGRATION_CONTRACT.json") or {}
        comps=matrix.get("components") or {}; controls=sorted((contract.get("cross_cutting_controls") or {}).keys())
        required_component_fields=("owner","canonical_paths","workflows","ai_task_families","evidence","cross_cutting_controls","evidence_contract")
        for name,component in comps.items():
            missing_fields=[field for field in required_component_fields if not component.get(field)]
            if missing_fields:
                add(fs,"maps_docs_policy","matrix","critical","component_contract_incomplete",f"Project component {name} is missing required improvement-matrix fields.",{"missing_fields":missing_fields})
        fabric=j(a.operations/"docs/AI_PROVIDER_TASK_FABRIC_2026-09-30.json") or {}
        fabric_tasks=set(fabric.get("task_families") or [])
        matrix_tasks=set().union(*(set(v.get("ai_task_families") or []) for v in comps.values()))
        missing_tasks=sorted(matrix_tasks-fabric_tasks)
        if missing_tasks:add(fs,"maps_docs_policy","ai_task_family","critical","task_family_parity","Project matrix task families are missing from the Operations task fabric.",{"missing":missing_tasks})
        product_space=len(comps)*len(controls)*max(len(fabric_tasks),1)
        add(fs,"maps_docs_policy","cross_product","info","bounded_feature_policy_cross_product","Bounded component×control×task-family review space.",{"components":len(comps),"controls":len(controls),"task_families":len(fabric_tasks),"review_cells":product_space})
        pairs=covered=0
        for name,d in comps.items():
            for p in d.get("canonical_paths") or []:
                pp=p
                roots=[a.foundation,a.operations]
                if pp.startswith("private/"):roots=[a.operations]
                if pp.startswith("foundation/"):roots=[a.foundation];pp=pp[len("foundation/"):]
                if pp.startswith("operations/"):roots=[a.operations];pp=pp[len("operations/"):]
                if not any(exists(root,pp) for root in roots):add(fs,"maps_docs_policy","directory","attention","dangling_canonical_path",f"Component {name} declares a missing canonical path.",{"path":p})
            dc=set(d.get("cross_cutting_controls") or [])
            for c in controls:pairs+=1;covered+=int(c in dc)
        add(fs,"maps_docs_policy","cross_product","info","component_control_pair_coverage","Declared component×cross-cutting-control coverage.",{"pairs":pairs,"covered":covered,"coverage_percent":round(covered/pairs*100,1) if pairs else 100.0})
        for p in contract.get("required_cross_repo_anchors",{}).get("foundation",[]):
            if not (a.foundation/p).exists():add(fs,"maps_docs_policy","integration","critical","missing_foundation_anchor","Required Foundation anchor is missing.",paths=[p])
        for p in contract.get("required_cross_repo_anchors",{}).get("operations",[]):
            if not exists(a.operations,p):add(fs,"maps_docs_policy","integration","critical","missing_operations_anchor","Required Operations anchor is missing.",paths=[p])

    if lane in ("all","quality_learning_evolution"):
        contract=j(a.foundation/"docs/SYSTEM_INTEGRATION_CONTRACT.json") or {}
        quality=(contract.get("cross_cutting_controls") or {}).get("quality") or {}
        gates=set(quality.get("hard_gates") or [])
        if not {"security_policy","provenance"}.issubset(gates):
            add(fs,"quality_learning_evolution","quality","critical","quality_hard_gate_incomplete","Quality authority is missing the required security_policy/provenance hard gates.",{"hard_gates":sorted(gates)})
        for p in ("private/evolution_score.py","private/evolution_engine.py","private/evolution_integration.py","private/self_evolution_boundary.py","private/strategy_matrix.py","private/ai_maintainability_policy.py","private/language_fit_policy.py","private/migration_artifact_policy.py","private/audit_rule_catalog.py"):
            if not (a.operations/p).exists():add(fs,"quality_learning_evolution","evolution","critical","missing_evolution_policy_anchor","Canonical evolution/policy anchor is missing.",paths=[p])
        if not (a.operations/"docs/FEATURE_SURFACE_GOVERNANCE_POLICY.json").exists():add(fs,"quality_learning_evolution","feature_policy","attention","feature_policy_matrix_missing","Feature/function/policy comparison contract is missing.")

    if lane in ("all","performance_resources"):
        rows_run=[]
        for repo in ("foundation","operations"):
            for r in snap.get(repo,{}).get("runs") or []:
                s=r.get("run_started_at") or r.get("created_at"); e=r.get("updated_at")
                if not s or not e:continue
                try:rows_run.append(((datetime.fromisoformat(e.replace("Z","+00:00"))-datetime.fromisoformat(s.replace("Z","+00:00"))).total_seconds(),repo,r.get("name"),r.get("id")))
                except ValueError:pass
        if rows_run:add(fs,"performance_resources","execution","info","workflow_duration_inventory","Recent workflow duration inventory captured.",{"sampled_runs":len(rows_run),"max_seconds":round(max(x[0] for x in rows_run),1)})
        slow=[x for x in rows_run if x[0]>=600]
        if slow:add(fs,"performance_resources","execution","attention","slow_workflow_runs","Recent workflow runs include executions of ten minutes or more.",{"count":len(slow),"runs":[{"seconds":round(s),"repo":repo,"name":name,"id":rid} for s,repo,name,rid in sorted(slow,reverse=True)[:15]]})

    if lane=="all":
        canonical=[".github/workflows/family-full-coverage.yml",".github/workflows/cross-repository-contract-drift.yml",".github/workflows/exhaustive-six-lane-audit.yml",".github/workflows/polyglot-migration-review.yml",".github/workflows/project-improvement-supervisor.yml",".github/workflows/autonomous-engineering-supervisor.yml"]
        miss=[p for p in canonical if not (a.foundation/p).exists()]
        if miss:add(fs,"automation","coverage","critical","canonical_automation_missing","Existing canonical automation is missing.",paths=miss)

    result={"schema":"comprehensive-governance-scan/v1","generated_at":now.isoformat().replace("+00:00","Z"),"lane":lane,
            "repos":{"foundation":{"tracked_files":len(F)},"operations":{"tracked_files":len(O)}},
            "coverage":{"finding_count":len(fs),"critical_findings":sum(x["severity"]=="critical" for x in fs),"attention_findings":sum(x["severity"]=="attention" for x in fs),"telemetry_status":"descriptive_only"},
            "findings":fs,"cross_fire_lanes":list(LANES),
            "authority_note":"Observation/governance overlay only. Existing component, policy, evidence, promotion and release authorities remain canonical."}
    a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result["coverage"]))
if __name__=="__main__":raise SystemExit(main())
