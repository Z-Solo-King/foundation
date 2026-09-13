"""Pure planner algorithms: classification, query generation, scoring and recovery.

No network, provider secrets or protected-policy decisions live here.
"""
from __future__ import annotations

import re
from dataclasses import replace
from typing import Iterable, Mapping, Sequence

from .planner_models import (
    Action,
    ClaimRequirement,
    Coverage,
    CoverageState,
    FactType,
    FailureClass,
    MethodCandidate,
    QueryCandidate,
    ResourceEnvelope,
    SourcePlan,
    SourceProfileHint,
    StopReason,
    TaskMode,
    TaskPlan,
)


def classify_task(question: str, output_type: str = "") -> TaskMode:
    text = f"{question} {output_type}".lower()
    signals = {
        TaskMode.RECOMMENDATION: ("recommend", "best", "which should", "buy"),
        TaskMode.COMPARISON: ("compare", "versus", "vs", "difference"),
        TaskMode.TEMPORAL: ("history", "historical", "changed", "when", "latest"),
        TaskMode.CONTRADICTION: ("contradict", "disagree", "is it true", "conflict"),
        TaskMode.PRICE_AVAILABILITY: ("price", "cost", "stock", "available"),
        TaskMode.SPECIFICATION: ("spec", "specification", "dimensions", "ports", "hz", "ram", "cpu"),
        TaskMode.DIAGNOSIS: ("why", "problem", "error", "broken", "debug"),
        TaskMode.COMMUNITY: ("reddit", "forum", "community", "user experience", "sentiment"),
        TaskMode.PRIMARY_SOURCE: ("official", "manufacturer", "source of record", "primary source"),
        TaskMode.ENTITY_RESOLUTION: ("same product", "same model", "match", "identify entity"),
        TaskMode.CODE: ("code", "repository", "python", "javascript", "bug", "pull request"),
        TaskMode.DATA: ("dataset", "csv", "spreadsheet", "columns", "dataframe"),
        TaskMode.DOCUMENT: ("document", "pdf", "report", "contract"),
        TaskMode.MEDIA: ("image", "video", "audio", "transcript", "frame"),
    }
    matches = [mode for mode, words in signals.items() if any(w in text for w in words)]
    if len(matches) > 1:
        return TaskMode.MIXED
    return matches[0] if matches else TaskMode.FACT


def infer_fact_type(text: str) -> FactType:
    value = text.lower()
    if any(x in value for x in ("price", "cost", "discount", "currency")):
        return FactType.COMMERCIAL
    if any(x in value for x in ("stock", "availability", "available")):
        return FactType.AVAILABILITY
    if any(x in value for x in ("release", "launched", "updated", "current", "historical")):
        return FactType.TEMPORAL
    if any(x in value for x in ("compatible", "works with", "depends on")):
        return FactType.RELATIONAL
    if any(x in value for x in ("review", "experience", "feel", "quality")):
        return FactType.QUALITATIVE
    if any(x in value for x in ("policy", "terms", "rule", "regulation")):
        return FactType.NORMATIVE
    if any(x in value for x in ("model", "sku", "mpn", "gtin", "version", "name")):
        return FactType.IDENTITY
    return FactType.SPECIFICATION if any(x in value for x in ("spec", "size", "port", "hz", "memory", "weight")) else FactType.IDENTITY


def decompose_claims(question: str, required: Sequence[str] | None = None) -> tuple[ClaimRequirement, ...]:
    items = [x.strip() for x in (required or ()) if x and x.strip()]
    if not items:
        pieces = re.split(r"\s*(?:,|;|\band\b|\bplus\b)\s*", question, flags=re.I)
        items = [p.strip() for p in pieces if len(p.strip()) >= 8]
    if not items:
        items = [question.strip()]
    return tuple(
        ClaimRequirement(
            claim_id=f"claim-{i+1}",
            text=text,
            fact_type=infer_fact_type(text),
        )
        for i, text in enumerate(items)
    )


def generate_query_portfolio(
    question: str,
    claims: Sequence[ClaimRequirement],
    languages: Sequence[str] = (),
    source_families: Sequence[str] = (),
    max_queries: int = 12,
) -> tuple[QueryCandidate, ...]:
    base = question.strip()
    candidates: list[QueryCandidate] = []
    seen: set[str] = set()

    def add(query: str, purpose: str, gain: float, family: str | None = None, claim_ids: tuple[str, ...] = ()) -> None:
        normalized = " ".join(query.split()).lower()
        if not normalized or normalized in seen or len(candidates) >= max_queries:
            return
        seen.add(normalized)
        candidates.append(QueryCandidate(query=query, purpose=purpose, expected_information_gain=gain,
                                         estimated_cost=1.0, target_source_family=family,
                                         target_claim_ids=claim_ids))

    claim_ids = tuple(c.claim_id for c in claims)
    add(base, "exact", 0.90, claim_ids=claim_ids)
    for claim in claims[:3]:
        add(f"\"{claim.text}\"", "identifier/exact-claim", 0.85, claim_ids=(claim.claim_id,))
    add(f"{base} official", "primary-source", 0.88, "official", claim_ids)
    add(f"{base} specifications", "specification", 0.75, "manufacturer", claim_ids)
    add(f"{base} counterclaim", "counterclaim", 0.70, claim_ids=claim_ids)
    add(f"{base} recent", "freshness", 0.72, claim_ids=claim_ids)
    for family in source_families:
        add(f"site:{family} {base}", "site-restricted", 0.65, family, claim_ids)
    for language in languages:
        if language.lower() not in {"en", "english"}:
            add(f"{base} {language}", "multilingual", 0.62, claim_ids=claim_ids)
    add(f"{base} review experience", "community", 0.55, "community", claim_ids)
    return tuple(candidates)


def method_utility(method: MethodCandidate) -> float:
    positive = (
        method.evidence_directness * 0.22
        + method.authority * 0.18
        + method.expected_success * 0.18
        + method.expected_completeness * 0.16
        + method.freshness * 0.08
        + method.independence * 0.08
        + method.information_gain * 0.10
    )
    cost = 0.06 * method.latency_cost + 0.08 * method.resource_cost + 0.10 * method.risk_penalty
    return positive - cost


def rank_methods(methods: Iterable[MethodCandidate]) -> tuple[MethodCandidate, ...]:
    return tuple(sorted(methods, key=lambda m: (-method_utility(m), m.method_id)))


def apply_source_profiles(methods: Sequence[MethodCandidate], profiles: Mapping[str, SourceProfileHint]) -> tuple[MethodCandidate, ...]:
    updated: list[MethodCandidate] = []
    for method in methods:
        profile = profiles.get(method.source_id)
        if profile is None:
            updated.append(method)
            continue
        if profile.supported_representations and method.representation not in profile.supported_representations:
            continue
        risk = method.risk_penalty + max(0.0, 0.5 - profile.health)
        expected_success = min(0.99, max(0.01, (method.expected_success + profile.health) / 2))
        if profile.sample_size < 5:
            expected_success = (expected_success + 0.5) / 2
        updated.append(replace(method, expected_success=expected_success, risk_penalty=risk))
    return rank_methods(updated)


def coverage_map(claims: Sequence[ClaimRequirement], evidence: Mapping[str, Coverage]) -> tuple[Coverage, ...]:
    return tuple(evidence.get(c.claim_id, Coverage(c.claim_id, CoverageState.UNSUPPORTED)) for c in claims)


def recovery_actions(coverage: Sequence[Coverage]) -> tuple[Action, ...]:
    actions: list[Action] = []
    for item in coverage:
        if item.state in (CoverageState.CONTRADICTED, CoverageState.AMBIGUOUS):
            actions.append(Action(f"recover-{item.claim_id}-independent", "search", "independent/counterclaim verification", (item.claim_id,)))
        elif item.state in (CoverageState.PARTIAL, CoverageState.UNSUPPORTED):
            actions.append(Action(f"recover-{item.claim_id}-primary", "search", "primary/gap retrieval", (item.claim_id,)))
        elif item.state == CoverageState.STALE:
            actions.append(Action(f"recover-{item.claim_id}-fresh", "search", "freshness refresh", (item.claim_id,)))
        elif item.state in (CoverageState.BLOCKED, CoverageState.INACCESSIBLE):
            actions.append(Action(f"recover-{item.claim_id}-alternate", "search", "permitted alternate source", (item.claim_id,)))
    return tuple(actions)


def choose_stop_reason(coverage: Sequence[Coverage], budget_remaining: float, min_gain: float = 0.05) -> StopReason | None:
    hard = {CoverageState.UNSUPPORTED, CoverageState.PARTIAL, CoverageState.CONTRADICTED, CoverageState.STALE,
            CoverageState.BLOCKED, CoverageState.INACCESSIBLE, CoverageState.AMBIGUOUS}
    if coverage and all(c.state not in hard for c in coverage):
        return StopReason.QUALITY_FLOOR
    if budget_remaining <= 0:
        return StopReason.BUDGET_EXHAUSTED
    if budget_remaining < min_gain:
        return StopReason.LOW_INFORMATION_GAIN
    return None


def build_task_plan(
    question: str,
    output_type: str = "",
    claims: Sequence[str] | None = None,
    languages: Sequence[str] = (),
    source_families: Sequence[str] = (),
    methods: Sequence[MethodCandidate] = (),
    envelope: ResourceEnvelope | None = None,
    max_queries: int = 12,
) -> TaskPlan:
    mode = classify_task(question, output_type)
    claim_reqs = decompose_claims(question, claims)
    queries = generate_query_portfolio(question, claim_reqs, languages, source_families, max_queries=max_queries)
    ranked = apply_source_profiles(methods, {})
    source_plans = tuple(SourcePlan(family, required=(family in ("official", "primary"))) for family in source_families)
    actions = tuple(Action(f"query-{i+1}", "search", q.purpose, q.target_claim_ids, estimated_cost=q.estimated_cost)
                    for i, q in enumerate(queries))
    env = envelope or ResourceEnvelope(search_units=max(1, len(queries)))
    env.validate()
    return TaskPlan(mode, tuple(claim_reqs), source_plans, queries, ranked, actions, env,
                    metadata={"output_type": output_type, "planner": "deterministic-v1"})


def create_task_plan(contract: object) -> TaskPlan:
    """Build the canonical immutable task plan from a validated research contract."""
    contract.validate()
    return build_task_plan(
        question=contract.question,
        output_type=contract.output_type,
        claims=contract.claims_required,
        languages=contract.languages,
        source_families=contract.source_families_required,
        envelope=contract.resource_envelope,
        max_queries=contract.max_search_actions,
    )


__all__ = [
    "classify_task",
    "infer_fact_type",
    "decompose_claims",
    "generate_query_portfolio",
    "method_utility",
    "rank_methods",
    "apply_source_profiles",
    "coverage_map",
    "recovery_actions",
    "choose_stop_reason",
    "build_task_plan",
    "create_task_plan",
]
