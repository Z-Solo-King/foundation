#!/usr/bin/env python3
"""Scan the intentionally public documentation surface and PR metadata for high-risk private disclosures."""
from __future__ import annotations
import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_DOCS = (
    "README.md", "CHATGPT.md", "REPOSITORY_MAP.json",
    "docs/CURRENT_SOURCE_OF_TRUTH.md", "docs/FAMILY_SYNC_STATE.json",
    "docs/PROMPT_TO_CANONICAL_DOC_MAP.md", "docs/PUBLIC_SURFACE_POLICY.md",
    "docs/PUBLIC_SURFACE_POLICY.json",
)
HIGH_RISK = (
    (r"research-intelligence-engine-(?:private|public)", "legacy private Worker identity"),
    (r"heroic-ai\.dev", "non-canonical private/custom domain"),
    (r"heroic\.heroic-ai\.workers\.dev", "Worker origin URL"),
    (r"66cd52347a2a64648eb0f4cca8ac88b7", "Cloudflare account identifier"),
    (r"19f51638-47a5-4218-a9dc-73dbfd6156fe", "D1 resource identifier"),
    (r"(?i)github:[0-9a-f]{40}", "private revision provenance literal"),
    (r"(?i)OPERATIONS_(?:SECRET_SYNC_REF|REF|PRODUCTION_REF)\s*[:=]\s*[0-9a-f]{40}", "private revision configuration"),
)
WARN = (
    (r"Z-Solo-King/operations", "private repository reference"),
    (r"OPERATIONS_APP_PRIVATE_KEY", "credential identifier"),
)

@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    message: str

def scan_text(path: str, text: str) -> tuple[list[Finding], list[str]]:
    findings=[]
    warnings=[]
    for pattern, message in HIGH_RISK:
        if re.search(pattern, text):
            findings.append(Finding(path, "public-disclosure", message))
    for pattern, message in WARN:
        if re.search(pattern, text):
            warnings.append(f"{path}: {message}")
    return findings, warnings

def scan_metadata(payload: dict) -> tuple[list[Finding], list[str]]:
    text="\n".join(str(payload.get(k, "")) for k in ("title", "body"))
    commits=payload.get("commits", [])
    if isinstance(commits, list):
        text += "\n" + "\n".join(str(x) for x in commits)
    return scan_text('<pr-metadata>', text)

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--metadata-file")
    args=ap.parse_args()
    findings=[]
    warnings=[]
    for rel in PUBLIC_DOCS:
        path=ROOT/rel
        if path.exists():
            fs, ws=scan_text(rel, path.read_text(encoding='utf-8'))
            findings.extend(fs); warnings.extend(ws)
    if args.metadata_file:
        payload=json.loads(Path(args.metadata_file).read_text(encoding='utf-8'))
        fs, ws=scan_metadata(payload)
        findings.extend(fs); warnings.extend(ws)
    out={
        "schema_version":"public-surface-scan/v1",
        "files_checked":len([p for p in PUBLIC_DOCS if (ROOT/p).exists()]),
        "findings":[f"{f.path}: {f.rule}: {f.message}" for f in findings],
        "warnings":warnings,
        "passed":not findings,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 1 if args.strict and findings else 0

if __name__ == "__main__":
    raise SystemExit(main())
