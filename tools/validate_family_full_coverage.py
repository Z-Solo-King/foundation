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
    ".tox", ".nox", "node_modules", ".venv", "venv", "dist", "build", "target",
}


def load_matrix() -> dict:
    payload = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "family-full-coverage/v1":
        raise ValueError("unsupported family-full-coverage schema")
    if set(payload.get("repositories", {})) != {"foundation", "operations"}:
        raise ValueError("family repository inventory drift")
    surfaces = payload.get("functional_surfaces", [])
    ids = [str(item.get("id")) for item in surfaces]
    if len(ids) != len(set(ids)) or not ids or any(not item for item in ids):
        raise ValueError("functional surface identifiers must be unique and non-empty")
    for repo, rules in payload.get("primary_classification", {}).items():
        prefixes = [str(prefix) for prefix, _surface in rules]
        if len(prefixes) != len(set(prefixes)):
            raise ValueError(f"duplicate primary-classification prefix in {repo}")
    return payload


def tracked_files(root: Path) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "-C", str(root), "ls-files", "-z"],
            text=False,
            timeout=30,
        )
        values = out.decode("utf-8", errors="surrogateescape").split("\x00")
        return sorted(
            value for value in values
            if value and not any(part in SKIP_DIRS for part in Path(value).parts)
        )
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return sorted(
            str(path.relative_to(root)).replace("\\", "/")
            for path in root.rglob("*")
            if path.is_file() and not any(part in SKIP_DIRS for part in path.parts)
        )


def classification_matches(repo: str, rel: str, matrix: dict) -> list[tuple[str, str]]:
    matches: list[tuple[str, str]] = []
    for prefix, surface in matrix["primary_classification"].get(repo, []):
        prefix = str(prefix)
        applies = rel.startswith(prefix) if prefix.endswith("/") else rel == prefix
        if applies:
            matches.append((prefix, str(surface)))
    return matches


def classify(repo: str, rel: str, matrix: dict) -> str | None:
    matches = classification_matches(repo, rel, matrix)
    if not matches:
        return None
    longest = max(len(prefix) for prefix, _surface in matches)
    winners = sorted({surface for prefix, surface in matches if len(prefix) == longest})
    if len(winners) != 1:
        raise ValueError(f"ambiguous primary classification for {repo}:{rel}: {winners}")
    return winners[0]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_anchor(root_by_name: dict[str, Path], repo: str, rel: str) -> str | None:
    if repo not in root_by_name:
        return f"{repo}:{rel}:repo-not-supplied"
    path = root_by_name[repo] / rel
    return None if path.is_file() else f"{repo}:{rel}"


def validate_external(root_by_name: dict[str, Path], matrix: dict) -> list[str]:
    errors: list[str] = []
    foundation = root_by_name["foundation"]
    operations = root_by_name["operations"]

    mcp_path = operations / "docs/MCP_DERIVED_TOOLING_PATTERNS.md"
    mcp = mcp_path.read_text(encoding="utf-8", errors="ignore") if mcp_path.is_file() else ""
    if "The project does not add these MCP servers directly" not in mcp and "No MCP package is added to:" not in mcp:
        errors.append("mcp: discovery-only/no-runtime-dependency statement missing")

    app_policy = json.loads((foundation / "docs/GITHUB_APP_INTEGRATION_POLICY.json").read_text(encoding="utf-8"))
    z = app_policy["zero_cost_policy"]
    if (
        app_policy["external_marketplace_apps"] != []
        or z["paid_plans_allowed"]
        or z["free_trials_allowed"]
        or z["payment_method_required"]
        or z["external_billing_dependency_allowed"]
    ):
        errors.append("github_apps: strict $0 Marketplace App policy drift")

    action_policy = json.loads((foundation / "docs/GITHUB_ACTIONS_ZERO_COST_POLICY.json").read_text(encoding="utf-8"))
    a = action_policy["action_policy"]
    invariants = action_policy["zero_cost_invariants"]
    if (
        not a["full_sha_required"]
        or a["unknown_action_ref_policy"] != "deny"
        or a["docker_actions_allowed"]
        or action_policy["runner_policy"]["allowed_labels"] != ["ubuntu-latest"]
        or invariants["max_additional_cost_usd"] != 0
        or invariants["external_billing_dependency_allowed"]
        or invariants["paid_marketplace_action_or_service_allowed"]
        or invariants["larger_runners_allowed"]
        or invariants["private_hosted_runner_usage_allowed"]
    ):
        errors.append("github_actions: strict $0 immutable-action policy drift")

    action_audit = (foundation / "docs/GITHUB_ACTIONS_MARKETPLACE_AUDIT_2026-10-01.md").read_text(encoding="utf-8", errors="ignore")
    app_audit = (foundation / "docs/GITHUB_APP_MARKETPLACE_AUDIT_2026-10-01.md").read_text(encoding="utf-8", errors="ignore")
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

    all_records: list[dict] = []
    errors: list[str] = []
    repo_counts: dict[str, int] = {}

    for repo, root in roots.items():
        if not root.is_dir():
            errors.append(f"{repo}: repository root does not exist")
            continue
        files = tracked_files(root)
        repo_counts[repo] = len(files)
        for rel in files:
            try:
                surface = classify(repo, rel, matrix)
            except ValueError as exc:
                errors.append(f"{repo}:{rel}:{exc}")
                continue
            if surface is None:
                errors.append(f"{repo}:{rel}:unclassified")
                continue
            path = root / rel
            if not path.is_file():
                errors.append(f"{repo}:{rel}:tracked file missing from checkout")
                continue
            all_records.append({
                "repo": repo,
                "path": rel,
                "surface": surface,
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })

    if family_mode:
        for surface in matrix["functional_surfaces"]:
            missing = [
                miss for repo, rel in surface.get("anchors", [])
                if (miss := assert_anchor(roots, repo, rel)) is not None
            ]
            if missing:
                errors.append(f"surface {surface['id']}: missing anchors: {', '.join(missing)}")
    else:
        for surface in matrix["functional_surfaces"]:
            missing = [
                f"foundation:{rel}"
                for repo, rel in surface.get("anchors", [])
                if repo == "foundation" and not (roots["foundation"] / rel).is_file()
            ]
            if missing:
                errors.append(f"surface {surface['id']}: missing Foundation anchors: {', '.join(missing)}")

    if family_mode:
        errors.extend(validate_external(roots, matrix))

    expected = sum(repo_counts.values())
    covered = len(all_records)
    digest_input = "\n".join(
        f"{row['repo']}|{row['path']}|{row['surface']}|{row['sha256']}"
        for row in sorted(all_records, key=lambda x: (x["repo"], x["path"]))
    ).encode("utf-8")
    inventory_digest = hashlib.sha256(digest_input).hexdigest()

    result = {
        "schema": "family-full-coverage-receipt/v1",
        "mode": "family" if family_mode else "foundation",
        "repositories": {name: str(path) for name, path in roots.items()},
        "tracked_files_expected": expected,
        "tracked_files_classified": covered,
        "coverage_percent": round((covered / expected) * 100.0, 4) if expected else 100.0,
        "unclassified_or_missing_count": max(0, expected - covered),
        "blocking_error_count": len(errors),
        "inventory_digest": inventory_digest,
        "surface_counts": {
            surface["id"]: sum(1 for row in all_records if row["surface"] == surface["id"])
            for surface in matrix["functional_surfaces"]
        },
        "records": all_records,
        "errors": errors,
        "external_ecosystems_checked": family_mode,
        "status": "PASS" if expected == covered and not errors else "FAIL",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        k: result[k]
        for k in (
            "schema", "mode", "tracked_files_expected", "tracked_files_classified",
            "coverage_percent", "unclassified_or_missing_count",
            "blocking_error_count", "inventory_digest", "status",
        )
    }, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
