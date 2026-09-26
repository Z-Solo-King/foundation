#!/usr/bin/env python3
from __future__ import annotations
import argparse
import subprocess
from pathlib import Path

REQUIRED_DOCS = (Path("docs/CURRENT_SOURCE_OF_TRUTH.md"), Path("docs/FAMILY_SYNC_STATE.json"))
CANONICAL_PREFIXES = ("backend/","foundation_core/","frontend/","migrations/","polyglot/",".github/workflows/")
CANONICAL_FILES = {"CAPABILITIES.json","REPOSITORY_MAP.json","worker.py","wrangler.toml"}

def changed_files(base_sha: str, head_sha: str) -> list[str]:
    probe=subprocess.run(["git","cat-file","-e",f"{base_sha}^{{commit}}"],check=False,capture_output=True,text=True)
    if probe.returncode != 0:
        fetch=subprocess.run(["git","fetch","--no-tags","origin",base_sha],check=False,capture_output=True,text=True)
        if fetch.returncode != 0:
            raise SystemExit(
                f"continuity-freshness: cannot materialize base revision {base_sha}: "
                f"{fetch.stderr.strip() or fetch.stdout.strip()}"
            )
    result=subprocess.run(["git","diff","--name-only","--diff-filter=ACMRT",f"{base_sha}..{head_sha}"],check=True,capture_output=True,text=True)
    return [x.strip() for x in result.stdout.splitlines() if x.strip()]

def is_canonical_change(path: str) -> bool:
    return path in CANONICAL_FILES or any(path.startswith(p) for p in CANONICAL_PREFIXES)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--base-sha",required=True)
    ap.add_argument("--head-sha",default="HEAD")
    a=ap.parse_args()
    files=changed_files(a.base_sha,a.head_sha)
    canonical=[p for p in files if is_canonical_change(p)]
    if not canonical:
        print("continuity-freshness: PASS (no canonical behavior/authority files changed)")
        return 0
    missing=[str(p) for p in REQUIRED_DOCS if not p.exists()]
    stale=[str(p) for p in REQUIRED_DOCS if str(p) not in set(files)]
    if missing or stale:
        print({"status":"FAIL","canonical_changes":canonical,"missing_required_docs":missing,"required_docs_not_updated":stale})
        return 1
    print({"status":"PASS","canonical_changes":canonical,"required_docs_updated":[str(p) for p in REQUIRED_DOCS]})
    return 0

if __name__=="__main__":
    raise SystemExit(main())
