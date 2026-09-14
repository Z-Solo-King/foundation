from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SCHEMA = "nightly-research-ledger/v1"


def canonical_url(value: str) -> str:
    parts = urlsplit(value.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise ValueError(f"unsupported URL: {value!r}")
    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    port = parts.port
    netloc = host if not port or (scheme, port) in {("http", 80), ("https", 443)} else f"{host}:{port}"
    path = parts.path or "/"
    return urlunsplit((scheme, netloc, path, parts.query, ""))


def visit_key(task_id: str, url: str) -> str:
    value = f"{task_id}\n{canonical_url(url)}"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def empty_ledger(night_id: str, baseline_sha: str | None = None) -> dict[str, object]:
    return {
        "schema": SCHEMA,
        "night_id": night_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "completed_at": None,
        "baseline_sha": baseline_sha,
        "tasks": [],
        "visits": [],
        "findings": [],
        "next_tasks": [],
    }


def load(path: Path) -> dict[str, object]:
    if not path.exists():
        raise FileNotFoundError(path)
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError(f"invalid ledger schema in {path}")
    for key in ("tasks", "visits", "findings", "next_tasks"):
        if not isinstance(value.get(key), list):
            raise ValueError(f"ledger field {key!r} must be a list")
    return value


def visited_index(ledger: dict[str, object]) -> dict[str, dict[str, object]]:
    index: dict[str, dict[str, object]] = {}
    for row in ledger.get("visits", []):
        if not isinstance(row, dict):
            continue
        task_id = row.get("task_id")
        url = row.get("canonical_url")
        if isinstance(task_id, str) and isinstance(url, str):
            index[visit_key(task_id, url)] = row
    return index


def can_visit(
    ledger: dict[str, object],
    task_id: str,
    url: str,
    *,
    force_reason: str | None = None,
) -> tuple[bool, str]:
    key = visit_key(task_id, url)
    prior = visited_index(ledger).get(key)
    if prior is None:
        return True, "new_source"
    if force_reason in {
        "freshness_expired",
        "previous_failure_retry",
        "contradiction_check",
        "new_revision_or_region",
        "material_question_change",
        "high_churn_source",
    }:
        return True, force_reason
    return False, "already_visited_for_task"


def record_visit(
    ledger: dict[str, object],
    *,
    task_id: str,
    url: str,
    source_family: str,
    purpose: str,
    method: str,
    result: str,
    finding_ids: list[str] | None = None,
    revisit_policy: str = "never_same_task_unless_new_question",
    next_eligible_at: str | None = None,
    notes: str = "",
) -> dict[str, object]:
    canonical = canonical_url(url)
    allowed_results = {"useful", "duplicate", "blocked", "irrelevant", "stale", "contradictory", "failed"}
    if result not in allowed_results:
        raise ValueError(f"invalid result: {result}")
    row = {
        "visit_id": hashlib.sha256(
            f"{task_id}\n{canonical}\n{datetime.now(timezone.utc).isoformat()}".encode("utf-8")
        ).hexdigest()[:16],
        "task_id": task_id,
        "source_family": source_family,
        "domain": urlsplit(canonical).hostname or "",
        "canonical_url": canonical,
        "purpose": purpose,
        "method": method,
        "result": result,
        "visited_at": datetime.now(timezone.utc).isoformat(),
        "finding_ids": finding_ids or [],
        "revisit_policy": revisit_policy,
        "next_eligible_at": next_eligible_at,
        "notes": notes,
    }
    visits = ledger.setdefault("visits", [])
    if not isinstance(visits, list):
        raise ValueError("ledger visits field is not a list")
    visits.append(row)
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage nightly research source tracking")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init")
    init.add_argument("--output", required=True)
    init.add_argument("--night-id", required=True)
    init.add_argument("--baseline-sha")

    check = sub.add_parser("check")
    check.add_argument("--ledger", required=True)
    check.add_argument("--task-id", required=True)
    check.add_argument("--url", required=True)
    check.add_argument("--force-reason")

    args = parser.parse_args()
    if args.command == "init":
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(empty_ledger(args.night_id, args.baseline_sha), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return 0

    ledger = load(Path(args.ledger))
    allowed, reason = can_visit(ledger, args.task_id, args.url, force_reason=args.force_reason)
    print(json.dumps({"allowed": allowed, "reason": reason}, sort_keys=True))
    return 0 if allowed else 2


if __name__ == "__main__":
    raise SystemExit(main())
