from __future__ import annotations

import argparse
import json
from pathlib import Path

from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan

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
}


def load_queries(path: Path) -> list[dict[str, object]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    rows = value.get("queries", []) if isinstance(value, dict) else value
    if not isinstance(rows, list) or not rows:
        raise ValueError("query corpus must contain a non-empty queries list")
    return [row for row in rows if isinstance(row, dict) and row.get("id") and row.get("query")]


def run(path: Path, output: Path, allow_failures: bool = False) -> int:
    rows = load_queries(path)
    results: list[dict[str, object]] = []
    failures = 0
    for row in rows:
        query = str(row["query"])
        expected = {str(x) for x in row.get("required_sources", [])}
        expected_families = {SOURCE_ALIASES.get(source, source) for source in expected}
        contract = ResearchContract(question=query, depth="deep", require_citations=True, max_sources=40, max_evidence_items=200)
        try:
            plan = create_plan(contract)
            families = {x for x in plan.metadata.get("required_source_families", "").split(",") if x}
            missing = sorted(expected_families - families)
            stages_ok = REQUIRED_DEEP_STAGES.issubset(set(plan.stages))
            temporal_expected = row.get("temporal") == "old_vs_new"
            temporal_ok = plan.metadata.get("temporal_reconciliation") == "true" if temporal_expected else True
            citation_ok = plan.metadata.get("require_citations") == "true"
            passed = stages_ok and citation_ok and not missing and temporal_ok
            if not passed:
                failures += 1
            results.append({"id": row["id"], "category": row.get("category", ""), "passed": passed, "required_sources": sorted(expected), "required_source_families": sorted(expected_families), "planned_sources": sorted(families), "missing_source_families": missing, "temporal_expected": temporal_expected, "temporal_planned": plan.metadata.get("temporal_reconciliation"), "citations_required": True, "citations_planned": citation_ok, "stages": list(plan.stages)})
        except Exception as exc:
            failures += 1
            results.append({"id": row["id"], "category": row.get("category", ""), "passed": False, "error": type(exc).__name__})

    summary = {"schema": "chatbot-research-query-benchmark/v2", "queries": len(results), "passed": len(results) - failures, "failed": failures, "pass_rate": round((len(results) - failures) / len(results), 4) if results else 0.0, "results": results}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if allow_failures or failures == 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="benchmark/chatbot-query-corpus.json")
    parser.add_argument("--output", default=".runtime/chatbot-query-benchmark.json")
    parser.add_argument("--allow-failures", action="store_true", help="record research gaps without failing the acquisition runner")
    args = parser.parse_args()
    return run(Path(args.input), Path(args.output), args.allow_failures)


if __name__ == "__main__":
    raise SystemExit(main())