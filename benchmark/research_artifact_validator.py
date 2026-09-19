from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_CATEGORIES = {
    "project_architecture",
    "project_status",
    "research_artifacts",
    "nightly_artifact_integrity",
    "extraction_quality",
    "regression_analysis",
    "ci_health",
    "source_novelty",
    "evidence_quality",
    "research_efficiency",
    "frontend_research",
    "acceptance",
}

REQUIRED_CATALOG_PATHS = {
    "benchmark/chatbot-query-corpus.json",
    "benchmark/chatbot_query_benchmark.py",
    "benchmark/public_chatbot_runner.py",
    "benchmark/nightly/NIGHTLY_RESEARCH_PLAN.json",
    "benchmark/nightly/research-ledger.schema.json",
    "benchmark/nightly/research_ledger.py",
    "benchmark/autonomous_scorecard.py",
    "benchmark/multi_agent/baseline.py",
}

NIGHTLY_LANE_COUNT = 3
NIGHTLY_PROGRAMS_PER_LANE = 8
NIGHTLY_PROGRAM_COUNT = 24
NIGHTLY_LANE_STATES = {
    "live_research_executed",
    "dry_run",
    "blocked_before_execution",
    "lane_failure",
}


def _load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _find_named_artifacts(root: Path, filename: str) -> list[Path]:
    """Find artifact files, explicitly traversing hidden runtime outputs."""
    candidates: set[Path] = set()
    runtime_dir = root / ".runtime"
    if runtime_dir.is_dir():
        candidates.update(path for path in runtime_dir.rglob(filename) if path.is_file())
    candidates.update(path for path in root.rglob(filename) if path.is_file())
    return sorted(candidates)


def _scorecard_evidence_boundary_errors(scorecard: dict[str, Any]) -> list[str]:
    """Return explicit violations of the benchmark-vs-correctness evidence boundary."""
    errors: list[str] = []
    structural = scorecard.get("structural_signals") or {}
    if not isinstance(structural, dict):
        structural = {}
    oracle_claim = structural.get("field_level_correctness_oracle") is True
    field_level_scope = structural.get("evidence_scope") == "field_level_correctness"
    if oracle_claim or field_level_scope:
        errors.append(
            "field-level correctness claims require an explicit verified oracle; "
            "transport and structural benchmark signals are not product-field correctness"
        )
    return errors


def _nightly_artifact_errors(root: Path) -> list[str]:
    """Validate the nightly lane/diagnosis/summary/baseline bundle when present."""
    lane_paths = {
        lane: root / ".runtime" / "artifacts" / f"nightly-lane-{lane}-status.json"
        for lane in range(NIGHTLY_LANE_COUNT)
    }
    discovered_lane_paths = {
        lane: discovered[0]
        for lane, candidate in lane_paths.items()
        if (discovered := _find_named_artifacts(root, candidate.name))
    }

    if not discovered_lane_paths:
        for lane in range(NIGHTLY_LANE_COUNT):
            discovered = _find_named_artifacts(root, f"nightly-lane-{lane}-status.json")
            if discovered:
                discovered_lane_paths[lane] = discovered[0]

    artifacts_present = bool(discovered_lane_paths)
    if not artifacts_present:
        return []

    errors: list[str] = []
    missing_lanes = sorted(set(range(NIGHTLY_LANE_COUNT)) - set(discovered_lane_paths))
    errors.extend(f"nightly artifact bundle missing lane status: lane {lane}" for lane in missing_lanes)
    if missing_lanes:
        return errors

    statuses = [_load(discovered_lane_paths[lane]) for lane in range(NIGHTLY_LANE_COUNT)]
    schemas = {str(item.get("schema", "")) for item in statuses}
    if schemas != {"nightly-research-lane-status/v1"}:
        errors.append(f"unexpected nightly lane status schemas: {sorted(schemas)}")

    run_ids = {str(item.get("run_id", "")) for item in statuses}
    if len(run_ids) != 1 or "" in run_ids:
        errors.append("nightly lane statuses must share one non-empty run_id")

    modes = {str(item.get("mode", "")) for item in statuses}
    if len(modes) != 1 or not modes.issubset({"live", "dry-run"}):
        errors.append(f"nightly lane statuses must share one valid mode: {sorted(modes)}")

    operations_revisions = {str(item.get("operations_revision", "")) for item in statuses}
    if len(operations_revisions) != 1 or "" in operations_revisions:
        errors.append("nightly lane statuses must share one non-empty Operations revision")

    for lane, status in enumerate(statuses):
        if int(status.get("lane", -1)) != lane:
            errors.append(f"nightly lane {lane} status has mismatched lane field")
        state = str(status.get("state", ""))
        if state not in NIGHTLY_LANE_STATES:
            errors.append(f"nightly lane {lane} has unknown state: {state}")
        program_count = int(status.get("program_count", 0) or 0)
        if program_count != NIGHTLY_PROGRAMS_PER_LANE:
            errors.append(f"nightly lane {lane} must report exactly 8 programs, got {program_count}")
        programs = {str(program) for program in (status.get("programs") or [])}
        expected = {f"lane{lane}-slot{slot}" for slot in range(NIGHTLY_PROGRAMS_PER_LANE)}
        if state in {"live_research_executed", "dry_run"} and programs != expected:
            errors.append(f"nightly lane {lane} program IDs do not exactly match the 8-slot contract")
        if str(status.get("mode")) == "live" and state == "dry_run":
            errors.append(f"nightly lane {lane} cannot be dry_run while mode=live")

    diagnosis_paths = _find_named_artifacts(root, "nightly-diagnosis.json")
    if diagnosis_paths:
        diagnosis = _load(diagnosis_paths[0])
        if diagnosis.get("schema") != "nightly-research-diagnosis/v1":
            errors.append(f"unsupported nightly diagnosis schema: {diagnosis.get('schema')!r}")
        if str(diagnosis.get("run_id")) not in run_ids:
            errors.append("nightly diagnosis run_id does not match lane statuses")
        lane_state_set = {str(item.get("state")) for item in statuses}
        expected_aggregate = (
            "lane_specific_failure" if "lane_failure" in lane_state_set else
            "blocked_before_execution" if "blocked_before_execution" in lane_state_set else
            "dry_run" if lane_state_set == {"dry_run"} else
            "live_research_executed" if lane_state_set == {"live_research_executed"} else
            "partial_or_mixed"
        )
        if diagnosis.get("aggregate_state") != expected_aggregate:
            errors.append(
                f"nightly diagnosis aggregate_state mismatch: expected {expected_aggregate}, "
                f"got {diagnosis.get('aggregate_state')!r}"
            )
        allowed_findings = bool(diagnosis.get("real_research_findings_allowed"))
        should_allow = expected_aggregate == "live_research_executed" and modes == {"live"}
        if allowed_findings != should_allow:
            errors.append("nightly diagnosis real_research_findings_allowed violates execution/evidence boundary")
        if diagnosis.get("historical_dry_run_findings_are_real_research") is not False:
            errors.append("nightly diagnosis must mark dry-run findings as non-research")

    project_paths = _find_named_artifacts(root, "nightly-project-improvement.json")
    if project_paths:
        project = _load(project_paths[0])
        if project.get("schema") != "project-improvement-research/v1":
            errors.append(f"unsupported project-improvement schema: {project.get('schema')!r}")
        if str(project.get("research_mode")) != "project_improvement":
            errors.append("nightly project-improvement artifact must declare research_mode=project_improvement")
        if int(project.get("program_count", 0) or 0) != NIGHTLY_PROGRAM_COUNT:
            errors.append("nightly project-improvement artifact must contain all 24 programs")
        if not (project.get("project_snapshot") or {}).get("revision"):
            errors.append("nightly project-improvement artifact must carry a project revision")
        evidence_policy = project.get("evidence_policy") or {}
        if evidence_policy.get("llm_findings") != "candidate_only_until_acquisition_receipt":
            errors.append("nightly project-improvement artifact violates the LLM evidence policy")
        if "live_research_executed" not in {str(item.get("state")) for item in statuses}:
            errors.append("nightly project-improvement artifact requires live research lane execution")

    baseline_paths = _find_named_artifacts(root, "nightly-baseline.json")
    if baseline_paths:
        baseline = _load(baseline_paths[0])
        if baseline.get("schema") != "project-improvement-baseline/v1":
            errors.append(f"unsupported nightly baseline schema: {baseline.get('schema')!r}")
        if baseline.get("decision") not in {"NO_BASELINE", "IMPROVED", "REGRESSED", "STABLE"}:
            errors.append(f"invalid nightly baseline decision: {baseline.get('decision')!r}")
        if baseline.get("available") is True:
            for field in ("current_research_id", "previous_research_id", "current_revision", "previous_revision"):
                if not baseline.get(field):
                    errors.append(f"available nightly baseline is missing {field}")

    return errors


def validate_repository(root: Path) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    catalog_path = root / "benchmark/research_artifact_catalog.json"
    corpus_path = root / "benchmark/chatbot-query-corpus.json"
    if not catalog_path.exists():
        errors.append("missing research artifact catalog")
        return _report(errors, warnings)
    if not corpus_path.exists():
        errors.append("missing chatbot query corpus")
        return _report(errors, warnings)

    catalog = _load(catalog_path)
    if catalog.get("schema") != "research-artifact-catalog/v1":
        errors.append(f"unsupported catalog schema: {catalog.get('schema')!r}")

    artifacts = {str(row.get("path")): row for row in catalog.get("artifacts", []) if isinstance(row, dict)}
    missing_catalog_entries = sorted(REQUIRED_CATALOG_PATHS - artifacts.keys())
    errors.extend(f"catalog missing required artifact: {path}" for path in missing_catalog_entries)
    for path, row in artifacts.items():
        if not (root / path).exists():
            errors.append(f"catalog points to missing path: {path}")
        if not isinstance(row.get("reusable_evidence"), bool):
            errors.append(f"reusable_evidence must be boolean: {path}")
        if row.get("research_value") not in {"High", "Medium", "Low"}:
            errors.append(f"invalid research_value: {path}")

    rules = catalog.get("reusable_evidence_rules")
    if not isinstance(rules, list) or len(rules) < 4:
        errors.append("catalog must contain at least four reusable-evidence rules")

    corpus = _load(corpus_path)
    if corpus.get("schema") != "chatbot-research-query-corpus/v3":
        errors.append(f"unsupported corpus schema: {corpus.get('schema')!r}")
    queries = corpus.get("queries", [])
    if not isinstance(queries, list) or not queries:
        errors.append("query corpus is empty")
        return _report(errors, warnings)

    ids = [str(row.get("id")) for row in queries if isinstance(row, dict)]
    duplicate_ids = sorted({query_id for query_id in ids if ids.count(query_id) > 1})
    errors.extend(f"duplicate query id: {query_id}" for query_id in duplicate_ids)

    project_rows = [
        row for row in queries
        if isinstance(row, dict) and row.get("category") in PROJECT_CATEGORIES
    ]
    categories = {row.get("category") for row in project_rows}
    missing_categories = sorted(PROJECT_CATEGORIES - categories)
    errors.extend(f"missing project research category: {category}" for category in missing_categories)
    for row in project_rows:
        sources = {str(source) for source in row.get("required_sources", [])}
        if "github" not in sources:
            errors.append(f"project query without github source family: {row.get('id')}")
    if not any(row.get("temporal") == "old_vs_new" for row in project_rows):
        errors.append("project corpus has no old_vs_new query")

    if len(project_rows) < len(PROJECT_CATEGORIES):
        warnings.append("multiple project categories are not represented by distinct queries")

    benchmark_paths = _find_named_artifacts(root, "chatbot-query-benchmark.json")
    if benchmark_paths:
        benchmark = _load(benchmark_paths[0])
        schema = str(benchmark.get("schema", ""))
        if not schema.startswith("chatbot-research-query-benchmark/"):
            errors.append(f"unsupported benchmark artifact schema: {schema!r}")
        failed = int(benchmark.get("failed") or 0)
        if failed:
            warnings.append(f"benchmark artifact reports {failed} failed query contracts")
        coverage = benchmark.get("corpus_coverage") or {}
        if int(coverage.get("project_query_count") or 0) < len(PROJECT_CATEGORIES):
            errors.append("benchmark artifact reports incomplete project-query coverage")

    scorecard_paths = _find_named_artifacts(root, "research-scorecard.json")
    if scorecard_paths:
        scorecard = _load(scorecard_paths[0])
        schema = str(scorecard.get("schema", ""))
        if not schema.startswith("autonomous-research-scorecard/"):
            errors.append(f"unsupported scorecard artifact schema: {schema!r}")
        errors.extend(_scorecard_evidence_boundary_errors(scorecard))

    nightly_errors = _nightly_artifact_errors(root)
    errors.extend(nightly_errors)

    return _report(errors, warnings)


def _report(errors: list[str], warnings: list[str]) -> dict[str, Any]:
    return {
        "schema": "research-artifact-validation/v1",
        "valid": not errors,
        "errors": sorted(errors),
        "warnings": sorted(warnings),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the research artifact/evidence boundary.")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--strict", action="store_true", help="also fail when benchmark artifacts report query failures")
    args = parser.parse_args()
    report = validate_repository(args.root)
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["valid"]:
        return 1
    if args.strict and report["warnings"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
