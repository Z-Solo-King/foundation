from __future__ import annotations

from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


REQUIRED_FAMILIES_BY_ALIAS = {
    "bilibili": "chinese_communities",
    "zhihu": "chinese_communities",
    "baidu_tieba": "chinese_communities",
    "douban": "chinese_communities",
    "ptt": "chinese_communities",
    "regional_communities": "social_communities",
    "forums": "social_communities",
    "twitter": "social_media",
    "instagram": "social_media",
}


def test_aliases_canonicalize_before_source_family_gate():
    contract = ResearchContract(
        question="Investigate Chinese and regional community feedback.",
        depth="deep",
        require_citations=True,
        required_source_families=tuple(REQUIRED_FAMILIES_BY_ALIAS),
        max_sources=40,
        max_evidence_items=200,
    )
    plan = create_plan(contract)
    families = set(plan.metadata["required_source_families"].split(","))
    assert "chinese_communities" in families
    assert "social_communities" in families
    assert "bilibili" not in families
    assert "regional_communities" not in families


def test_current_chatbot_query_corpus_categories_are_source_complete():
    from benchmark.chatbot_query_benchmark import load_queries, SOURCE_ALIASES
    from pathlib import Path

    rows = load_queries(Path("benchmark/chatbot-query-corpus.json"))
    assert len(rows) == 17
    for row in rows:
        expected = {
            SOURCE_ALIASES.get(str(source), str(source))
            for source in row.get("required_sources", [])
        }
        contract = ResearchContract(
            question=str(row["query"]),
            depth="deep",
            require_citations=True,
            max_sources=40,
            max_evidence_items=200,
            query_category=str(row.get("category") or "") or None,
            required_source_families=tuple(sorted(expected)),
        )
        plan = create_plan(contract)
        actual = set(plan.metadata["required_source_families"].split(","))
        assert expected <= actual, f"{row['id']} missing source families: {sorted(expected - actual)}"
