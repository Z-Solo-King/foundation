from dataclasses import dataclass

from backend.research import ResearchContract


@dataclass(frozen=True)
class ResearchPlan:
    question: str
    depth: str
    require_citations: bool
    stages: tuple[str, ...]


def create_plan(contract: ResearchContract) -> ResearchPlan:
    stages = (
        "define_question",
        "discover_sources",
        "collect_evidence",
        "verify_evidence",
        "synthesize_answer",
    )

    if contract.depth == "quick":
        stages = stages[:4]

    return ResearchPlan(
        question=contract.question,
        depth=contract.depth,
        require_citations=contract.require_citations,
        stages=stages,
    )
