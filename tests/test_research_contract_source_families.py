from __future__ import annotations

import pytest

from backend.intelligence.contracts import ResearchContract
from backend.intelligence.planning import create_plan


def test_research_contract_accepts_category_and_explicit_families() -> None:
    contract = ResearchContract(
        question="best laptop under 100000",
        depth="deep",
        query_category="best_product",
        required_source_families=("reddit", "  flipkart  "),
    )
    contract.validate()
    plan = create_plan(contract)
    families = set(plan.metadata["required_source_families"].split(","))
    assert {"amazon", "flipkart", "reddit", "retailers", "professional_reviews"} <= families
    assert plan.metadata["required_source_families_origin"] == "explicit+category+question"
    assert plan.metadata["query_category"] == "best_product"


def test_research_contract_rejects_blank_source_family() -> None:
    contract = ResearchContract(question="test", required_source_families=("",))
    with pytest.raises(ValueError, match="non-empty names"):
        contract.validate()


def test_research_contract_rejects_duplicate_source_families() -> None:
    contract = ResearchContract(question="test", required_source_families=("reddit", "reddit"))
    with pytest.raises(ValueError, match="duplicates"):
        contract.validate()


def test_planner_handles_missing_category_and_normalizes_explicit_entries() -> None:
    contract = ResearchContract(
        question="basic product research",
        required_source_families=("  reddit  ", "youtube"),
    )
    plan = create_plan(contract)
    families = set(plan.metadata["required_source_families"].split(","))
    assert "reddit" in families
    assert "youtube" in families
    assert "  reddit  " not in families
    assert plan.metadata["query_category"] == ""


def test_planner_category_and_temporal_metadata_are_independent() -> None:
    category_plan = create_plan(
        ResearchContract(question="buying guide", query_category="buying_guide")
    )
    temporal_plan = create_plan(
        ResearchContract(question="latest revision versus 2024", query_category=None)
    )
    assert "amazon" in category_plan.metadata["required_source_families"]
    assert category_plan.metadata["temporal_reconciliation"] == "false"
    assert temporal_plan.metadata["temporal_reconciliation"] == "true"


def test_planner_quick_contract_keeps_bounded_stage_set() -> None:
    plan = create_plan(ResearchContract(question="quick lookup", depth="quick"))
    assert plan.stages == (
        "define_question",
        "discover_sources",
        "collect_observations",
        "verify_evidence",
        "synthesize_answer",
    )
