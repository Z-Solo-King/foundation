#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"docs/OPERATIONS_PIN_MANIFEST.json"
SHA_RE=re.compile(r"\b[0-9a-f]{40}\b")
def main():
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    pins={v["revision"] for v in data["purpose_scoped_pins"].values()}
    violations=[]
    paths=list((ROOT/".github/workflows").glob("*.yml"))+[ROOT/"scripts/production_release.sh",ROOT/"DEPLOYMENT.md"]
    for path in paths:
        if not path.exists(): continue
        for n,line in enumerate(path.read_text(encoding="utf-8",errors="ignore").splitlines(),1):
            if "operations" not in line.lower() and "OPERATIONS" not in line:
                continue
            for sha in SHA_RE.findall(line):
                if sha not in pins and "actions/" not in line:
                    violations.append(f"{path.relative_to(ROOT)}:{n}:{sha}")
    if violations:
        print("Operations pin manifest drift:")
        print("\n".join(violations))
        return 1
    print(f"Operations pin manifest PASS: {len(pins)} purpose-scoped immutable revision(s)")
    return 0
if __name__=="__main__":
    raise SystemExit(main())
