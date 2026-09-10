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
    return ResearchPlan(
        question=contract.question,
        stages=stages,
        source_budget=contract.max_sources,
        evidence_budget=contract.max_evidence_items,
        metadata={"depth": contract.depth},
    )
