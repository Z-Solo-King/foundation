from .contracts import ResearchContract, ResearchPlan


DEFAULT_STAGES = (
    "define_question",
    "assess_constraints",
    "discover_sources",
    "collect_observations",
    "map_evidence",
    "verify_evidence",
    "check_independence",
    "synthesize_answer",
)

CATEGORY_REQUIRED_SOURCE_FAMILIES: dict[str, tuple[str, ...]] = {
    "buying_guide": ("amazon", "flipkart", "reddit", "retailers", "oem"),
    "best_product": ("amazon", "flipkart", "reddit", "retailers", "professional_reviews"),
    "deep_hardware": ("reddit", "amazon", "flipkart", "chinese_communities"),
    "temporal_reconciliation": ("amazon", "flipkart", "reddit", "youtube", "oem", "social_communities"),
    "review_forensics": ("amazon", "flipkart", "reddit"),
    "cross_source": ("amazon", "flipkart", "reddit", "youtube", "social_communities"),
    "social_media": ("reddit", "social_media", "youtube", "amazon", "flipkart"),
    "restricted_evidence": ("reddit", "chinese_communities", "social_communities", "social_media"),
    "build": ("retailers", "amazon", "flipkart", "reddit", "oem"),
    "hinglish": ("amazon", "flipkart", "reddit", "retailers"),
    "follow_up": ("reddit", "amazon", "flipkart", "youtube"),
    "hardware_revision": ("oem", "reddit", "chinese_communities", "youtube", "retailers"),
    "service": ("oem", "amazon", "flipkart", "reddit", "retailers"),
    "trending": ("search_trends", "amazon", "flipkart", "reddit", "retailers"),
}


def _source_families(question: str, category: str | None = None, explicit: tuple[str, ...] = ()) -> tuple[str, ...]:
    text = question.casefold()
    families: set[str] = {"web_search", "retailers", "oem"}
    families.update(CATEGORY_REQUIRED_SOURCE_FAMILIES.get(category or "", ()))
    families.update(item.strip() for item in explicit if item.strip())

    keyword_groups = {
        "reddit": ("reddit", "subreddit", "owner reports", "ownership"),
        "amazon": ("amazon", "buyer reviews", "verified buyer"),
        "flipkart": ("flipkart",),
        "youtube": ("youtube", "video review", "long-term review"),
        "social_media": (
            "social media", "twitter", "x.com", "instagram", "facebook", "tiktok", "meta ai", "threads",
        ),
        "social_communities": ("social", "community", "forum"),
        "chinese_communities": (
            "chinese", "china", "bilibili", "zhihu", "baidu tieba", "tieba", "douban", "ptt",
        ),
        "teardown_evidence": (
            "teardown", "internal", "pcb", "mcu", "controller", "soldering", "component", "revision",
        ),
        "professional_reviews": ("professional review", "reviewers", "expert review"),
        "search_trends": ("trending", "trend", "search popularity"),
        "price_stock": ("price", "stock", "availability", "current"),
    }
    for family, terms in keyword_groups.items():
        if any(term in text for term in terms):
            families.add(family)

    return tuple(sorted(families))


def create_plan(contract: ResearchContract) -> ResearchPlan:
    contract.validate()
    stages = DEFAULT_STAGES

    if contract.depth == "quick":
        stages = (
            "define_question",
            "discover_sources",
            "collect_observations",
            "verify_evidence",
            "synthesize_answer",
        )

    source_families = _source_families(
        contract.question,
        category=contract.query_category,
        explicit=contract.required_source_families,
    )
    metadata = {
        "depth": contract.depth,
        "require_citations": str(contract.require_citations).lower(),
        "required_source_families": ",".join(source_families),
        "required_source_families_origin": "explicit+category+question",
        "query_category": contract.query_category or "",
        "temporal_reconciliation": str(
            any(term in contract.question.casefold() for term in (
                "old vs new", "older reviews", "latest", "recent", "2024", "2025", "2026", "revision",
            ))
        ).lower(),
        "contract_revision": contract.contract_revision,
        "policy_version": contract.policy_version,
        "contract_fingerprint": contract.contract_fingerprint,
        "required_output_scope": ",".join(contract.required_output_scope),
        "optional_output_scope": ",".join(contract.optional_output_scope),
        "freshness_requirement": contract.freshness_requirement or "",
        "evidence_requirement": contract.evidence_requirement,
        "allowed_tool_classes": ",".join(contract.allowed_tool_classes),
        "deadline_ms": "" if contract.deadline_ms is None else str(contract.deadline_ms),
        "execution_budget_units": "" if contract.execution_budget_units is None else str(contract.execution_budget_units),
        "privacy_policy": contract.privacy_policy,
        "publication_policy": contract.publication_policy,
        "expected_result_states": ",".join(contract.expected_result_states),
    }

    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata=metadata,
    )
