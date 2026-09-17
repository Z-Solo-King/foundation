from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan
from benchmark.evidence_tier import EvidenceTier, parse_evidence_tier

REQUIRED_DEEP_STAGES = {
    "define_question",
    "assess_constraints",
    "discover_sources",
    "collect_observations",
    "map_evidence",
    "verify_evidence",
    "check_independence",
    "synthesize_answer",
}

SOURCE_ALIASES = {
    "bilibili": "chinese_communities", "zhihu": "chinese_communities", "baidu_tieba": "chinese_communities", "douban": "chinese_communities", "ptt": "chinese_communities",
    "social_communities": "social_communities", "regional_communities": "social_communities", "social_media": "social_media",
    "x_twitter": "social_media", "instagram": "social_media", "facebook": "social_media", "tiktok": "social_media", "meta_ai": "social_media",
    "search_trends": "search_trends", "retailers": "retailers", "professional_reviews": "professional_reviews", "price_stock": "price_stock",
    "oem": "oem", "amazon": "amazon", "flipkart": "flipkart", "reddit": "reddit", "youtube": "youtube",
    "project_docs": "github", "github_issues": "github", "github_actions": "github", "operations": "github",
}

PROJECT_CATEGORIES = {
    "project_architecture", "project_status", "research_artifacts", "extraction_quality", "regression_analysis",
    "ci_health", "source_novelty", "evidence_quality", "research_efficiency", "frontend_research", "acceptance",
}


def load_queries(path: Path) -> list[dict[str, object]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("queries", []) if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError("query corpus must contain a non-empty queries list")
    return [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("query")]


def run(
    path: Path,
    output: Path,
    allow_failures: bool = False,
    evidence_tier: str = EvidenceTier.DETERMINISTIC_CONTRACT.value,
) -> int:
    evidence = parse_evidence_tier(evidence_tier)
    # This benchmark exercises deterministic research planning only. A caller
    # cannot label it as live/integration/production evidence without changing
    # the benchmark implementation to actually exercise that environment.
    if evidence.tier is not EvidenceTier.DETERMINISTIC_CONTRACT:
        raise ValueError(
            "chatbot_query_benchmark executes deterministic research-plan contracts only; "
            "use a runtime-aware benchmark runner for live-provider/integration/production tiers"
        )

    rows = load_queries(path)
    results: list[dict[str, object]] = []
    failures = 0
    category_failures: Counter[str] = Counter()
    source_family_failures: Counter[str] = Counter()
    categories: Counter[str] = Counter()
    source_families: Counter[str] = Counter()
    temporal_modes: Counter[str] = Counter()
    project_query_count = 0

    for row in rows:
        query = str(row["query"])
        expected = {str(x) for x in row.get("required_sources", [])}
        expected_families = {SOURCE_ALIASES.get(source, source) for source in expected}
        category = str(row.get("category", "")) or "unknown"
        categories[category] += 1
        temporal = str(row.get("temporal", "current"))
        temporal_modes[temporal] += 1
        source_families.update(expected_families)
        is_project_query = category in PROJECT_CATEGORIES
        project_query_count += int(is_project_query)
        contract = ResearchContract(
            question=query,
            depth="deep",
            require_citations=True,
            max_sources=40,
            max_evidence_items=200,
            query_category=category,
            required_source_families=tuple(sorted(expected_families)),
        )
        try:
            plan = create_plan(contract)
            families = {x for x in plan.metadata.get("required_source_families", "").split(",") if x}
            missing = sorted(expected_families - families)
            stages_ok = REQUIRED_DEEP_STAGES.issubset(set(plan.stages))
            temporal_expected = temporal == "old_vs_new"
            temporal_ok = plan.metadata.get("temporal_reconciliation") == "true" if temporal_expected else True
            citation_ok = plan.metadata.get("require_citations") == "true"
            passed = stages_ok and citation_ok and not missing and temporal_ok
            if not passed:
                failures += 1
                category_failures[category] += 1
                for family in missing:
                    source_family_failures[family] += 1
                if not stages_ok:
                    source_family_failures["__missing_required_stage__"] += 1
                if not citation_ok:
                    source_family_failures["__citations_not_planned__"] += 1
                if not temporal_ok:
                    source_family_failures["__temporal_reconciliation_missing__"] += 1
            results.append({
                "id": row["id"],
                "category": category,
                "project_query": is_project_query,
                "passed": passed,
                "required_sources": sorted(expected),
                "required_source_families": sorted(expected_families),
                "planned_sources": sorted(families),
                "missing_source_families": missing,
                "temporal_expected": temporal_expected,
                "temporal_planned": plan.metadata.get("temporal_reconciliation"),
                "citations_required": True,
                "citations_planned": citation_ok,
                "stages": list(plan.stages),
            })
        except Exception as exc:
            failures += 1
            category_failures[category] += 1
            source_family_failures[f"__exception__:{type(exc).__name__}"] += 1
            results.append({"id": row["id"], "category": category, "project_query": is_project_query, "passed": False, "error": type(exc).__name__})

    total = len(results)
    summary = {
        "schema": "chatbot-research-query-benchmark/v6",
        "queries": total,
        "passed": total - failures,
        "failed": failures,
        "pass_rate": round((total - failures) / total, 4) if total else 0.0,
        "evidence": evidence.to_dict(),
        "evidence_rule": "This runner proves deterministic research-plan contract coverage only; it does not certify live provider, integration runtime or production behavior.",
        "corpus_coverage": {
            "category_count": len(categories),
            "categories": dict(sorted(categories.items())),
            "source_family_count": len(source_families),
            "source_families": dict(sorted(source_families.items())),
            "temporal_modes": dict(sorted(temporal_modes.items())),
            "project_query_count": project_query_count,
            "project_query_rate": round(project_query_count / total, 4) if total else 0.0,
        },
        "failure_categories": dict(sorted(category_failures.items())),
        "failure_causes": dict(sorted(source_family_failures.items())),
        "strict": not allow_failures,
        "results": results,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if allow_failures or failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="benchmark/chatbot-query-corpus.json")
    parser.add_argument("--output", default=".runtime/chatbot-query-benchmark.json")
    parser.add_argument("--allow-failures", action="store_true", help="record research gaps without failing the benchmark")
    parser.add_argument("--evidence-tier", default=EvidenceTier.DETERMINISTIC_CONTRACT.value)
    args = parser.parse_args()
    return run(Path(args.input), Path(args.output), args.allow_failures, args.evidence_tier)


if __name__ == "__main__":
    raise SystemExit(main())
