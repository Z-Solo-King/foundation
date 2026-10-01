#!/usr/bin/env python3
"""Fail-closed 100% Git-tracked family surface coverage validator."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "docs" / "FAMILY_FULL_COVERAGE_MATRIX.json"
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", "node_modules", ".venv", "venv", "dist", "build", "target"
}


def load_matrix() -> dict:
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "family-full-coverage/v1":
        raise ValueError("unsupported family-full-coverage schema")
    if set(payload.get("repositories", {})) != {"foundation", "operations"}:
        raise ValueError("family repository inventory drift")
    surfaces = payload.get("functional_surfaces", [])
    ids = [str(item.get("id")) for item in surfaces]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("functional surface identifiers must be unique and non-empty")
    return payload


def tracked_files(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z"],
            text=False,
            timeout=30,
        )
        values = out.decode("utf-8", errors="surrogateescape").split("\x00")
        files = [value for value in values if value and not any(part in SKIP_DIRS for part in Path(value).parts)]
        return sorted(files)
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return sorted(
            str(path.relative_to(root)).replace("\\", "/")
            for path in root.rglob("*")
            if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
        )


def classify(repo: str, rel: str, matrix: dict) -> str | None:
    for prefix, surface in matrix["primary_classification"].get(repo, []):
        if prefix.endswith("/"):
            if rel.startswith(prefix):
                return surface
        elif rel == prefix:
            return surface
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_anchor(root_by_name: dict[str, Path], repo: str, rel: str) -> str | None:
    root = root_by_name[repo]
    path = root / rel
    return None if path.is_file() else f"{repo}:{rel}"


def text_for(root_by_name: dict[str, Path], repo: str, rel: str) -> str:
    path = root_by_name[repo] / rel
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def validate_external(root_by_name: dict[str, Path], matrix: dict) -> list[str]:
    errors: list[str] = []
    f = root_by_name["foundation"]
    mcp = (f / "docs/MCP_DERIVED_TOOLING_PATTERNS.md").read_text(encoding="utf-8", errors="ignore")
    if "No MCP package is added to:" not in mcp and "The project does not add these MCP servers directly" not in mcp:
        errors.append("mcp: discovery-only/no-runtime-dependency statement missing")
    app_policy = json.loads((f / "docs/GITHUB_APP_INTEGRATION_POLICY.json").read_text(encoding="utf-8"))
    z = app_policy["zero_cost_policy"]
    if app_policy["external_marketplace_apps"] != [] or z["paid_plans_allowed"] or z["free_trials_allowed"] or z["payment_method_required"] or z["external_billing_dependency_allowed"]:
        errors.append("github_apps: strict $0 Marketplace App policy drift")
    action_policy = json.loads((f / "docs/GITHUB_ACTIONS_ZERO_COST_POLICY.json").read_text(encoding="utf-8"))
    a = action_policy["action_policy"]
    if not a["full_sha_required"] or a["unknown_action_ref_policy"] != "deny" or a["docker_actions_allowed"]:
        errors.append("github_actions: immutable/deny policy drift")
    action_audit = (f / "docs/GITHUB_ACTIONS_MARKETPLACE_AUDIT_2026-10-01.md").read_text(encoding="utf-8", errors="ignore")
    app_audit = (f / "docs/GITHUB_APP_MARKETPLACE_AUDIT_2026-10-01.md").read_text(encoding="utf-8", errors="ignore")
    if "9,999 action entries" not in action_audit:
        errors.append("github_actions: supplied dataset count is not documented")
    if "1,408 GitHub App entries" not in app_audit:
        errors.append("github_apps: supplied dataset count is not documented")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--foundation-root", type=Path, required=True)
    parser.add_argument("--operations-root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    matrix = load_matrix()
    roots = {"foundation": args.foundation_root.resolve()}
    if args.operations_root:
        roots["operations"] = args.operations_root.resolve()
    family_mode = "operations" in roots
    roots_by_name = roots

    all_records: list[dict] = []
    errors: list[str] = []
    for repo, root in roots.items():
        if not root.is_dir():
            errors.append(f"{repo}: repository root does not exist")
            continue
        files = tracked_files(root)
        repo_errors = []
        for rel in files:
            surface = classify(repo, rel, matrix)
            if surface is None:
                repo_errors.append(f"{repo}:{rel}")
                continue
            path = root / rel
            if not path.is_file():
                repo_errors.append(f"{repo}:{rel}:tracked file missing from checkout")
                continue
            sha = sha256_file(path)
            all_records.append({
                "repo": repo,
                "path": rel,
                "surface": surface,
                "bytes": path.stat().st_size,
                "sha256": sha,
            })
        if repo_errors:
            errors.append(f"{repo}: unclassified_or_missing_files={len(repo_errors)}")
            errors.extend(repo_errors[:100])
        else:
            errors.append(f"{repo}:OK:{len(files)}")
    if family_mode:
        for surface in matrix["functional_surfaces"]:
            missing = []
            for repo, rel in surface.get("anchors", []):
                if repo not in roots:
                    missing.append(f"{repo}:{rel}:repo-not-supplied")
                else:
                    miss = assert_anchor(roots_by_name, repo, rel)
                    if miss:
                        missing.append(miss)
            if missing:
                errors.append(f"surface {surface['id']}: missing anchors: {', '.join(missing)}")
    else:
        # PR-safe mode validates Foundation anchors only; private Operations anchors are
        # validated in the full-family scheduled/main run where the App token is available.
        for surface in matrix["functional_surfaces"]:
            foundation_anchors = [rel for repo, rel in surface.get("anchors", []) if repo == "foundation"]
            if not foundation_anchors:
                continue
            missing = [f"foundation:{rel}" for rel in foundation_anchors if not (roots_by_name["foundation"]/rel).is_file()]
            if missing:
                errors.append(f"surface {surface['id']}: missing Foundation anchors: {', '.join(missing)}")
    if family_mode:
        errors.extend(validate_external(roots_by_name, matrix))

    covered = len(all_records)
    expected = sum(len(tracked_files(root)) for root in roots.values() if root.is_dir())
    unclassified = [item for item in all_records if not item.get("surface")]
    digest_input = "\n".join(
        f"{row['repo']}|{row['path']}|{row['surface']}|{row['sha256']}"
        for row in sorted(all_records, key=lambda x: (x["repo"], x["path"]))
    ).encode("utf-8")
    inventory_digest = hashlib.sha256(digest_input).hexdigest()
    blocking_errors = [item for item in errors if not (item.endswith(":OK:"+item.rsplit(":OK:",1)[-1])) and not item.startswith("foundation:OK:") and not item.startswith("operations:OK:")]
    result = {
        "schema": "family-full-coverage-receipt/v1",
        "mode": "family" if family_mode else "foundation",
        "repositories": {name: str(path) for name, path in roots.items()},
        "tracked_files_expected": expected,
        "tracked_files_classified": covered,
        "coverage_percent": round((covered / expected) * 100.0, 4) if expected else 100.0,
        "unclassified_or_missing_count": max(0, expected - covered),
        "blocking_error_count": len(blocking_errors),
        "inventory_digest": inventory_digest,
        "surface_counts": {
            surface["id"]: sum(1 for row in all_records if row["surface"] == surface["id"])
            for surface in matrix["functional_surfaces"]
        },
        "records": all_records,
        "errors": blocking_errors,
        "external_ecosystems_checked": family_mode,
        "status": "PASS" if expected == covered and not blocking_errors else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("schema","mode","tracked_files_expected","tracked_files_classified","coverage_percent","unclassified_or_missing_count","blocking_error_count","inventory_digest","status")}, indent=2))
    if result["status"] != "PASS" and (args.strict or family_mode):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
