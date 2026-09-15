"""Deterministic 20-job nightly experiment matrix."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
CASES=("acquisition_html","api_xhr","identity_variants","contradiction_specs","price_stock","pagination_sitemap","images","blocking","multilingual","review_poisoning","freshness","comparison","missing_data","prompt_injection","repository_repair","vcs_comparison","assistant_ecosystem","agent_scaling","self_audit")
AGENTS=(1,2,4,6,7,8,10)

def build_matrix():
    rows=[]
    for i,case in enumerate(CASES):
        row={"job_index":i+1,"job_id":f"research-{i+1:02d}","case_id":case,"agent_budget":10 if case=="agent_scaling" else AGENTS[i%len(AGENTS)],"strict_zero_cost_only":True,"provenance_required":True,"chat_memory_authority":"candidate_only","production_controls_mutable":False}
        row["matrix_digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(); rows.append(row)
    row={"job_index":20,"job_id":"aggregator-20","case_id":"aggregate","agent_budget":1,"strict_zero_cost_only":True,"provenance_required":True,"chat_memory_authority":"candidate_only","production_controls_mutable":False}
    row["matrix_digest"]=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest(); rows.append(row)
    return rows

def write(path:Path):
    rows=build_matrix(); assert len(rows)==20 and len({r['job_id'] for r in rows})==20
    path.parent.mkdir(parents=True,exist_ok=True); path.write_text(json.dumps(rows,indent=2,sort_keys=True)+"\n",encoding="utf-8")
