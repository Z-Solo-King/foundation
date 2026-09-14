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


def _source_families(question: str) -> tuple[str, ...]:
    text = question.casefold()
    families: set[str] = {"web_search", "retailers", "oem"}

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

    metadata = {
        "depth": contract.depth,
        "require_citations": str(contract.require_citations).lower(),
        "required_source_families": ",".join(_source_families(contract.question)),
        "temporal_reconciliation": str(
            any(term in contract.question.casefold() for term in (
                "old vs new", "older reviews", "latest", "recent", "2024", "2025", "2026", "revision",
            ))
        ).lower(),
    }

    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata=metadata,
    )
