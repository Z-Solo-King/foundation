#!/usr/bin/env python3
"""Fail-closed scan of the public Foundation surface for private disclosures."""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROOT_PUBLIC_FILES = (
    "README.md",
    "CHATGPT.md",
    "DEPLOYMENT.md",
    "SECURITY.md",
    "REPOSITORY_MAP.json",
)
DOC_SUFFIXES = {".md", ".json"}
WORKFLOW_SUFFIXES = {".yml", ".yaml"}
FORBIDDEN_TARGET_SURFACES = (
    "tools/woocommerce_google_feed_*.mjs",
    "tools/custom_api_google_feed_*.mjs",
    "data/feed_lab/custom_api_google_feed_registry_*.json",
    ".github/workflows/woocommerce-google-feed-recovery-*.yml",
    ".github/workflows/custom-api-google-feed-recovery-*.yml",
)
HIGH_RISK = (
    (r"research-intelligence-engine-(?:private|public)", "legacy private Worker identity"),
    (r"heroic-ai\.dev", "live custom-domain identifier"),
    (r"https?://[A-Za-z0-9.-]+\.workers\.dev(?:[/A-Za-z0-9_.?=&%:-]*)?", "live Workers.dev origin"),
    (r"\bSuper Administrator\s*-\s*All Privileges\b", "privileged Cloudflare account role"),
    (r"\bCloudflare account(?: ID| identifier)?\s*[:=]?\s*[0-9a-f]{32}\b", "Cloudflare account identifier"),
    (r"\bD1 (?:database )?(?:ID|identifier)\s*[:=]?\s*[0-9a-f-]{36}\b", "D1 resource identifier"),
    (r"(?i)(?:version ID|deployment ID)\s*[:=]?\s*[0-9a-f]{8}-[0-9a-f-]{27,}\b", "Cloudflare version/deployment identifier"),
    (r"(?i)\b(?:deployed )?Operations provenance\b[^\n]*\b[0-9a-f]{40}\b", "private Operations deployment provenance"),
    (r"(?i)github:[0-9a-f]{40}", "private revision provenance literal"),
    (r'(?im)^\s*["\']?(?:live_d1_counts|d1_counts|live_d1_row_counts)["\']?\s*:\s*\{[^{}]*\b(?:count|total|rows|observations|reservations)\b\s*[:=]\s*[0-9]+', "live D1 operational counts"),
    (r"(?i)cloudflare nameservers?\s*[:=]", "Cloudflare nameserver disclosure"),
    (r"(?i)Worker-managed .*?(?:AAAA|edge address)\s*[:=]", "Worker edge-address disclosure"),
    (r"(?i)BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY", "private key material"),
    (r"(?i)\b(?:github_pat_|ghp_|gho_|ghu_|ghs_|ghr_)[A-Za-z0-9_]{20,}\b", "GitHub credential material"),
)
WARN = (
    (r"Z-Solo-King/operations", "private repository reference"),
    (r"OPERATIONS_APP_PRIVATE_KEY", "credential identifier"),
    (r"\b(?:GH_ADMIN_TOKEN|CF_API_TOKEN|CF_ACCOUNT_ID|PROVIDER_KEYS_JSON)\b", "credential identifier"),
)

@dataclass(frozen=True)
class Finding:
    path: str
    rule: str
    message: str


def public_paths() -> tuple[str, ...]:
    paths = set(ROOT_PUBLIC_FILES)
    docs_root = ROOT / "docs"
    if docs_root.exists():
        for path in docs_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in DOC_SUFFIXES:
                paths.add(path.relative_to(ROOT).as_posix())
    workflows_root = ROOT / ".github" / "workflows"
    if workflows_root.exists():
        for path in workflows_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in WORKFLOW_SUFFIXES:
                paths.add(path.relative_to(ROOT).as_posix())
    return tuple(sorted(path for path in paths if (ROOT / path).exists()))


def scan_text(path: str, text: str) -> tuple[list[Finding], list[str]]:
    findings: list[Finding] = []
    warnings: list[str] = []
    for pattern, message in HIGH_RISK:
        # Immutable Operations pins are build inputs, not runtime provenance; only
        # historical documentation/records are subject to the private-revision rule.
        if message in {
            "private Operations deployment provenance",
            "private revision provenance literal",
        } and path.startswith(".github/workflows/"):
            continue
        if re.search(pattern, text):
            findings.append(Finding(path, "public-disclosure", message))
    for pattern, message in WARN:
        if re.search(pattern, text):
            warnings.append(f"{path}: {message}")
    return findings, warnings


def scan_path_rules(path: str) -> list[Finding]:
    return [
        Finding(
            path,
            "forbidden-public-target-surface",
            "live feed-recovery target tooling must live on private Operations",
        )
        for pattern in FORBIDDEN_TARGET_SURFACES
        if fnmatch(path, pattern)
    ]


def scan_metadata(payload: dict) -> tuple[list[Finding], list[str]]:
    text = "\n".join(str(payload.get(k, "")) for k in ("title", "body"))
    commits = payload.get("commits", [])
    if isinstance(commits, list):
        text += "\n" + "\n".join(str(x) for x in commits)
    return scan_text("<pr-metadata>", text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--metadata-file")
    args = ap.parse_args()

    findings: list[Finding] = []
    warnings: list[str] = []
    paths = public_paths()

    for rel in paths:
        findings.extend(scan_path_rules(rel))
        path = ROOT / rel
        fs, ws = scan_text(rel, path.read_text(encoding="utf-8"))
        findings.extend(fs)
        warnings.extend(ws)

        if rel.startswith("docs/CUSTOM_API_GOOGLE_FEED_LIVE_RECEIPT_") or rel.startswith("docs/WOOCOMMERCE_GOOGLE_FEED_RECOVERY_"):
            if re.search(r"https?://", path.read_text(encoding="utf-8")):
                findings.append(Finding(rel, "public-disclosure", "live feed target URL in public recovery record"))

    if args.metadata_file:
        payload = json.loads(Path(args.metadata_file).read_text(encoding="utf-8"))
        fs, ws = scan_metadata(payload)
        findings.extend(fs)
        warnings.extend(ws)

    out = {
        "schema_version": "public-surface-scan/v2",
        "files_checked": len(paths),
        "files": list(paths),
        "findings": [f"{f.path}: {f.rule}: {f.message}" for f in findings],
        "warnings": warnings,
        "passed": not findings,
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
