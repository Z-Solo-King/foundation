#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from benchmark.instruction_audit import audit_instruction_files


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit agent instruction files")
    parser.add_argument("--output", default=".runtime/instruction-audit.json")
    parser.add_argument("paths", nargs="*", default=["AGENTS.md", "CLAUDE.md"])
    args = parser.parse_args()
    findings = audit_instruction_files(args.paths)
    payload = {
        "schema": "instruction-audit/v1",
        "checked_paths": args.paths,
        "finding_count": len(findings),
        "findings": [
            {"kind": f.kind, "document": f.document, "line": f.line, "detail": f.detail}
            for f in findings
        ],
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"finding_count": len(findings), "output": str(output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
