#!/usr/bin/env python3
from __future__ import annotations
import json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SHA_RE=re.compile(r"^[0-9a-f]{40}$")
def load_manifest():
    data=json.loads((ROOT/"docs/OPERATIONS_PIN_MANIFEST.json").read_text(encoding="utf-8"))
    assert data["schema"]=="operations-pin-manifest/v1"
    for item in data["pins"].values(): assert SHA_RE.fullmatch(item["sha"])
    assert data["rules"]["mutable_refs_forbidden"] is True
    return data
def main():
    m=load_manifest()
    prod=m["pins"]["production_runtime"]["sha"]; research=m["pins"]["research_runtime"]["sha"]; secret_sync_revision=m["pins"]["secret_sync_utility"]["sha"]
    production=(ROOT/"scripts/production_release.sh").read_text(encoding="utf-8")
    nightly=(ROOT/".github/workflows/nightly-multi-agent-research-v3.yml").read_text(encoding="utf-8")
    sync=(ROOT/".github/workflows/sync-secrets.yml").read_text(encoding="utf-8")
    assert "OPERATIONS_PIN_MANIFEST.json" in production
    assert ("OPERATIONS_RESEARCH_REF: "+research) in nightly
    assert ("OPERATIONS_SECRET_SYNC_REF: "+secret_sync_revision) in sync
    print(json.dumps({"ok":True,"production_runtime_pinned":bool(prod),"research_runtime_pinned":bool(research),"secret_sync_utility_pinned":bool(secret_sync_revision)},sort_keys=True))
if __name__=="__main__": main()
