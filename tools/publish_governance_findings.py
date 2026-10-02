#!/usr/bin/env python3
"""Publish deterministic governance findings to GitHub with stable deduplication markers."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import urllib.request
from pathlib import Path

def api(repo, token, path, method="GET", body=None):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request("https://api.github.com/repos/" + repo + path, data=data, method=method, headers={"Accept":"application/vnd.github+json","Authorization":"Bearer " + token,"X-GitHub-Api-Version":"2022-11-28","Content-Type":"application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        raw = response.read().decode()
        return json.loads(raw) if raw else None

def marker(finding_id):
    return "<!-- governance-finding:" + finding_id + " -->"

def digest(finding):
    payload = {key: finding.get(key) for key in ("category","severity","code","summary","details","paths")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]

def render(finding, stamp):
    lines = [marker(finding["finding_id"]), "# Automated governance finding", "", "**Scan:** " + str(stamp), "**Severity:** " + finding["severity"], "**Lane:** " + finding["lane"], "**Code:** " + finding["code"], "", finding["summary"], "", "## Evidence", "```json", json.dumps(finding.get("details"), indent=2)[:5000], "```", "", "## Paths"]
    lines.extend("- " + path for path in (finding.get("paths") or [])[:25])
    lines.extend(["", "This is governance telemetry, not an acceptance/promotion/production certificate.", "<!-- governance-digest:" + digest(finding) + " -->"])
    return "\n".join(lines) + "\n"

def publish(repo, token, report):
    open_issues = api(repo, token, "/issues?state=open&per_page=100") or []
    touched = 0
    for finding in report.get("findings", []):
        if finding.get("severity") == "info":
            continue
        mark = marker(finding["finding_id"])
        existing = next((issue for issue in open_issues if "pull_request" not in issue and mark in (issue.get("body") or "")), None)
        body = render(finding, report.get("generated_at"))
        if existing:
            old = existing.get("body") or ""
            api(repo, token, "/issues/" + str(existing["number"]), "PATCH", {"body": body})
            if "<!-- governance-digest:" + digest(finding) + " -->" not in old:
                api(repo, token, "/issues/" + str(existing["number"]) + "/comments", "POST", {"body": mark + "\n**Governance sweep update**\n\n" + finding["summary"]})
        else:
            api(repo, token, "/issues", "POST", {"title": "[governance][" + finding["severity"] + "] " + finding["code"] + ": " + finding["summary"][:120], "body": body})
        touched += 1

    open_prs = api(repo, token, "/pulls?state=open&per_page=100") or []
    comments = 0
    for pr in open_prs:
        changed_files = {item.get("filename") for item in (api(repo, token, "/pulls/" + str(pr["number"]) + "/files?per_page=100") or [])}
        comments_api = api(repo, token, "/issues/" + str(pr["number"]) + "/comments?per_page=100") or []
        for finding in report.get("findings", []):
            if finding.get("severity") == "info":
                continue
            paths = finding.get("paths") or []
            if not paths:
                continue
            overlap = any(changed == path or changed.startswith(path.rstrip("/") + "/") or ("*" in path and changed.startswith(path.split("*", 1)[0])) for path in paths for changed in changed_files)
            if not overlap:
                continue
            mark = marker(finding["finding_id"])
            if any(mark in (comment.get("body") or "") for comment in comments_api):
                continue
            api(repo, token, "/issues/" + str(pr["number"]) + "/comments", "POST", {"body": mark + "\n**Governance sweep finding affecting this PR**\n\n" + finding["summary"]})
            comments += 1
    return {"issues_touched": touched, "pr_comments": comments}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--report", required=True)
    parser.add_argument("--token-env", default="GH_TOKEN")
    args = parser.parse_args()
    token = os.getenv(args.token_env, "")
    if not token:
        raise SystemExit(args.token_env + " required")
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    print(json.dumps(publish(args.repo, token, report)))

if __name__ == "__main__":
    main()
