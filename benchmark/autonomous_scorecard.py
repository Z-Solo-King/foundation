from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


STATUS_KEYS = ("ok", "empty", "blocked", "resource_limited", "error")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def collect_summary_files(root: Path) -> list[Path]:
    return sorted(root.rglob("benchmark-summary.json"))


def build_scorecard(root: Path) -> dict[str, Any]:
    summary_paths = collect_summary_files(root)
    if not summary_paths:
        raise ValueError(f"no benchmark-summary.json files found under {root}")

    status_counts: Counter[str] = Counter()
    http_counts: Counter[str] = Counter()
    diagnostic_counts: Counter[str] = Counter()
    targets: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "url": "",
            "observations": 0,
            "failures": 0,
            "status_counts": Counter(),
            "http_status_counts": Counter(),
            "diagnostics": Counter(),
        }
    )
    selected_targets = 0
    cycles = 0
    run_ids: set[str] = set()
    shards: list[int] = []
    measurement_gaps: set[str] = set()

    for path in summary_paths:
        row = _read_json(path)
        schema = str(row.get("schema", ""))
        if not schema.startswith("autonomous-public-benchmark-summary/"):
            raise ValueError(f"unexpected benchmark summary schema in {path}: {schema!r}")
        run_id = str(row.get("run_id") or "")
        if run_id:
            run_ids.add(run_id)
        shard = row.get("shard")
        if isinstance(shard, int):
            shards.append(shard)
        selected_targets += int(row.get("selected_targets") or row.get("selected") or 0)
        cycles += int(row.get("cycles") or 0)
        status_counts.update({str(k): int(v) for k, v in (row.get("status_counts") or {}).items()})
        http_counts.update({str(k): int(v) for k, v in (row.get("http_status_counts") or {}).items()})
        diagnostic_counts.update({str(k): int(v) for k, v in (row.get("diagnostic_counts") or {}).items()})

        failures = row.get("targets_with_failures") or []
        for target in failures:
            url = str(target.get("url") or "")
            entry = targets[url]
            entry["url"] = url
            observations = int(target.get("observations") or 0)
            entry["observations"] += observations
            entry["failures"] += int(target.get("failures") or 0)
            entry["status_counts"].update(
                {str(k): int(v) for k, v in (target.get("status_counts") or {}).items()}
            )
            entry["http_status_counts"].update(
                {str(k): int(v) for k, v in (target.get("http_status_counts") or {}).items()}
            )
            entry["diagnostics"].update(
                {str(k): int(v) for k, v in (target.get("diagnostics") or {}).items()}
            )

        measurement_gaps.update(
            {
                "sanitized benchmark artifacts do not expose latency percentiles",
                "sanitized benchmark artifacts do not aggregate product-candidate counts",
                "sanitized benchmark artifacts do not aggregate JSON-LD extraction counts",
                "live benchmark validates transport/content hints, not field-level product correctness",
                "no oracle-backed product-field recall/precision score is present in this run",
            }
        )

    total_observations = sum(status_counts.values())
    ok = int(status_counts.get("ok", 0))
    empty = int(status_counts.get("empty", 0))
    blocked = int(status_counts.get("blocked", 0))
    resource_limited = int(status_counts.get("resource_limited", 0))
    errors = int(status_counts.get("error", 0))
    operational_failures = blocked + resource_limited
    clean_failures = empty + blocked + resource_limited + errors

    query_result = None
    query_paths = sorted(root.rglob("chatbot-query-benchmark.json"))
    if query_paths:
        # One deep-query artifact is expected. Prefer the first deterministic path.
        query_result = _read_json(query_paths[0])
    query_total = int((query_result or {}).get("queries") or 0)
    query_passed = int((query_result or {}).get("passed") or 0)
    query_failed = int((query_result or {}).get("failed") or 0)

    shard_expected = sorted(set(shards))
    execution_pass = bool(total_observations > 0 and shard_expected)
    contract_status = "PASS" if query_result is not None and query_total > 0 and query_failed == 0 and query_passed == query_total else "FAIL"
    acquisition_clean_status = "PASS" if clean_failures == 0 else "FAIL"
    overall_status = "PASS" if execution_pass and contract_status == "PASS" and acquisition_clean_status == "PASS" else "WARN"

    target_rows = []
    for entry in targets.values():
        observations = int(entry["observations"])
        failures = int(entry["failures"])
        target_rows.append(
            {
                "url": entry["url"],
                "observations": observations,
                "failures": failures,
                "failure_rate": _ratio(failures, observations),
                "status_counts": dict(sorted(entry["status_counts"].items())),
                "http_status_counts": dict(sorted(entry["http_status_counts"].items())),
                "diagnostics": dict(sorted(entry["diagnostics"].items())),
            }
        )
    target_rows.sort(key=lambda item: (-float(item["failure_rate"] or 0), item["url"]))

    return {
        "schema": "autonomous-research-scorecard/v1",
        "run_ids": sorted(run_ids),
        "shards": shard_expected,
        "selected_targets": selected_targets,
        "cycles": cycles,
        "total_observations": total_observations,
        "status": {
            "overall": overall_status,
            "execution": "PASS" if execution_pass else "FAIL",
            "research_contract": contract_status,
            "acquisition_clean": acquisition_clean_status,
        },
        "research_contract": {
            "queries": query_total,
            "passed": query_passed,
            "failed": query_failed,
            "pass_rate": _ratio(query_passed, query_total),
        },
        "acquisition": {
            "usable_observation_rate": _ratio(ok, total_observations),
            "operational_failure_rate": _ratio(operational_failures, total_observations),
            "error_rate": _ratio(errors, total_observations),
            "empty_rate": _ratio(empty, total_observations),
            "blocked_rate": _ratio(blocked, total_observations),
            "resource_limited_rate": _ratio(resource_limited, total_observations),
            "clean_failure_rate": _ratio(clean_failures, total_observations),
            "status_counts": dict(sorted(status_counts.items())),
            "http_status_counts": dict(sorted(http_counts.items())),
            "diagnostic_counts": dict(sorted(diagnostic_counts.items())),
        },
        "targets_with_failures": target_rows,
        "measurement_gaps": sorted(measurement_gaps),
    }


def render_markdown(scorecard: dict[str, Any]) -> str:
    status = scorecard["status"]
    contract = scorecard["research_contract"]
    acquisition = scorecard["acquisition"]
    lines = [
        "# Autonomous Research Scorecard",
        "",
        f"Overall: **{status['overall']}**",
        f"Execution: **{status['execution']}**",
        f"Research contract: **{status['research_contract']}** ({contract['passed']}/{contract['queries']} passed)",
        f"Acquisition clean: **{status['acquisition_clean']}**",
        "",
        "## Acquisition performance",
        "",
        f"- Targets selected: {scorecard['selected_targets']}",
        f"- Cycles: {scorecard['cycles']}",
        f"- Observations: {scorecard['total_observations']}",
        f"- Usable observation rate: {acquisition['usable_observation_rate']}",
        f"- Operational failure rate: {acquisition['operational_failure_rate']}",
        f"- Error rate: {acquisition['error_rate']}",
        f"- Blocked rate: {acquisition['blocked_rate']}",
        f"- Resource-limited rate: {acquisition['resource_limited_rate']}",
        f"- Empty rate: {acquisition['empty_rate']}",
        "",
        "## Measurement gaps",
        "",
    ]
    lines.extend(f"- {gap}" for gap in scorecard["measurement_gaps"])
    lines.extend(["", "## Targets with failures", ""])
    if scorecard["targets_with_failures"]:
        lines.append("| Target | Observations | Failures | Failure rate | HTTP statuses |")
        lines.append("|---|---:|---:|---:|---|")
        for target in scorecard["targets_with_failures"]:
            lines.append(
                "| {url} | {observations} | {failures} | {failure_rate} | {http} |".format(
                    url=target["url"],
                    observations=target["observations"],
                    failures=target["failures"],
                    failure_rate=target["failure_rate"],
                    http=", ".join(f"{k}:{v}" for k, v in target["http_status_counts"].items()) or "-",
                )
            )
    else:
        lines.append("No target-level failures were recorded.")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate autonomous benchmark artifacts into a research scorecard.")
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--json-output", type=Path, required=True)
    parser.add_argument("--markdown-output", type=Path, required=True)
    args = parser.parse_args()
    scorecard = build_scorecard(args.root)
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(scorecard, indent=2, sort_keys=True), encoding="utf-8")
    args.markdown_output.write_text(render_markdown(scorecard), encoding="utf-8")
    print(json.dumps(scorecard, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
