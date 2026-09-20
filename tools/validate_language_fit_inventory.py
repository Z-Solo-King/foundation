#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_language_fit_inventory.py PATH", file=sys.stderr)
        return 2
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    assert data["rows"] > 0, "family inventory is empty"
    assert all(row.get("coverage_status") == "covered" for row in data["artifacts"]), "uncovered artifact row detected"
    assert all(row.get("language_fit") for row in data["artifacts"]), "artifact missing language scores"
    for repo, summary in data["repositories"].items():
        assert summary["files"] > 0, f"{repo} has no covered artifacts"
    print(json.dumps({"rows": data["rows"], "repositories": data["repositories"], "coverage": "100% of inventoried engineering artifacts"}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())