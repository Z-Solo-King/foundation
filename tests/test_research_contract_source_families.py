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


def test_research_contract_fingerprints_canonicalize_semantically_identical_inputs():
    first = ResearchContract(
        question="  latest   product  ",
        required_source_families=("reddit", "amazon"),
        subquestions=(" Price? ", "Availability?"),
        required_output_scope=("answer", "citations"),
        optional_output_scope=("notes",),
        freshness_requirement="  recent  ",
        evidence_requirement=" verified ",
        allowed_tool_classes=("research", "web"),
        deadline_ms=1000,
        execution_budget_units=50,
        privacy_policy="public_safe",
        publication_policy="public_safe",
        expected_result_states=("PARTIAL", "COMPLETED"),
        contract_revision="v1",
        policy_version="p1",
    )
    second = ResearchContract(
        question="latest product",
        required_source_families=("amazon", "reddit"),
        subquestions=("Availability?", "Price?"),
        required_output_scope=("citations", "answer"),
        optional_output_scope=("notes",),
        freshness_requirement="recent",
        evidence_requirement="verified",
        allowed_tool_classes=("web", "research"),
        deadline_ms=1000,
        execution_budget_units=50,
        privacy_policy="public_safe",
        publication_policy="public_safe",
        expected_result_states=("COMPLETED", "PARTIAL"),
        contract_revision="v1",
        policy_version="p1",
    )
    assert first.contract_fingerprint == second.contract_fingerprint
    assert len(first.contract_fingerprint) == 64


def test_research_contract_validation_rejects_new_contract_gates():
    cases = [
        dict(subquestions=("",)),
        dict(subquestions=("a", "A")),
        dict(required_output_scope=("",)),
        dict(optional_output_scope=("",)),
        dict(required_output_scope=("answer",), optional_output_scope=("ANSWER",)),
        dict(freshness_requirement=" "),
        dict(evidence_requirement=" "),
        dict(allowed_tool_classes=("",)),
        dict(allowed_tool_classes=("web", "WEB")),
        dict(deadline_ms=0),
        dict(execution_budget_units=0),
        dict(privacy_policy=" "),
        dict(publication_policy=" "),
        dict(expected_result_states=()),
        dict(expected_result_states=("NOT_A_STATE",)),
        dict(contract_revision=" "),
        dict(policy_version=" "),
    ]
    for changes in cases:
        with pytest.raises(ValueError):
            ResearchContract(question="test", **changes).validate()


def test_research_contract_derive_child_never_expands_parent_budgets():
    parent = ResearchContract(
        question="test",
        max_sources=20,
        max_evidence_items=100,
        deadline_ms=10_000,
        execution_budget_units=100,
    )
    child = parent.derive_child(
        max_sources=10,
        max_evidence_items=50,
        deadline_ms=5_000,
        execution_budget_units=50,
    )
    assert child.max_sources == 10
    assert child.max_evidence_items == 50
    assert child.deadline_ms == 5_000
    assert child.execution_budget_units == 50

    for changes in (
        {"max_sources": 21},
        {"max_evidence_items": 101},
        {"deadline_ms": 20_000},
        {"execution_budget_units": 101},
    ):
        with pytest.raises(ValueError):
            parent.derive_child(**changes)


def test_research_contract_derive_child_inherits_unspecified_limits():
    parent = ResearchContract(question="test")
    child = parent.derive_child()
    assert child.max_sources == parent.max_sources
    assert child.max_evidence_items == parent.max_evidence_items
    assert child.deadline_ms is None
    assert child.execution_budget_units is None


def test_research_contract_versions_must_match_for_compatibility():
    base = ResearchContract(question="test", contract_revision="v1", policy_version="p1")
    same = ResearchContract(question="test", contract_revision="v1", policy_version="p1")
    base.ensure_compatible(same)

    with pytest.raises(ValueError, match="incompatible"):
        base.ensure_compatible(ResearchContract(question="test", contract_revision="v2", policy_version="p1"))
    with pytest.raises(ValueError, match="incompatible"):
        base.ensure_compatible(ResearchContract(question="test", contract_revision="v1", policy_version="p2"))


def test_research_plan_preserves_contract_identity_and_scope_metadata():
    contract = ResearchContract(
        question="latest product",
        required_output_scope=("answer", "citations"),
        optional_output_scope=("notes",),
        freshness_requirement="recent",
        evidence_requirement="verified",
        allowed_tool_classes=("web", "research"),
        deadline_ms=2000,
        execution_budget_units=80,
    )
    plan = create_plan(contract)
    assert plan.metadata["contract_fingerprint"] == contract.contract_fingerprint
    assert plan.metadata["required_output_scope"] == "answer,citations"
    assert plan.metadata["optional_output_scope"] == "notes"
    assert plan.metadata["freshness_requirement"] == "recent"
    assert plan.metadata["allowed_tool_classes"] == "web,research"
    assert plan.metadata["deadline_ms"] == "2000"
    assert plan.metadata["execution_budget_units"] == "80"
