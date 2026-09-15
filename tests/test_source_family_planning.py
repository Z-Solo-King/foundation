from __future__ import annotations

import json
from pathlib import Path

from benchmark.chatbot_query_benchmark import SOURCE_ALIASES, load_queries
from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


CORPUS = Path("benchmark/chatbot-query-corpus.json")


def test_all_corpus_queries_plan_required_source_families() -> None:
    failures: list[str] = []
    for row in load_queries(CORPUS):
        expected = {SOURCE_ALIASES.get(str(value), str(value)) for value in row.get("required_sources", [])}
        plan = create_plan(
            ResearchContract(
                question=str(row["query"]),
                depth="deep",
                require_citations=True,
                max_sources=40,
                max_evidence_items=200,
                query_category=str(row.get("category", "")) or None,
                required_source_families=tuple(sorted(expected)),
            )
        )
        planned = {value for value in plan.metadata["required_source_families"].split(",") if value}
        missing = expected - planned
        if missing:
            failures.append(f"{row['id']}: {sorted(missing)}")
        if row.get("temporal") == "old_vs_new" and plan.metadata.get("temporal_reconciliation") != "true":
            failures.append(f"{row['id']}: temporal reconciliation not planned")
    assert not failures, "\n".join(failures)


def test_source_family_contract_rejects_duplicate_requirements() -> None:
    with_json = json.dumps({"required": ["amazon", "amazon"]})
    assert "amazon" in with_json
    try:
        ResearchContract(question="test", required_source_families=("amazon", "amazon")).validate()
    except ValueError as exc:
        assert "duplicates" in str(exc)
    else:
        raise AssertionError("duplicate source families must be rejected")
