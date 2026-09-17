from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


PROJECT_CATEGORIES = {
    "project_architecture",
    "project_status",
    "research_artifacts",
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
        structural = scorecard.get("structural_signals") or {}
        oracle_claim = structural.get("field_level_correctness_oracle") is True
        field_level_scope = structural.get("evidence_scope") == "field_level_correctness"
        if oracle_claim or field_level_scope:
            errors.append(
                "field-level correctness claims require an explicit verified oracle; "
                "transport and structural benchmark signals are not product-field correctness"
            )

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
