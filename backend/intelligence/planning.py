from __future__ import annotations
from typing import Mapping, Sequence
from .contracts import ResearchContract, ResearchPlan

DEFAULT_STAGES = (
    "define_question","assess_constraints","discover_sources","collect_observations",
    "map_evidence","verify_evidence","check_independence","synthesize_answer",
)

def _source_families(
    question: str,
    *,
    category: str | None = None,
    explicit: tuple[str, ...] = (),
    planning_policy: Mapping[str, object] | None = None,
) -> tuple[str, ...]:
    text=question.casefold()
    policy=planning_policy or {}
    families=set(str(x).strip() for x in policy.get("base_source_families", ()) if str(x).strip())
    category_rules=policy.get("category_required_source_families", {})
    if isinstance(category_rules, Mapping):
        values=category_rules.get(category or "", ())
        if isinstance(values, Sequence) and not isinstance(values,(str,bytes)):
            families.update(str(x).strip() for x in values if str(x).strip())
    families.update(item.strip() for item in explicit if item.strip())
    keyword_groups=policy.get("keyword_groups", {})
    if isinstance(keyword_groups, Mapping):
        for family,terms in keyword_groups.items():
            if isinstance(terms,Sequence) and not isinstance(terms,(str,bytes)) and any(str(term).casefold() in text for term in terms if str(term).strip()):
                families.add(str(family).strip())
    return tuple(sorted(families))

def create_plan(contract: ResearchContract, *, planning_policy: Mapping[str, object] | None = None) -> ResearchPlan:
    contract.validate()
    policy=planning_policy or {}
    stages=tuple(str(x) for x in policy.get("standard_stages", DEFAULT_STAGES))
    if contract.depth=="quick":
        stages=tuple(str(x) for x in policy.get("quick_stages", (
            "define_question","discover_sources","collect_observations","verify_evidence","synthesize_answer"
        )))
    source_families=_source_families(
        contract.question,
        category=contract.query_category,
        explicit=contract.required_source_families,
        planning_policy=policy,
    )
    temporal_terms=policy.get("temporal_terms", ())
    q=contract.question.casefold()
    temporal=isinstance(temporal_terms,Sequence) and not isinstance(temporal_terms,(str,bytes)) and any(str(term).casefold() in q for term in temporal_terms if str(term).strip())
    metadata={
        "depth":contract.depth,
        "require_citations":str(contract.require_citations).lower(),
        "required_source_families":",".join(source_families),
        "required_source_families_origin":"explicit+private_policy" if planning_policy else "explicit_only",
        "query_category":contract.query_category or "",
        "temporal_reconciliation":str(temporal).lower(),
        "contract_revision":contract.contract_revision,
        "policy_version":contract.policy_version,
        "contract_fingerprint":contract.contract_fingerprint,
        "required_output_scope":",".join(contract.required_output_scope),
        "optional_output_scope":",".join(contract.optional_output_scope),
        "freshness_requirement":contract.freshness_requirement or "",
        "evidence_requirement":contract.evidence_requirement,
        "allowed_tool_classes":",".join(contract.allowed_tool_classes),
        "deadline_ms":"" if contract.deadline_ms is None else str(contract.deadline_ms),
        "execution_budget_units":"" if contract.execution_budget_units is None else str(contract.execution_budget_units),
        "privacy_policy":contract.privacy_policy,
        "publication_policy":contract.publication_policy,
        "expected_result_states":",".join(contract.expected_result_states),
    }
    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata=metadata,
    )
