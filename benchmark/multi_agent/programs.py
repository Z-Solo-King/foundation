from __future__ import annotations

from .models import AgentSpec, ResearchProgram

ROLE_TEMPLATES = (
    ("research_lead", "decompose the question and identify the highest-value unknowns", 100),
    ("source_discovery", "discover independent source families and high-signal sources", 95),
    ("primary_evidence", "collect primary or first-party evidence for the central claim", 90),
    ("secondary_evidence", "collect independent secondary evidence and corroboration", 75),
    ("adversarial", "search for counterexamples, failure modes, copied claims, and misleading evidence", 90),
    ("temporal", "compare historical versus current evidence and detect stale information", 80),
    ("technical", "look for technical, implementation, teardown, protocol, or architecture evidence", 80),
    ("community", "search community, regional, multilingual, and hard-to-reach evidence", 70),
    ("reconciler", "reconcile contradictions, independence, identity, revisions, and confidence", 85),
    ("evaluator", "judge evidence quality, gaps, cost, latency, and the next best research action", 100),
)

PROGRAM_DEFS: tuple[tuple[int, int, str, str, str, tuple[str, ...]], ...] = (
    (0, 0, "acquisition", "HTML and structured extraction", "How can product research maximize useful HTML, JSON-LD, embedded-state, and structured-data extraction without unnecessary browser work?", ("retailers", "oem", "web_search")),
    (0, 1, "acquisition", "Public API and XHR discovery", "Which bounded techniques best discover public REST, GraphQL, Fetch, and XHR evidence while respecting source policy and rate limits?", ("retailers", "web_search", "api")),
    (0, 2, "acquisition", "Hydration and browser escalation", "When should the engine escalate from HTML to hydration-state parsing or browser execution, and what signals predict success?", ("retailers", "professional_reviews", "web_search")),
    (0, 3, "acquisition", "Pagination, variants, sitemap, feeds", "How can the engine discover deep pagination, variants, sitemaps, feeds, and hidden catalog entries efficiently?", ("retailers", "web_search")),
    (0, 4, "acquisition", "Image intelligence", "How can product images contribute identity, model, specification, revision, and visual evidence without hallucinating facts?", ("retailers", "oem", "professional_reviews")),
    (0, 5, "acquisition", "Robots, blocking, and resilience", "What patterns best distinguish allowed access, blocking, rate limiting, transient failure, and truthful fallback?", ("web_search", "retailers")),
    (0, 6, "acquisition", "Acquisition efficiency", "Which extraction strategy ordering, caching, deduplication, and bounded parallelism reduce requests and latency while preserving coverage?", ("retailers", "web_search")),
    (0, 7, "acquisition", "Cross-source acquisition benchmark", "Where does the current acquisition stack lose useful evidence compared with alternative open-source extraction approaches?", ("retailers", "oem", "professional_reviews", "web_search")),

    (1, 0, "mapper", "Product identity resolution", "How should the mapper resolve product identity, SKU, model, GTIN, variant, and bundle relationships across conflicting sources?", ("retailers", "amazon", "flipkart", "oem")),
    (1, 1, "mapper", "Specification normalization", "What compiler-like parsing and normalization techniques improve extraction of detailed hardware and product specifications?", ("retailers", "oem", "professional_reviews")),
    (1, 2, "mapper", "Price and stock intelligence", "How should current price, MRP, discount, availability, seller, and regional price evidence be reconciled over time?", ("retailers", "amazon", "flipkart", "price_stock")),
    (1, 3, "mapper", "Cross-source reconciliation", "How can the engine distinguish independent corroboration, republishing, revision differences, and genuine contradictions?", ("retailers", "oem", "professional_reviews", "reddit")),
    (1, 4, "chatbot", "Temporal review intelligence", "How can research compare launch reviews, older ownership reports, 2024-2026 evidence, and the latest 3-6 months without stale evidence dominating?", ("reddit", "amazon", "flipkart", "youtube", "professional_reviews")),
    (1, 5, "chatbot", "Adversarial review analysis", "How should the chatbot detect review spam, copied claims, seller-versus-product complaints, revision changes, and fake or weak evidence?", ("reddit", "amazon", "flipkart", "youtube", "social_communities")),
    (1, 6, "chatbot", "Unreachable evidence", "Which high-value evidence classes remain hard to retrieve, such as old pages, teardowns, PCB details, firmware issues, and regional reports?", ("reddit", "youtube", "teardown_evidence", "chinese_communities")),
    (1, 7, "chatbot", "Multilingual and regional research", "How should the chatbot broaden research across Hinglish, Chinese communities, PTT, Bilibili, Zhihu, Baidu Tieba, Douban, and regional terminology?", ("chinese_communities", "social_communities", "reddit")),

    (2, 0, "search", "Search-provider strategy", "Which query expansion, reranking, date filtering, source targeting, and multilingual search strategies produce more useful independent evidence?", ("web_search", "search_trends", "reddit", "chinese_communities")),
    (2, 1, "models", "Model routing and cost", "Which model-routing strategy assigns cheap models to simple tasks and stronger models to contradiction, multilingual, technical, and synthesis tasks?", ("web_search", "professional_reviews")),
    (2, 2, "agents", "Multi-agent architecture", "Which multi-agent decomposition patterns improve research quality without causing duplicated work, agent chatter, or runaway cost?", ("web_search", "professional_reviews")),
    (2, 3, "architecture", "Open-source architecture archaeology", "Which extractor, crawler, browser-agent, mapper, AI-gateway, and research-agent repositories contain reusable techniques worth benchmarking?", ("web_search", "oem")),
    (2, 4, "infrastructure", "GitHub Actions execution", "How should the nightly research system use GitHub Actions concurrency, scheduling, artifacts, caching, checkpoints, and runner limits efficiently?", ("web_search",)),
    (2, 5, "performance", "Latency and token efficiency", "How can the engine maximize useful evidence per token, per tool call, per request, and per unit time through caching and context reuse?", ("web_search", "professional_reviews")),
    (2, 6, "alternatives", "Alternative implementation methods", "Which alternative languages, runtimes, parsers, queues, model servers, browser agents, or retrieval stacks could outperform the current approach?", ("web_search", "oem")),
    (2, 7, "evaluation", "Benchmark evolution", "Which new regression tests and benchmark dimensions should be added when nightly research discovers new failures, sources, techniques, or platform behavior?", ("web_search", "professional_reviews")),
)


def _agents(program_id: str, title: str, source_families: tuple[str, ...]) -> tuple[AgentSpec, ...]:
    return tuple(
        AgentSpec(
            agent_id=f"{program_id}-{role}",
            role=role,
            objective=f"{objective}; focus on {title}",
            source_families=source_families,
            priority=priority,
        )
        for role, objective, priority in ROLE_TEMPLATES
    )


def _build(row: tuple[int, int, str, str, str, tuple[str, ...]]) -> ResearchProgram:
    lane, slot, category, title, question, source_families = row
    program_id = f"lane{lane}-slot{slot}"
    return ResearchProgram(
        program_id=program_id,
        lane=lane,
        slot=slot,
        category=category,
        title=title,
        question=question,
        agent_specs=_agents(program_id, title, source_families),
        max_active_agents=6,
    )


NIGHTLY_PROGRAMS: tuple[ResearchProgram, ...] = tuple(_build(row) for row in PROGRAM_DEFS)
PROGRAMS_BY_LANE: dict[int, tuple[ResearchProgram, ...]] = {
    lane: tuple(program for program in NIGHTLY_PROGRAMS if program.lane == lane)
    for lane in range(3)
}

if sum(len(rows) for rows in PROGRAMS_BY_LANE.values()) != 24:
    raise AssertionError("nightly program matrix must contain 24 research programs")
