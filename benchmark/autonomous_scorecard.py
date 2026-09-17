from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from benchmark.evidence_tier import EvidenceTier, parse_evidence_tier

STATUS_KEYS = ("ok", "empty", "blocked", "resource_limited", "error")


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def _ratio(numerator: int, denominator: int) -> float | None:
    return round(numerator / denominator, 6) if denominator else None


def _weighted_average(values: list[tuple[int, int]]) -> float | None:
    total_weight = sum(weight for _, weight in values)
    return round(sum(value * weight for value, weight in values) / total_weight, 3) if total_weight else None


def collect_summary_files(root: Path) -> list[Path]:
    return sorted(root.rglob("benchmark-summary.json")) + sorted(root.rglob("summary-*.json"))


def _tier_rank(value: str) -> int:
    try:
        return parse_evidence_tier(value).rank
    except ValueError:
        return -1


def build_scorecard(root: Path) -> dict[str, Any]:
    raw_summary_paths = collect_summary_files(root)
    # Avoid double-counting when an artifact contains both naming conventions.
    summary_paths = sorted({path.resolve() for path in raw_summary_paths})
    if not summary_paths:
        raise ValueError(f"no benchmark summary files found under {root}")

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
    measurement_rows: list[dict[str, Any]] = []
    component_tiers: set[str] = set()

    for path in summary_paths:
        row = _read_json(path)
        schema = str(row.get("schema", ""))
        if not schema.startswith("autonomous-public-benchmark-summary/"):
            continue
        evidence = row.get("evidence")
        if isinstance(evidence, dict) and isinstance(evidence.get("tier"), str):
            tier = evidence["tier"]
            if tier in {item.value for item in EvidenceTier}:
                component_tiers.add(tier)
            else:
                measurement_gaps.add(f"benchmark artifact declares unsupported evidence tier: {tier}")
        else:
            component_tiers.add("legacy_untyped")
            measurement_gaps.add("one or more acquisition artifacts predate the explicit evidence-tier contract")

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
        measurement = row.get("measurement")
        if isinstance(measurement, dict):
            measurement_rows.append(measurement)
        else:
            measurement_gaps.add("sanitized benchmark summary does not expose structural or latency measurements")

        failures = row.get("targets_with_failures") or []
        for target in failures:
            if not isinstance(target, dict):
                continue
            url = str(target.get("url") or "")
            entry = targets[url]
            entry["url"] = url
            observations = int(target.get("observations") or 0)
            entry["observations"] += observations
            entry["failures"] += int(target.get("failures") or 0)
            entry["status_counts"].update({str(k): int(v) for k, v in (target.get("status_counts") or {}).items()})
            entry["http_status_counts"].update({str(k): int(v) for k, v in (target.get("http_status_counts") or {}).items()})
            entry["diagnostics"].update({str(k): int(v) for k, v in (target.get("diagnostics") or {}).items()})

    measurement_observations = sum(int(row.get("observations", 0) or 0) for row in measurement_rows)
    product_candidates = sum(int(row.get("product_candidates_total", 0) or 0) for row in measurement_rows)
    jsonld_blocks = sum(int(row.get("jsonld_blocks_total", 0) or 0) for row in measurement_rows)
    product_observations = sum(int(row.get("observations_with_product_candidates", 0) or 0) for row in measurement_rows)
    jsonld_observations = sum(int(row.get("observations_with_jsonld", 0) or 0) for row in measurement_rows)
    latency_means: list[tuple[int, int]] = []
    p95_values: list[int] = []
    for row in measurement_rows:
        latency = row.get("elapsed_ms")
        if not isinstance(latency, dict):
            continue
        median = latency.get("median")
        p95 = latency.get("p95")
        observations = int(row.get("observations", 0) or 0)
        if isinstance(median, (int, float)) and observations:
            latency_means.append((int(median), observations))
        if isinstance(p95, (int, float)):
            p95_values.append(int(p95))

    if not measurement_rows:
        measurement_gaps.update(
            {
                "sanitized benchmark artifacts do not expose latency measurements",
                "sanitized benchmark artifacts do not expose product-candidate counts",
                "sanitized benchmark artifacts do not expose JSON-LD counts",
            }
        )
    if measurement_rows and all(not bool(row.get("field_level_correctness_oracle")) for row in measurement_rows):
        measurement_gaps.add("no oracle-backed product-field recall/precision score is present in this run")
    measurement_gaps.add("product-candidate and JSON-LD counts are structural hints, not correctness judgments")
    measurement_gaps.add("live benchmark validates transport/content structure, not field-level product correctness")

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
        query_result = _read_json(query_paths[0])
    query_total = int((query_result or {}).get("queries") or 0)
    query_passed = int((query_result or {}).get("passed") or 0)
    query_failed = int((query_result or {}).get("failed") or 0)
    corpus_coverage = (query_result or {}).get("corpus_coverage") or {}

    query_schema = str((query_result or {}).get("schema") or "")
    query_evidence = (query_result or {}).get("evidence")
    query_tier = None
    if isinstance(query_evidence, dict) and isinstance(query_evidence.get("tier"), str):
        if query_evidence["tier"] in {item.value for item in EvidenceTier}:
            query_tier = query_evidence["tier"]
            component_tiers.add(query_tier)
        else:
            measurement_gaps.add(f"query benchmark declares unsupported evidence tier: {query_evidence['tier']}")
    else:
        component_tiers.add("legacy_untyped")
        measurement_gaps.add("deep-query benchmark artifact predates the explicit evidence-tier contract")

    if query_result is None:
        measurement_gaps.add("deep-query benchmark artifact was not published with this run")
    elif not query_schema.startswith("chatbot-research-query-benchmark/"):
        measurement_gaps.add("deep-query benchmark artifact uses an unexpected schema")

    shard_expected = sorted(set(shards))
    execution_pass = bool(total_observations > 0 and shard_expected)
    contract_status = "PASS" if query_result is not None and query_total > 0 and query_failed == 0 and query_passed == query_total else "FAIL"
    acquisition_clean_status = "PASS" if clean_failures == 0 else "FAIL"
    overall_status = "PASS" if execution_pass and contract_status == "PASS" and acquisition_clean_status == "PASS" else "WARN"

    typed_component_tiers = sorted(
        (tier for tier in component_tiers if tier != "legacy_untyped"),
        key=_tier_rank,
    )
    minimum_tier = typed_component_tiers[0] if typed_component_tiers else "legacy_untyped"
    evidence = {
        "component_tiers": sorted(component_tiers),
        "minimum_tier": minimum_tier,
        "research_contract_tier": query_tier,
        "live_provider_claim_allowed": False,
        "integration_runtime_claim_allowed": False,
        "production_readiness_claim_allowed": False,
        "field_level_correctness_oracle": False,
        "rule": "Aggregate scorecards cannot claim a stronger tier than their individual artifacts; transport/structural signals remain distinct from correctness and production readiness.",
    }

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
        "schema": "autonomous-research-scorecard/v3",
        "run_ids": sorted(run_ids),
        "shards": shard_expected,
        "selected_targets": selected_targets,
        "cycles": cycles,
        "total_observations": total_observations,
        "evidence": evidence,
        "status": {
            "overall": overall_status,
            "execution": "PASS" if execution_pass else "FAIL",
            "research_contract": contract_status,
            "acquisition_clean": acquisition_clean_status,
        },
        "research_contract": {
            "schema": query_schema or None,
            "queries": query_total,
            "passed": query_passed,
            "failed": query_failed,
            "pass_rate": _ratio(query_passed, query_total),
            "project_query_count": int(corpus_coverage.get("project_query_count") or 0),
            "project_query_rate": corpus_coverage.get("project_query_rate"),
            "category_count": int(corpus_coverage.get("category_count") or 0),
            "source_family_count": int(corpus_coverage.get("source_family_count") or 0),
            "temporal_modes": dict(corpus_coverage.get("temporal_modes") or {}),
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
        "structural_signals": {
            "observations_measured": measurement_observations,
            "observations_with_product_candidates": product_observations,
            "product_candidate_observation_rate": _ratio(product_observations, measurement_observations),
            "product_candidates_total": product_candidates,
            "observations_with_jsonld": jsonld_observations,
            "jsonld_observation_rate": _ratio(jsonld_observations, measurement_observations),
            "jsonld_blocks_total": jsonld_blocks,
            "weighted_median_latency_ms": _weighted_average(latency_means),
            "max_shard_p95_latency_ms": max(p95_values) if p95_values else None,
            "evidence_scope": "transport_and_structural_signals_only" if measurement_rows else "transport_only",
            "field_level_correctness_oracle": False,
        },
        "targets_with_failures": target_rows,
        "measurement_gaps": sorted(measurement_gaps),
    }


def render_markdown(scorecard: dict[str, Any]) -> str:
    status = scorecard["status"]
    contract = scorecard["research_contract"]
    acquisition = scorecard["acquisition"]
    structural = scorecard["structural_signals"]
    evidence = scorecard["evidence"]
    lines = [
        "# Autonomous Research Scorecard",
        "",
        f"Overall: **{status['overall']}**",
        f"Execution: **{status['execution']}**",
        f"Research contract: **{status['research_contract']}** ({contract['passed']}/{contract['queries']} passed)",
        f"Acquisition clean: **{status['acquisition_clean']}**",
        "",
        "## Evidence tier",
        "",
        f"- Minimum aggregate tier: {evidence['minimum_tier']}",
        f"- Component tiers: {', '.join(evidence['component_tiers'])}",
        "- Live-provider claim allowed: False",
        "- Integration-runtime claim allowed: False",
        "- Production-readiness claim allowed: False",
        "- Field-level correctness oracle: False",
        "",
        "## Research contract coverage",
        "",
        f"- Project queries: {contract['project_query_count']} ({contract['project_query_rate']})",
        f"- Query categories: {contract['category_count']}",
        f"- Source families: {contract['source_family_count']}",
        f"- Temporal modes: {contract['temporal_modes']}",
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
        "## Structural acquisition signals",
        "",
        f"- Measured observations: {structural['observations_measured']}",
        f"- Product-candidate observation rate: {structural['product_candidate_observation_rate']}",
        f"- Product-candidate hints: {structural['product_candidates_total']}",
        f"- JSON-LD observation rate: {structural['jsonld_observation_rate']}",
        f"- JSON-LD blocks: {structural['jsonld_blocks_total']}",
        f"- Weighted median latency (shard medians): {structural['weighted_median_latency_ms']} ms",
        f"- Maximum shard-local p95 latency: {structural['max_shard_p95_latency_ms']} ms",
        f"- Evidence scope: {structural['evidence_scope']}",
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
