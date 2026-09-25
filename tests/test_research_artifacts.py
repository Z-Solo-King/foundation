from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_research_artifact_catalog_is_structured_and_truthful() -> None:
    catalog = _load("benchmark/research_artifact_catalog.json")
    assert catalog["schema"] == "research-artifact-catalog/v1"
    artifacts = {row["path"]: row for row in catalog["artifacts"]}
    required = {
        "benchmark/chatbot-query-corpus.json",
        "benchmark/chatbot_query_benchmark.py",
        "benchmark/public_chatbot_runner.py",
        "benchmark/research_artifact_validator.py",
        "benchmark/multi_agent/baseline.py",
        "benchmark/nightly/NIGHTLY_RESEARCH_PLAN.json",
        "benchmark/nightly/research-ledger.schema.json",
        "benchmark/nightly/research_ledger.py",
        "benchmark/autonomous_scorecard.py",
    }
    assert required <= artifacts.keys()
    for path, row in artifacts.items():
        assert (ROOT / path).exists(), path
        assert isinstance(row["reusable_evidence"], bool)
        assert row["research_value"] in {"High", "Medium", "Low"}
    assert len(catalog["reusable_evidence_rules"]) >= 6


def test_project_research_corpus_has_broad_project_coverage() -> None:
    corpus = _load("benchmark/chatbot-query-corpus.json")
    assert corpus["schema"] == "chatbot-research-query-corpus/v3"
    queries = corpus["queries"]
    assert len(queries) >= 25
    categories = {row["category"] for row in queries}
    project_categories = {
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
        "nightly_artifact_integrity",
    }
    assert project_categories <= categories
    project_rows = [row for row in queries if row["category"] in project_categories]
    project_category_counts = {category: sum(1 for row in project_rows if row["category"] == category) for category in project_categories}
    assert all(count >= 1 for count in project_category_counts.values())
    assert len(project_rows) >= len(project_categories)
    assert all("github" in row["required_sources"] for row in project_rows)
    assert any(row["temporal"] == "old_vs_new" for row in project_rows)


def test_project_queries_cover_the_research_artifacts_themselves() -> None:
    corpus = _load("benchmark/chatbot-query-corpus.json")
    queries = {row["id"]: row["query"].lower() for row in corpus["queries"]}
    assert "project-research-artifacts" in queries
    assert "query corpora" in queries["project-research-artifacts"]
    assert "nightly research plans" in queries["project-research-artifacts"]
    assert "scorecards" in queries["project-research-artifacts"]
