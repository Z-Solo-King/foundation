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

SOURCE_FAMILY_ALIASES: dict[str, str] = {
    "bilibili": "chinese_communities",
    "zhihu": "chinese_communities",
    "baidu_tieba": "chinese_communities",
    "douban": "chinese_communities",
    "ptt": "chinese_communities",
    "regional_communities": "social_communities",
    "forums": "social_communities",
    "social": "social_communities",
    "social_media": "social_media",
    "x_twitter": "social_media",
    "twitter": "social_media",
    "instagram": "social_media",
    "facebook": "social_media",
    "tiktok": "social_media",
    "meta_ai": "social_media",
}

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


def _canonical_source_family(value: str) -> str:
    normalized = value.strip().casefold()
    return SOURCE_FAMILY_ALIASES.get(normalized, normalized)


def _source_families(question: str, category: str | None = None, explicit: tuple[str, ...] = ()) -> tuple[str, ...]:
    text = question.casefold()
    families: set[str] = {"web_search", "retailers", "oem"}
    families.update(_canonical_source_family(item) for item in CATEGORY_REQUIRED_SOURCE_FAMILIES.get(category or "", ()))
    families.update(_canonical_source_family(item) for item in explicit if item.strip())

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
            families.add(_canonical_source_family(family))

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
    }

    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata=metadata,
    )
